"""Published starts get new evidence without changing earlier fixture selections."""
import json
import shutil
import unittest

from tools.tests import test_development_interop_contract as previous
import phase_response_compatibility as compatibility


class PhaseResponseContractTests(unittest.TestCase):
    def setUp(self):
        previous.DevelopmentInteropContractTests.setUp(self)
        directory = 'evaluation/phase_responses_v1'
        shutil.copytree(previous.CATALOG / directory, self.root / directory)

    def edit(self, mutate):
        path = self.root / compatibility.CONTRACT
        doc = json.loads(path.read_text())
        mutate(doc)
        path.write_text(json.dumps(doc))

    def reset(self):
        shutil.copy2(previous.CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)

    def test_separate_record_selects_pinned_engine_and_preserves_received_only_baseline(self):
        doc = compatibility.load_contract(self.root)
        old = compatibility.baseline.load_contract(self.root)
        self.assertTrue(doc['process_contract']['public_start_available'])
        self.assertFalse(old['process_contract']['public_start_available'])
        self.assertEqual(doc['consumers']['engine_commit'], doc['consumers']['app_engine_pin'])
        self.assertEqual(doc['consumers']['app_catalog_pin'], '526404128830a99fe8ea5c2bce43b6ea7d45fe6f')
        self.assertFalse(compatibility.validate_compatibility(self.root)['runtime_execution_verified_by_schema'])

    def test_original_matrix_cannot_be_repinned(self):
        path = self.root / compatibility.SOURCE
        doc = json.loads(path.read_text())
        doc['consumers']['app_commit'] = 'a' * 40
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'interoperability bytes changed'):
            compatibility.load_contract(self.root)

    def test_exact_pins_are_required_and_old_app_cannot_claim_starts(self):
        for changes in ({'app_commit': 'main'}, {'engine_commit': 'a' * 40},
                        {'app_commit': '67411f8ef5214c8cb51af2b244590751e6ea20df'}):
            self.reset()
            self.edit(lambda doc: doc['consumers'].update(changes))
            with self.assertRaises(ValueError):
                compatibility.load_contract(self.root)

    def test_private_interfaces_or_unpublished_commands_cannot_be_claimed(self):
        for changes in ({'public_start_available': False}, {'commands': ['start', 'communicate']},
                        {'view_field': 'raw_world'}, {'schema_version': True}):
            self.reset()
            self.edit(lambda doc: doc['process_contract'].update(changes))
            with self.assertRaises(ValueError):
                compatibility.load_contract(self.root)

    def test_rights_usage_contexts_and_joined_approval_cannot_be_relaxed(self):
        for mutate in (lambda doc: doc['rights'].update(external_processing='allowed'),
                       lambda doc: doc['presentation_contract'].update(model_tokens=False),
                       lambda doc: doc['presentation_contract'].update(provider_calls=1),
                       lambda doc: doc.update(context_ids=['rise']),
                       lambda doc: doc.update(qualification_scope='joined_approved')):
            self.reset()
            self.edit(mutate)
            with self.assertRaises(ValueError):
                compatibility.load_contract(self.root)

    def test_original_actor_exports_stay_detached_and_oracle_free(self):
        original = compatibility.baseline.baseline.original
        for context in ('rise', 'quay'):
            doc = original.export_actor_input(context, self.root)
            self.assertNotIn('PRIVATE_', json.dumps(doc))
            self.assertNotIn('evaluator', json.dumps(doc))
            doc['cases'].clear()
            self.assertTrue(original.export_actor_input(context, self.root)['cases'])

    def test_unknown_duplicate_and_linked_documents_fail_intake(self):
        self.edit(lambda doc: doc.update(provider_route='not-catalog-data'))
        with self.assertRaises(ValueError):
            compatibility.load_contract(self.root)
        path = self.root / compatibility.CONTRACT
        path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            compatibility.load_contract(self.root)
        path.unlink()
        path.symlink_to(previous.CATALOG / compatibility.CONTRACT)
        with self.assertRaisesRegex(ValueError, 'Linked'):
            compatibility.load_contract(self.root)


if __name__ == '__main__':
    unittest.main()
