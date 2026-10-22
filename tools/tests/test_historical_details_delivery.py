"""Acceptance checks against the actual complete Catalog delivery.

Optional Engine/App checks select explicit source snapshots through environment
variables; they do not edit another component or change dependency pointers.
"""
import hashlib
import errno
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'IRGS_Catalog'))
import historical_details_package as package


def link_or_copy(source, destination):
    try:
        os.link(source, destination)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.copyfile(source, destination)


class DeliveryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-real-source-check-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = package.DEFAULT_MANIFEST.parent
        self.document = package.load_manifest()
        self.assertEqual(self.document['status'], 'complete', 'Actual delivery is not complete')

    def clone(self):
        destination = self.root / 'source'
        destination.mkdir()
        shutil.copyfile(self.source / 'manifest.json', destination / 'manifest.json')
        shutil.copyfile(self.source / 'member_inventory.json', destination / 'member_inventory.json')
        (destination / 'parts').mkdir()
        for part in self.document['parts']:
            # These links are read-only in tests. Mutation replaces a link with
            # a private copy first; unlinking a fixture never changes the source.
            link_or_copy(self.source / part['path'], destination / part['path'])
        return destination


class ActualDeliveryTests(DeliveryFixture):
    def test_actual_complete_zip_reassembles_and_verifies_every_member(self):
        output = self.root / 'original.zip'
        result = package.verify_package(output=output)
        self.assertEqual(output.stat().st_size, package.EXPECTED_ARCHIVE['bytes'])
        with output.open('rb') as stream:
            self.assertEqual(package._hash_stream(stream)[1], package.EXPECTED_ARCHIVE['sha256'])
        self.assertEqual(result['parts'], 32)
        self.assertEqual(result['collection_bindings_verified'], 10)
        self.assertEqual(result['archive_coverage'], 'complete')
        self.assertFalse(result['historical_truth_verified'])

    def test_actual_missing_part_fails_without_publishing_output(self):
        source = self.clone()
        (source / self.document['parts'][0]['path']).unlink()
        output = self.root / 'rejected.zip'
        with self.assertRaisesRegex(ValueError, 'Missing or truncated'):
            package.verify_package(source / 'manifest.json', output=output)
        self.assertFalse(output.exists())

    def test_actual_corruption_fails_without_publishing_output(self):
        source = self.clone()
        part = source / self.document['parts'][0]['path']
        data = part.read_bytes()
        part.unlink()
        part.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        output = self.root / 'rejected.zip'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            package.verify_package(source / 'manifest.json', output=output)
        self.assertFalse(output.exists())
        self.assertEqual(hashlib.sha256((self.source / self.document['parts'][0]['path']).read_bytes()).hexdigest(),
                         self.document['parts'][0]['sha256'])

    def test_actual_reordered_parts_fail(self):
        source = self.clone()
        self.document['parts'][:2] = reversed(self.document['parts'][:2])
        (source / 'manifest.json').write_text(json.dumps(self.document))
        with self.assertRaisesRegex(ValueError, 'reordered'):
            package.verify_package(source / 'manifest.json')

    def test_actual_duplicate_part_fails(self):
        source = self.clone()
        self.document['parts'][1]['path'] = self.document['parts'][0]['path']
        (source / 'manifest.json').write_text(json.dumps(self.document))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            package.verify_package(source / 'manifest.json')


@unittest.skipUnless(os.environ.get('IRGS_HISTORICAL_ENGINE_RUNTIME')
                     and os.environ.get('IRGS_HISTORICAL_APP_SOURCE'),
                     'Explicit Engine/App source snapshots required for cross-component checks')
class ActualReaderCompatibilityTests(DeliveryFixture):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.environ['IRGS_HISTORICAL_ENGINE_RUNTIME'])
        sys.path.insert(0, os.environ['IRGS_HISTORICAL_APP_SOURCE'])
        from historical_archive import from_catalog_manifest
        from historical_reference import HistoricalReferences
        cls.factory = staticmethod(from_catalog_manifest)
        cls.references = HistoricalReferences

    def references_for(self, manifest, *, pin=None):
        return self.references(config=self.root / 'no-owner-registration.json', manifest=manifest,
                               manifest_pin=pin, cache=self.root / 'installation-cache')

    def test_engine_reads_complete_real_archive_and_preserves_source_rows(self):
        manifest = self.source / 'manifest.json'
        pin = hashlib.sha256(manifest.read_bytes()).hexdigest()
        library = self.factory(manifest, pin, cache_dir=self.root / 'engine-cache')
        status = library.verify_collections()
        self.assertEqual(status['storage'], 'catalog_parts')
        self.assertEqual(status['sha256'], package.EXPECTED_ARCHIVE['sha256'])
        self.assertEqual(len(status['collections']), 10)
        for collection in self.document['coverage']['collections']:
            if collection['record_count']:
                page = library.search(collection['id'], '', limit=1)
                self.assertEqual(len(page['results']), 1)
                detail = library.record(collection['id'], page['results'][0]['row'])
                self.assertEqual(detail['reference']['archive_sha256'], package.EXPECTED_ARCHIVE['sha256'])
                self.assertFalse(detail['campaign_effects'])
                self.assertFalse(detail['adoption_performed'])

    def test_app_service_selects_catalog_release_pin_and_reads_real_source(self):
        references = self.references_for(self.source / 'manifest.json')
        status = references.status()
        self.assertEqual(status['status'], 'attached_read_only')
        self.assertEqual(status['source_kind'], 'catalog_multipart')
        self.assertEqual(status['title'], 'Historical Details')
        page = references.read('search', 'chronology', '', limit=1)
        detail = references.read('record', 'chronology', page['results'][0]['row'])
        self.assertFalse(detail['campaign_effects'])
        self.assertFalse(detail['adoption_performed'])
        self.assertFalse((self.root / 'no-owner-registration.json').exists())

    def test_app_reports_actual_missing_part_and_recovers_without_source_edits(self):
        source = self.clone()
        part = source / self.document['parts'][0]['path']
        part.unlink()
        pin = hashlib.sha256((source / 'manifest.json').read_bytes()).hexdigest()
        references = self.references_for(source / 'manifest.json', pin=pin)
        self.assertEqual(references.status()['status'], 'incomplete')
        self.assertFalse((self.root / 'installation-cache').exists())
        link_or_copy(self.source / self.document['parts'][0]['path'], part)
        self.assertEqual(references.status()['status'], 'attached_read_only')

    def test_app_reports_actual_corrupt_part_without_publishing_cache(self):
        source = self.clone()
        part = source / self.document['parts'][0]['path']
        data = part.read_bytes()
        part.unlink()
        part.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        pin = hashlib.sha256((source / 'manifest.json').read_bytes()).hexdigest()
        references = self.references_for(source / 'manifest.json', pin=pin)
        self.assertEqual(references.status()['status'], 'corrupt')
        cache = self.root / 'installation-cache'
        self.assertFalse(cache.exists() and list(cache.iterdir()))


if __name__ == '__main__':
    unittest.main()
