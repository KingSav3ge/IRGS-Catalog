"""Source intake, rights and actor/oracle separation for shared response checks."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import response_depot_compatibility as compatibility


class SharedResponseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(CATALOG / compatibility.FIXTURE, self.root / compatibility.FIXTURE)
        path = self.root / compatibility.LIBRARY
        path.parent.mkdir(parents=True)
        shutil.copy2(CATALOG / compatibility.LIBRARY, path)

    def update(self, name, mutate):
        path = self.root / compatibility.FIXTURE / name
        doc = json.loads(path.read_text())
        mutate(doc)
        path.write_text(json.dumps(doc))
        if name != 'manifest.json':
            manifest = self.root / compatibility.FIXTURE / 'manifest.json'
            value = json.loads(manifest.read_text())
            value['files_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(value))

    def test_two_supported_contexts_and_nine_cases_validate(self):
        result = compatibility.validate_fixture(self.root)
        self.assertEqual((result['contexts'], result['non_rise_contexts'], result['cases']), (2, 1, 9))
        self.assertFalse(result['runtime_execution_verified_by_schema'])

    def test_actor_export_excludes_oracle_and_returns_detached_data(self):
        for context in ('rise', 'quay'):
            exported = compatibility.export_actor_input(context, self.root)
            text = json.dumps(exported)
            for forbidden in ('PRIVATE_', 'evaluator', 'expected', 'duration_seconds', 'total_seconds', 'status'):
                self.assertNotIn(forbidden, text)
            exported['cases'].clear()
            self.assertTrue(compatibility.export_actor_input(context, self.root)['cases'])
        with self.assertRaisesRegex(ValueError, 'Unknown response context'):
            compatibility.export_actor_input('unpublished', self.root)

    def test_rehashed_hidden_oracle_field_in_actor_input_is_rejected(self):
        self.update('actor_inputs/quay.json', lambda doc: doc.update(expected='PRIVATE_INJECTED'))
        with self.assertRaisesRegex(ValueError, 'fields'):
            compatibility.load_fixture(self.root)

    def test_changed_rights_are_rejected(self):
        self.update('manifest.json', lambda doc: doc['rights'].update(external_processing='allowed'))
        with self.assertRaisesRegex(ValueError, 'rights'):
            compatibility.load_fixture(self.root)

    def test_unselected_initializer_cannot_create_an_adapter(self):
        self.update('manifest.json', lambda doc: doc['contexts']['quay']['selection'].update(opening_id='invented'))
        with self.assertRaisesRegex(ValueError, 'supported opening'):
            compatibility.load_fixture(self.root)

    def test_duplicate_case_identity_fails_even_after_source_refresh(self):
        self.update('actor_inputs/quay.json', lambda doc: doc['cases'][1].update(case_id=doc['cases'][0]['case_id']))
        with self.assertRaisesRegex(ValueError, 'Duplicate case'):
            compatibility.load_fixture(self.root)

    def test_invalid_elapsed_expectations_and_depot_revisions_are_rejected(self):
        self.update('evaluator_only/oracle.json', lambda doc: doc['cases']['quay-look'].update(duration_seconds=True))
        with self.assertRaisesRegex(ValueError, 'expected outcome'):
            compatibility.load_fixture(self.root)
        (self.root / compatibility.LIBRARY).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Depot source hash'):
            compatibility.load_fixture(self.root)

    def test_changed_payload_and_unexpected_payload_fail_intake(self):
        path = self.root / compatibility.FIXTURE / 'actor_inputs/quay.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'payload hash'):
            compatibility.load_fixture(self.root)
        path = self.root / compatibility.FIXTURE / 'actor_inputs/extra.json'
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected evaluation payload'):
            compatibility.load_fixture(self.root)


if __name__ == '__main__':
    unittest.main()
