"""Fixture intake failures must survive refreshed per-file hashes."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import solo_evaluation as evaluation


class SoloFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-synthetic-solo-schema-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'fixture'
        shutil.copytree(evaluation.DEFAULT_ROOT, self.root)

    def read(self, name):
        return json.loads((self.root / name).read_text())

    def write(self, name, document):
        path = self.root / name
        path.write_text(json.dumps(document))
        if name != 'manifest.json':
            manifest = self.read('manifest.json')
            for binding in [*manifest['actor_inputs'].values(), *manifest['evaluator_only'].values()]:
                if binding['path'] == name:
                    binding['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.write('manifest.json', manifest)

    def test_complete_fixture_validates_and_grants_no_runtime_approval(self):
        result = evaluation.validate_fixture(self.root)
        self.assertEqual(result['cases'], 10)
        self.assertEqual(result['legitimate_actions'], 5)
        self.assertFalse(result['runtime_execution_verified_by_schema'])
        self.assertFalse(result['public_discovery'])

    def test_export_does_not_open_or_require_any_evaluator_files(self):
        expected = evaluation.export_actor_input('solo-walk', self.root)
        shutil.rmtree(self.root / 'evaluator_only')
        self.assertEqual(evaluation.export_actor_input('solo-walk', self.root), expected)
        with self.assertRaises(FileNotFoundError):
            evaluation.validate_fixture(self.root)

    def test_oracle_paths_cannot_be_exported_as_actor_inputs_even_when_rehashed(self):
        manifest = self.read('manifest.json')
        manifest['actor_inputs']['solo-walk'] = manifest['evaluator_only']['oracle']
        self.write('manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'path or audience'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_traversal_and_linked_actor_paths_are_rejected(self):
        manifest = self.read('manifest.json')
        manifest['actor_inputs']['solo-walk']['path'] = 'actor_inputs/../evaluator_only/oracle.json'
        self.write('manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'path or audience'):
            evaluation.export_actor_input('solo-walk', self.root)
        self.write('manifest.json', evaluation.load_manifest())
        actor = self.root / 'actor_inputs/solo-walk.json'
        actor.unlink()
        actor.symlink_to(self.root / 'evaluator_only/oracle.json')
        with self.assertRaisesRegex(ValueError, 'Linked fixture'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_tampering_without_refresh_is_rejected(self):
        path = self.root / 'actor_inputs/solo-walk.json'
        path.write_text(path.read_text().replace('Walk to', 'Run to'))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_hidden_field_is_rejected_even_after_hash_refresh(self):
        name = 'actor_inputs/solo-walk.json'
        actor = self.read(name)
        actor['context']['private_npc_inventory'] = {'grain': 4}
        self.write(name, actor)
        with self.assertRaisesRegex(ValueError, 'schema fields'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_hidden_marker_in_otherwise_valid_prose_fails_intake_after_refresh(self):
        name = 'actor_inputs/solo-walk.json'
        actor = self.read(name)
        actor['user_intent'] += ' ' + self.read('evaluator_only/oracle.json')['hidden_markers'][0]
        self.write(name, actor)
        with self.assertRaisesRegex(ValueError, 'Hidden oracle leaked'):
            evaluation.validate_fixture(self.root)
        with self.assertRaisesRegex(ValueError, 'Hidden oracle leaked'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_processing_rights_are_explicit_and_unknown_imports_cannot_inherit_them(self):
        original = self.read('manifest.json')
        for field, value in [('rights', {}), ('classification', 'public-domain'),
                             ('provenance', {**original['provenance'], 'historical_calibration': True})]:
            with self.subTest(field=field):
                self.write('manifest.json', {**original, field: value})
                with self.assertRaises(ValueError):
                    evaluation.validate_fixture(self.root)

    def test_release_or_provider_configuration_fields_are_rejected(self):
        original = self.read('manifest.json')
        for field, value in [('public_discovery', True), ('playable_start', True),
                             ('release_approved', True), ('provider_model', 'test-model')]:
            with self.subTest(field=field):
                self.write('manifest.json', {**original, field: value})
                with self.assertRaises(ValueError):
                    evaluation.validate_fixture(self.root)

    def test_actor_identity_intent_reference_and_numeric_types_are_checked(self):
        name = 'actor_inputs/solo-walk.json'
        original = self.read(name)
        for field, value in [('actor_id', 'oren'), ('intent_ref', 'unbound'), ('schema_version', True)]:
            with self.subTest(field=field):
                self.write(name, {**original, field: value})
                with self.assertRaises(ValueError):
                    evaluation.export_actor_input('solo-walk', self.root)
        original['context']['reserved_for_work']['timber'] = 7
        self.write(name, original)
        with self.assertRaisesRegex(ValueError, 'exceed inventory'):
            evaluation.export_actor_input('solo-walk', self.root)

    def test_duplicate_or_missing_case_and_unsupported_success_are_rejected(self):
        name = 'evaluator_only/oracle.json'
        original = self.read(name)
        for mode in ('duplicate', 'missing', 'unsupported_success', 'invalid_replay'):
            oracle = json.loads(json.dumps(original))
            if mode == 'duplicate': oracle['cases'].append(oracle['cases'][0])
            if mode == 'missing': oracle['cases'].pop()
            if mode == 'unsupported_success': oracle['cases'][1]['kind'] = 'legitimate'
            if mode == 'invalid_replay': oracle['cases'][5]['replay_of'] = 'solo-denied-build'
            with self.subTest(mode=mode):
                self.write(name, oracle)
                with self.assertRaises(ValueError):
                    evaluation.validate_fixture(self.root)

    def test_duplicate_json_keys_and_unknown_export_case_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown actor case'):
            evaluation.export_actor_input('solo-no-such-case', self.root)
        path = self.root / 'manifest.json'
        path.write_text(path.read_text().replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,'))
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON field'):
            evaluation.load_manifest(self.root)


if __name__ == '__main__':
    unittest.main()
