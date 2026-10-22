"""Synthetic source-package checks; these do not certify the missing real archive."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('historical_package',
    ROOT / 'IRGS_Catalog/historical_details_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def make_archive(path, *, change=None):
    payloads = {}
    for collection, member in package.COLLECTIONS.items():
        records = [{'id': collection + '-1', 'source_ids': ['source-1'],
                    'certainty': 'disputed', 'rights_status': 'source-specific'},
                   {'id': collection + '-1', 'source_ids': ['unresolved-reference'],
                    'date_text': 'undated', 'units': None}]
        if member.endswith('.gz'):
            payloads[member] = gzip.compress(
                b''.join(json.dumps(row).encode() + b'\n' for row in records), mtime=0)
        else:
            payloads[member] = json.dumps(records).encode()
    # Enough opaque central database bytes for three actual 16 MiB parts.
    # Non-reader content must survive the same round trip as the ten collections.
    payloads['01_Database/central.sqlite'] = b'opaque fixture\x00\xff' * (2 * package.PART_SIZE // 16 + 1)
    payloads['05_Books/book.txt'] = b'Original book fixture; no new license granted.\n'
    payloads['09_Ancillary/unindexed.bin'] = b'preserve every ancillary byte\x00\xff'
    delivery = {'edition': 'Grand 1.1', 'files': [
        {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        for name, data in payloads.items() if name != '09_Ancillary/unindexed.bin']}
    if change:
        change(delivery, payloads)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name, data in payloads.items():
                archive.writestr('Fixture/' + name, data)
            archive.writestr('Fixture/07_Verification/delivery_manifest.json', json.dumps(delivery))


class HistoricalDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='irgs-package-tests-')
        cls.base = Path(cls.shared.name)
        cls.source = cls.base / 'source.zip'
        make_archive(cls.source)
        cls.identity = {'name': package.EXPECTED_ARCHIVE['name'],
                        'bytes': cls.source.stat().st_size,
                        'sha256': hashlib.sha256(cls.source.read_bytes()).hexdigest()}
        cls.original = cls.base / 'original'
        package.build_package(cls.source, cls.original, expected_archive=cls.identity)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-package-case-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.copy = self.root / 'package'
        shutil.copytree(self.original, self.copy)
        self.manifest = self.copy / 'manifest.json'
        self.document = json.loads(self.manifest.read_text())

    def save(self):
        self.manifest.write_text(json.dumps(self.document))

    def verify(self, **kwargs):
        return package.verify_package(self.manifest, expected_archive=self.identity, **kwargs)

    def part(self, index=0):
        return self.copy / self.document['parts'][index]['path']

    def test_deterministic_split_and_exact_full_archive_round_trip(self):
        second = self.root / 'second'
        package.build_package(self.source, second, expected_archive=self.identity)
        self.assertEqual(self.manifest.read_bytes(), (second / 'manifest.json').read_bytes())
        self.assertEqual(len(self.document['parts']), 3)
        self.assertEqual([p['bytes'] for p in self.document['parts'][:-1]],
                         [package.PART_SIZE, package.PART_SIZE])
        output = self.root / 'reassembled.zip'
        result = self.verify(output=output)
        self.assertEqual(output.read_bytes(), self.source.read_bytes())
        self.assertEqual(result['collection_bindings_verified'], 10)
        self.assertEqual(result['members_verified'], 14)
        self.assertFalse(result['historical_truth_verified'])
        self.assertIn('Fixture/09_Ancillary/unindexed.bin', result['unbound_members'])
        self.assertEqual([c['record_count'] for c in self.document['coverage']['collections']], [2] * 10)
        with zipfile.ZipFile(output) as archive:
            records = json.loads(archive.read('Fixture/' + package.COLLECTIONS['chronology']))
            self.assertEqual(records[0]['certainty'], 'disputed')
            self.assertEqual(records[1]['units'], None)
            self.assertEqual(records[0]['id'], records[1]['id'])
            self.assertIn('Fixture/01_Database/central.sqlite', archive.namelist())
            self.assertIn('Fixture/05_Books/book.txt', archive.namelist())

    def test_missing_part_rejects_without_publishing_output(self):
        self.part().unlink()
        output = self.root / 'output.zip'
        with self.assertRaisesRegex(ValueError, 'Missing or truncated'):
            self.verify(output=output)
        self.assertFalse(output.exists())

    def test_corruption_rejects_without_publishing_output(self):
        with self.part().open('r+b') as stream:
            stream.write(b'corruption')
        output = self.root / 'output.zip'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.verify(output=output)
        self.assertFalse(output.exists())

    def test_reordered_parts_fail(self):
        self.document['parts'][0], self.document['parts'][1] = self.document['parts'][1], self.document['parts'][0]
        self.save()
        with self.assertRaisesRegex(ValueError, 'reordered'):
            self.verify()

    def test_duplicate_part_path_fails(self):
        self.document['parts'][1]['path'] = self.document['parts'][0]['path']
        self.save()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.verify()

    def test_missing_inventory_entry_fails(self):
        self.document['parts'].pop()
        self.save()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.verify()

    def test_truncated_or_oversized_part_fails(self):
        with self.part().open('ab') as stream:
            stream.write(b'extra')
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.verify()

    def test_unrecorded_extra_part_fails(self):
        (self.copy / 'parts/extra.part').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'Unrecorded'):
            self.verify()

    def test_unsafe_or_nonportable_part_paths_fail(self):
        for name in ('../part', '/absolute/part', 'C:\\part', 'parts//part', 'parts/./part',
                     'parts/NUL', 'parts/part.', 'parts/part:stream'):
            with self.subTest(name=name):
                self.document['parts'][0]['path'] = name
                self.save()
                with self.assertRaises(ValueError):
                    self.verify()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'Symbolic links unavailable')
    def test_linked_part_is_rejected(self):
        part = self.part()
        original = self.root / 'external'
        part.rename(original)
        part.symlink_to(original)
        with self.assertRaisesRegex(ValueError, 'Linked'):
            self.verify()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'Symbolic links unavailable')
    def test_linked_part_directory_is_rejected(self):
        original = self.root / 'external-parts'
        (self.copy / 'parts').rename(original)
        (self.copy / 'parts').symlink_to(original, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Linked'):
            self.verify()

    def test_foreign_source_identity_fails(self):
        self.document['archive']['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'different source archive'):
            self.verify()

    def test_forged_whole_archive_hash_fails_despite_matching_part_hashes(self):
        self.document['archive']['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'Reassembled archive identity differs'):
            package.verify_package(self.manifest, expected_archive=self.document['archive'])

    def test_forged_collection_coverage_fails(self):
        self.document['coverage']['collections'][0]['record_count'] = 99
        self.save()
        with self.assertRaisesRegex(ValueError, 'coverage differs'):
            self.verify()

    def test_missing_member_inventory_fails(self):
        (self.copy / 'member_inventory.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or oversized'):
            self.verify()

    def test_forged_member_inventory_fails(self):
        path = self.copy / 'member_inventory.json'
        document = json.loads(path.read_text())
        document['members'].pop()
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'coverage differs'):
            self.verify()

    @unittest.skipUnless(hasattr(os, 'symlink'), 'Symbolic links unavailable')
    def test_linked_member_inventory_fails(self):
        path = self.copy / 'member_inventory.json'
        outside = self.root / 'external-index'
        path.rename(outside)
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Linked'):
            self.verify()

    def test_existing_output_is_preserved(self):
        output = self.root / 'owner.zip'
        output.write_bytes(b'existing owner data')
        with self.assertRaises(FileExistsError):
            self.verify(output=output)
        self.assertEqual(output.read_bytes(), b'existing owner data')

    def test_existing_import_is_preserved(self):
        before = self.manifest.read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            package.build_package(self.source, self.copy, expected_archive=self.identity)
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_wrong_source_leaves_no_package(self):
        destination = self.root / 'wrong'
        wrong = {**self.identity, 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'expected size and SHA-256'):
            package.build_package(self.source, destination, expected_archive=wrong)
        self.assertFalse(destination.exists())

    def test_duplicate_manifest_keys_fail(self):
        text = self.manifest.read_text().replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')
        self.manifest.write_text(text)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            self.verify()

    def test_declared_member_hash_mismatch_fails(self):
        source = self.root / 'bad-binding.zip'
        make_archive(source, change=lambda d, p: d['files'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'delivery binding differs'):
            package.inspect_archive(source)

    def test_collection_requires_delivery_binding(self):
        source = self.root / 'unbound-collection.zip'
        make_archive(source, change=lambda d, p: d['files'].pop(0))
        with self.assertRaisesRegex(ValueError, 'no delivery binding'):
            package.inspect_archive(source)

    def test_duplicate_archive_member_fails(self):
        source = self.root / 'duplicate.zip'
        shutil.copyfile(self.source, source)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(source, 'a') as archive:
                archive.writestr('Fixture/' + package.COLLECTIONS['chronology'], b'[]')
        with self.assertRaisesRegex(ValueError, 'Duplicate archive member'):
            package.inspect_archive(source)

    def test_source_path_validation(self):
        for name in ('a/../b', '/absolute', 'a//b', 'a/./b', 'C:\\b', 'NUL.txt', 'a/b.', 'a/b '):
            with self.subTest(name=name), self.assertRaises(ValueError):
                package._safe_name(name)


class UnavailableManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-unavailable-test-')
        self.addCleanup(self.temp.cleanup)
        self.manifest = Path(self.temp.name) / 'manifest.json'
        self.document = {'schema_version': 1, 'id': 'historical-details',
                         'display_name': 'Historical Details', 'status': 'blocked_missing_source',
                         'archive': dict(package.EXPECTED_ARCHIVE),
                         'part_size_bytes': package.PART_SIZE, 'parts': [],
                         'source_verification': 'not_run_missing_source',
                         'coverage': {'archive_bytes': 'unavailable',
                                      'member_inventory': 'not_run', 'collections': []}}
        self.manifest.write_text(json.dumps(self.document))

    def test_missing_source_is_not_verified_or_complete(self):
        result = package.package_status(self.manifest)
        self.assertEqual(result['status'], 'blocked_missing_source')
        self.assertFalse(result['payload_present'])
        self.assertFalse(result['source_identity_verified'])
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            package.verify_package(self.manifest)

    def test_blocked_manifest_cannot_claim_payload(self):
        self.document['parts'] = [{'ordinal': 1}]
        self.manifest.write_text(json.dumps(self.document))
        with self.assertRaisesRegex(ValueError, 'inconsistent payload claims'):
            package.package_status(self.manifest)

    def test_cli_missing_payload_reports_bounded_error(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'IRGS_Catalog/historical_details_package.py'),
                                 'verify', str(self.manifest)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        error = json.loads(result.stderr)
        self.assertEqual(error['status'], 'unavailable_or_invalid')
        self.assertIn('unavailable', error['error'])

    def test_blocked_manifest_cannot_hide_a_part_directory(self):
        (self.manifest.parent / 'parts').mkdir()
        with self.assertRaisesRegex(ValueError, 'inconsistent payload claims'):
            package.package_status(self.manifest)

    def test_oversized_selection_manifest_is_rejected(self):
        self.manifest.write_bytes(b' ' * (package.MAX_MANIFEST + 1))
        with self.assertRaisesRegex(ValueError, 'oversized'):
            package.load_manifest(self.manifest)


if __name__ == '__main__':
    unittest.main()
