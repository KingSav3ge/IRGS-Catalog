"""Current source matrix must not rewrite reviewed pins or old evidence."""
import json
from pathlib import Path
import shutil
import sys
import unittest

from tools.tests import test_integrated_response_contract as original_tests

CATALOG = original_tests.CATALOG
sys.path.insert(0, str(CATALOG))
import development_interop_compatibility as compatibility


class DevelopmentInteropContractTests(unittest.TestCase):
    def setUp(self):
        original_tests.IntegratedResponseContractTests.setUp(self)
        directory = 'evaluation/development_interop_v1'
        shutil.copytree(CATALOG / directory, self.root / directory)

    def edit(self, mutate):
        path = self.root / compatibility.CONTRACT
        doc = json.loads(path.read_text())
        mutate(doc)
        path.write_text(json.dumps(doc))

    def test_development_and_pinned_engine_are_explicit_distinct_selections(self):
        doc = compatibility.load_contract(self.root)
        consumers = doc['consumers']
        self.assertNotEqual(consumers['engine_commits']['development'], consumers['app_engine_pin'])
        self.assertEqual(consumers['engine_commits']['app_pinned'], consumers['app_engine_pin'])
        self.assertEqual(consumers['app_catalog_pin'], '27fff8385d1c01fdfe9ad7254b7647e6bc12a01e')
        self.assertFalse(compatibility.validate_compatibility(self.root)['runtime_execution_verified_by_schema'])

    def test_old_integrated_record_cannot_be_repinned_to_current_heads(self):
        path = self.root / compatibility.SOURCE
        doc = json.loads(path.read_text())
        doc['consumers']['app_commit'] = 'a' * 40
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'compatibility bytes changed'):
            compatibility.load_contract(self.root)

    def test_branch_names_and_pinned_role_mismatches_fail_intake(self):
        self.edit(lambda doc: doc['consumers']['engine_commits'].update(development='main'))
        with self.assertRaisesRegex(ValueError, 'Exact development'):
            compatibility.load_contract(self.root)
        shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
        self.edit(lambda doc: doc['consumers']['engine_commits'].update(app_pinned='a' * 40))
        with self.assertRaisesRegex(ValueError, 'Pinned Engine role'):
            compatibility.load_contract(self.root)

    def test_unpublished_start_or_command_cannot_be_claimed(self):
        for changes in ({'public_start_available': True}, {'commands': ['start']}, {'view_field': 'raw_world'}):
            shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
            self.edit(lambda doc: doc['process_contract'].update(changes))
            with self.assertRaisesRegex(ValueError, 'received-process'):
                compatibility.load_contract(self.root)

    def test_rights_paid_calls_and_joined_approval_claims_fail_intake(self):
        for mutate in (lambda doc: doc['rights'].update(external_processing='allowed'),
                       lambda doc: doc['presentation_contract'].update(provider_calls=1),
                       lambda doc: doc.update(qualification_scope='joined_approved')):
            shutil.copy2(CATALOG / compatibility.CONTRACT, self.root / compatibility.CONTRACT)
            self.edit(mutate)
            with self.assertRaises(ValueError):
                compatibility.load_contract(self.root)

    def test_unknown_fields_duplicate_json_and_linked_records_fail_intake(self):
        self.edit(lambda doc: doc.update(provider_config={}))
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
