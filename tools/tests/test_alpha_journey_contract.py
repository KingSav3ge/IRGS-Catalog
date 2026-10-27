"""Journey actor input, observed receipts and unmet acceptance stay separate."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import alpha_journey_evaluation as evaluation


class AlphaJourneyContractTests(unittest.TestCase):
    def evidence(self):
        return {'case_id': 'quay-contact', 'engine_commit': 'ea0631b8fbf94f425fa003d81b6907445a9a43c5',
            'app_commit': 'b3a53cfd11bbd3745253520b4e8ed6718c826ab8',
            'app_engine_pin': 'efc84364b86e640f5028bfac2dfd5ae3021695a9', 'sessions': 2,
            'receipt_ids': ['receipt-one', 'receipt-two'], 'retry_verified': True, 'restore_verified': True,
            'pending_requirements': list(evaluation.REQUIRED), 'alpha_qualified': False}

    def test_fixture_preserves_baseline_and_two_distinct_actor_inputs(self):
        self.assertFalse(evaluation.validate_fixture()['runtime_execution_verified_by_schema'])
        for case in evaluation.CASES:
            actor = evaluation.export_actor_input(case)
            self.assertNotIn('PRIVATE_', json.dumps(actor)); self.assertNotIn('evaluator_only', json.dumps(actor))
            actor['actions'].clear(); self.assertTrue(evaluation.export_actor_input(case)['actions'])

    def test_partial_evidence_requires_realistic_scope_and_cannot_grant_alpha(self):
        report = evaluation.assess_evidence(self.evidence())
        self.assertTrue(report['engine_override']); self.assertFalse(report['alpha_qualified'])
        self.assertFalse(report['runtime_execution_verified_by_schema'])
        for changes in ({'alpha_qualified': True}, {'pending_requirements': []}, {'sessions': True},
                        {'sessions': 1}, {'receipt_ids': ['same', 'same']},
                        {'app_engine_pin': 'ea0631b8fbf94f425fa003d81b6907445a9a43c5'},
                        {'private_world': {}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                evaluation.assess_evidence({**self.evidence(), **changes})


if __name__ == '__main__':
    unittest.main()
