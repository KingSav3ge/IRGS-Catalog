"""Separate source selection and unresolved source/App boundaries stay explicit."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import start_context_evaluation as evaluation


class StartContextContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for directory in (evaluation.FIXTURE, evaluation.baseline.FIXTURE):
            shutil.copytree(CATALOG / directory, self.root / directory)

    def edit(self, name, mutate):
        directory = self.root / evaluation.FIXTURE
        path = directory / name; doc = json.loads(path.read_text()); mutate(doc)
        path.write_text(json.dumps(doc))
        if name != 'manifest.json':
            manifest = directory / 'manifest.json'; doc = json.loads(manifest.read_text())
            doc['files_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(doc))

    def test_published_engine_and_pending_app_are_distinct_from_original_baseline(self):
        doc = evaluation.load_fixture(self.root)
        self.assertEqual(doc['engine_contract']['schema'], 'irgs-start-readiness-1')
        self.assertEqual(len(doc['contexts']), 6)
        self.assertIsNone(doc['app_adoption']['qualified_app_commit'])
        summary = evaluation.validate_fixture(self.root)
        self.assertFalse(summary['engine_execution_verified_by_schema'])
        self.assertFalse(summary['app_execution_qualified'])
        self.assertEqual(evaluation.baseline.load_fixture(self.root)['consumers']['engine_commit'],
            '91b20056e7db651966c9e92925313494917f47b1')

    def test_actor_exports_are_detached_and_do_not_include_oracle_or_source_findings(self):
        for case in evaluation.CASES:
            doc = evaluation.export_actor_input(case, self.root)
            for private in ('PRIVATE_', 'evaluator_only', 'boarding_date_resolution', 'source_review'):
                self.assertNotIn(private, json.dumps(doc))
            doc['selection'].clear()
            self.assertTrue(evaluation.export_actor_input(case, self.root)['selection'])

    def test_old_baseline_cannot_be_rehashed_or_repinned(self):
        path = self.root / evaluation.BASELINE
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'baseline bytes changed'):
            evaluation.load_fixture(self.root)

    def test_uncertainty_cannot_be_resolved_into_precise_location_boarding_date_or_hour(self):
        for changes in ({'accepted_precision': 'specific_ship'}, {'boarding_date_resolution': '7 August'},
                        {'opening_hour': '09:00'}, {'john_personal_context': 'at_the_quay'},
                        {'primary_documents_independently_collated': True}, {'articles_reproduced': True}):
            shutil.copytree(CATALOG / evaluation.FIXTURE, self.root / evaluation.FIXTURE, dirs_exist_ok=True)
            self.edit('source_review.json', lambda doc: doc.update(changes))
            with self.assertRaisesRegex(ValueError, 'source uncertainty'):
                evaluation.load_fixture(self.root)

    def test_rehashed_actor_substitutions_cannot_attach_henry_or_courier_fiction_to_john(self):
        self.edit('actor_inputs/john-1415-limited.json',
            lambda doc: doc['selection']['character'].update(opening_id='henry-1415-embarkation-v1'))
        with self.assertRaisesRegex(ValueError, 'actor-bound'):
            evaluation.load_fixture(self.root)

    def test_unexecuted_app_acceptance_cannot_be_promoted_by_metadata(self):
        self.edit('app_acceptance.json', lambda doc: doc.update(status='qualified', qualified_app_commit='a' * 40))
        with self.assertRaisesRegex(ValueError, 'Pending App acceptance'):
            evaluation.load_fixture(self.root)

    def test_paid_rights_branch_names_and_single_context_cannot_replace_the_selection(self):
        for mutate in (lambda doc: doc['rights'].update(external_processing='allowed'),
                       lambda doc: doc['engine_contract'].update(commit='main'),
                       lambda doc: doc['contexts'].pop('henry-1415-default')):
            shutil.copytree(CATALOG / evaluation.FIXTURE, self.root / evaluation.FIXTURE, dirs_exist_ok=True)
            self.edit('manifest.json', mutate)
            with self.assertRaises(ValueError):
                evaluation.load_fixture(self.root)

    def test_unknown_payload_duplicate_fields_and_linked_sources_fail_intake(self):
        directory = self.root / evaluation.FIXTURE
        extra = directory / 'private-save.json'; extra.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            evaluation.load_fixture(self.root)
        extra.unlink()
        manifest = directory / 'manifest.json'; manifest.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            evaluation.load_fixture(self.root)
        manifest.unlink(); manifest.symlink_to(CATALOG / evaluation.FIXTURE / 'manifest.json')
        with self.assertRaisesRegex(ValueError, 'Linked'):
            evaluation.load_fixture(self.root)


if __name__ == '__main__':
    unittest.main()
