"""The integrated pair gets a new record; historical fixtures never get repinned."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import integrated_response_compatibility as compatibility


class IntegratedResponseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('evaluation/shared_responses_v1', 'evaluation/integrated_responses_v1'):
            shutil.copytree(CATALOG / directory, self.root / directory)
        library = self.root / compatibility.original.LIBRARY
        library.parent.mkdir(parents=True)
        shutil.copy2(CATALOG / compatibility.original.LIBRARY, library)

    def edit(self, mutate):
        path = self.root / compatibility.CONTRACT
        doc = json.loads(path.read_text())
        mutate(doc)
        path.write_text(json.dumps(doc))

    def test_separate_identity_selects_integrated_pair_and_preserves_original_consumers(self):
        doc = compatibility.load_contract(self.root)
        self.assertEqual(doc['consumers']['engine_commit'], '2f9476c6090878257d17cab3ad3a83a7ce18a5dc')
        original = compatibility.original.load_fixture(self.root)
        self.assertEqual(original['consumers']['engine_commit'], '9ecf3b8864f5f93be6b15c8cf6087e6bd66c8443')
        self.assertNotEqual(doc['consumers'], original['consumers'])
        self.assertFalse(compatibility.validate_compatibility(self.root)['runtime_execution_verified_by_schema'])

    def test_exported_actor_inputs_are_original_detached_documents_without_oracle(self):
        for context in ('rise', 'quay'):
            actual = compatibility.export_actor_input(context, self.root)
            self.assertEqual(actual, compatibility.original.export_actor_input(context, self.root))
            self.assertNotIn('PRIVATE_', json.dumps(actual))
            self.assertNotIn('evaluator', json.dumps(actual))
            actual['cases'].clear()
            self.assertTrue(compatibility.export_actor_input(context, self.root)['cases'])

    def test_original_consumer_repin_is_rejected_even_when_it_is_a_valid_commit(self):
        path = self.root / compatibility.SOURCE
        doc = json.loads(path.read_text())
        doc['consumers']['engine_commit'] = 'a' * 40
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            compatibility.load_contract(self.root)

    def test_rehashed_original_payload_cannot_relabel_old_evidence(self):
        directory = self.root / compatibility.original.FIXTURE
        path = directory / 'actor_inputs/quay.json'
        path.write_text(path.read_text() + ' ')
        manifest = directory / 'manifest.json'
        doc = json.loads(manifest.read_text())
        doc['files_sha256']['actor_inputs/quay.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            compatibility.load_contract(self.root)

    def test_original_fixture_path_and_rights_cannot_be_replaced(self):
        self.edit(lambda doc: doc['source_fixture'].update(manifest='evaluator_only/oracle.json'))
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            compatibility.load_contract(self.root)
        shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
        self.edit(lambda doc: doc['rights'].update(external_processing='allowed'))
        with self.assertRaisesRegex(ValueError, 'rights'):
            compatibility.load_contract(self.root)

    def test_branch_names_and_reuse_of_old_pair_are_rejected(self):
        self.edit(lambda doc: doc['consumers'].update(app_commit='main'))
        with self.assertRaisesRegex(ValueError, 'Exact integrated'):
            compatibility.load_contract(self.root)
        shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
        old = compatibility.original.load_fixture(self.root)['consumers']
        self.edit(lambda doc: doc.update(consumers=old))
        with self.assertRaisesRegex(ValueError, 'own consumer pair'):
            compatibility.load_contract(self.root)

    def test_paid_counts_boolean_counts_and_foreign_presentation_fields_fail_intake(self):
        for changes in ({'provider_calls': 1}, {'model_tokens': False}, {'saved_result_field': 'private'}):
            with self.subTest(changes=changes):
                shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
                self.edit(lambda doc: doc['presentation_contract'].update(changes))
                with self.assertRaises(ValueError):
                    compatibility.load_contract(self.root)

    def test_single_context_unknown_fields_duplicate_json_and_links_fail_intake(self):
        for mutate in (lambda doc: doc.update(context_ids=['rise']),
                       lambda doc: doc.update(provider_route='not-content')):
            shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
            self.edit(mutate)
            with self.assertRaises(ValueError):
                compatibility.load_contract(self.root)
        path = self.root / compatibility.CONTRACT
        path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            compatibility.load_contract(self.root)
        path.unlink()
        path.symlink_to(CATALOG / compatibility.CONTRACT)
        with self.assertRaisesRegex(ValueError, 'Linked'):
            compatibility.load_contract(self.root)


if __name__ == '__main__':
    unittest.main()
