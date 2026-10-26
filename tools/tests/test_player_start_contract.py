"""Reference verification and eligibility never suffice for playable acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import player_start_evaluation as evaluation


class PlayerStartContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(CATALOG / evaluation.FIXTURE, self.root / evaluation.FIXTURE)

    def edit_payload(self, name, mutate):
        path = self.root / evaluation.FIXTURE / name
        doc = json.loads(path.read_text()); mutate(doc)
        path.write_text(json.dumps(doc))
        manifest = self.root / evaluation.FIXTURE / 'manifest.json'
        doc = json.loads(manifest.read_text())
        doc['files_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(doc))

    def evidence(self, **changes):
        return {'schema_version': 1, 'case_id': 'john-1415-existing', 'explicit_mode': 'executable_slice',
            **{key: True for key in evaluation.BOOL_FIELDS}, **changes}

    def test_four_paths_and_pending_owner_contracts_are_explicit(self):
        doc = evaluation.load_fixture(self.root)
        self.assertEqual(tuple(doc['contexts']), evaluation.CASES)
        summary = evaluation.validate_fixture(self.root)
        self.assertFalse(summary['runtime_start_contract_implemented'])
        criteria = evaluation.load_evaluator_data(self.root)
        self.assertEqual(len(criteria['findings']), 3)
        self.assertTrue(criteria['pending_owner_contracts'])

    def test_exports_detach_actor_instructions_and_exclude_evaluator_truth(self):
        for case in evaluation.CASES:
            actor = evaluation.export_actor_input(case, self.root)
            self.assertNotIn('PRIVATE_', json.dumps(actor))
            self.assertNotIn('evaluator_only', json.dumps(actor))
            self.assertNotIn('baseline_note', json.dumps(actor))
            actor['selection'].clear()
            self.assertTrue(evaluation.export_actor_input(case, self.root)['selection'])

    def test_each_confirmed_loop_requirement_is_necessary(self):
        self.assertTrue(evaluation.assess_evidence(self.evidence())['supported_start_accepted'])
        for field in evaluation.LOOP_FIELDS:
            with self.subTest(field=field):
                report = evaluation.assess_evidence(self.evidence(**{field: False}))
                self.assertFalse(report['loop_verified'])
                self.assertFalse(report['supported_start_accepted'])
                self.assertFalse(report['runtime_authorization_granted'])

    def test_reference_eligibility_labels_or_drafts_cannot_stand_in_for_execution(self):
        doc = self.evidence(**{key: False for key in evaluation.BOOL_FIELDS})
        doc.update(reference_ready=True, actor_eligible=True, mode_confirmed=True)
        report = evaluation.assess_evidence(doc)
        self.assertFalse(report['supported_start_accepted'])
        self.assertFalse(report['mode_review_verified'])
        with self.assertRaises(ValueError):
            evaluation.assess_evidence({**doc, 'draft_text': 'An army awaits you.'})

    def test_working_loop_is_distinct_from_mode_review_and_civil_date(self):
        for changes in ({'explicit_mode': 'unclassified'}, {'mode_confirmed': False},
                        {'civil_date_matches_source': False}, {'reference_ready': False}):
            report = evaluation.assess_evidence(self.evidence(**changes))
            self.assertTrue(report['loop_verified'])
            self.assertFalse(report['supported_start_accepted'])
        report = evaluation.assess_evidence(self.evidence(explicit_mode='declaration_only'))
        self.assertTrue(report['mode_review_verified'])
        self.assertFalse(report['supported_start_accepted'])
        report = evaluation.assess_evidence(self.evidence(case_id='rise-r00', civil_date_matches_source=False))
        self.assertFalse(report['civil_date_required'])
        self.assertFalse(report['civil_date_verified'])
        self.assertTrue(report['supported_start_accepted'])

    def test_ambiguous_types_and_unknown_private_fields_fail(self):
        for changes in ({'reference_ready': 1}, {'schema_version': True}, {'case_id': 'unreviewed'},
                        {'explicit_mode': 'ready'}, {'private_world': {}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                evaluation.assess_evidence(self.evidence(**changes))

    def test_rehashed_requirements_cannot_promote_source_claims_or_invent_an_hour(self):
        self.edit_payload('requirements/john_1415.json', lambda doc: doc['opening'].update(time='09:00'))
        with self.assertRaisesRegex(ValueError, 'hour'):
            evaluation.load_fixture(self.root)
        shutil.copytree(CATALOG / evaluation.FIXTURE, self.root / evaluation.FIXTURE, dirs_exist_ok=True)
        self.edit_payload('requirements/john_1415.json', lambda doc: doc['reference_claims'][0].update(access='actor_received'))
        with self.assertRaisesRegex(ValueError, 'player knowledge'):
            evaluation.load_fixture(self.root)

    def test_rehashed_historical_person_cannot_receive_fictional_courier_start(self):
        self.edit_payload('actor_inputs/john-1415-existing.json',
            lambda doc: doc['selection']['character'].update(opening_id='quay-delivery-v1'))
        with self.assertRaisesRegex(ValueError, 'fictional circumstances'):
            evaluation.load_fixture(self.root)

    def test_rights_payload_edits_duplicate_fields_and_links_fail(self):
        directory = self.root / evaluation.FIXTURE
        path = directory / 'actor_inputs/new-1415-default.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            evaluation.load_fixture(self.root)
        shutil.copy2(CATALOG / evaluation.FIXTURE / 'actor_inputs/new-1415-default.json', path)
        manifest = directory / 'manifest.json'
        doc = json.loads(manifest.read_text()); doc['rights']['external_processing'] = 'allowed'
        manifest.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'rights'):
            evaluation.load_fixture(self.root)
        manifest.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            evaluation.load_fixture(self.root)
        manifest.unlink(); manifest.symlink_to(CATALOG / evaluation.FIXTURE / 'manifest.json')
        with self.assertRaisesRegex(ValueError, 'Linked'):
            evaluation.load_fixture(self.root)


if __name__ == '__main__':
    unittest.main()
