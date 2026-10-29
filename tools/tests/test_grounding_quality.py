"""Adversarial evaluator cases; no claim of automatic semantic review."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'IRGS_Catalog'))
import grounding_quality as rubric
import world_authoring_examples as worlds


class GroundingQualityTests(unittest.TestCase):
    def setUp(self):
        self.input = {'actor_id': 'courier', 'intention': 'I enter the passage.', 'context': {'received': []},
                      'allowed_actions': ['enter-passage', 'look-quay'], 'source_refs': ['received-1']}
        self.proposal = {'intention': self.input['intention'], 'action_id': 'enter-passage', 'source_refs': ['received-1']}
        self.receipt = {'event_id': 'communication:sample', 'status': 'testimony_received',
                        'truth_status': 'testimony', 'utterance': 'I heard a rumor.'}

    def test_valid_structural_proposal_cannot_infer_intent_semantics(self):
        unknown = {'status': 'unknown', 'evidence_refs': []}
        result = rubric.assess_proposal(self.input, self.proposal, unknown)
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['semantic_inference_performed'])
        self.assertFalse(result['action_authorized'])
        wrong = {**self.proposal, 'action_id': 'look-quay'}
        result = rubric.assess_proposal(self.input, wrong, {'status': 'fail', 'evidence_refs': ['player-intention', 'action-review']})
        self.assertEqual(result['violations'], ['intent_mismatch_reported'])
        with self.assertRaises(ValueError):
            rubric.assess_proposal(self.input, self.proposal, {'status': 'pass', 'evidence_refs': []})

    def test_changed_intention_unreceived_sources_and_actions_fail_even_if_review_passes(self):
        annotation = {'status': 'pass', 'evidence_refs': ['human-review']}
        bad = {'intention': 'different', 'action_id': 'hidden-action', 'source_refs': ['hidden-source']}
        self.assertEqual(set(rubric.assess_proposal(self.input, bad, annotation)['violations']),
                         {'changed_intention', 'unreceived_action', 'unreceived_source'})
        self.assertEqual(rubric.assess_proposal(self.input, {**self.proposal, 'source_refs': ['received-1', 'received-1']}, annotation)['status'], 'fail')
        with self.assertRaises(ValueError):
            rubric.assess_proposal({**self.input, 'private_state': 'secret'}, self.proposal, annotation)

    def test_receipt_contradictions_never_become_supported_outcomes(self):
        self.assertEqual(rubric.assess_receipt(self.receipt, dict(self.receipt))['status'], 'exact_structured_match')
        for key, value in [('status', 'fulfilled'), ('truth_status', 'fact'), ('utterance', 'Changed.'), ('event_id', 'other')]:
            result = rubric.assess_receipt(self.receipt, {**self.receipt, key: value})
            self.assertEqual((result['status'], result['mismatches']), ('fail', [key]))
            self.assertFalse(result['live_model_quality_verified'])
        with self.assertRaises(ValueError):
            rubric.assess_receipt(self.receipt, {**self.receipt, 'hidden': 'invented'})

    def test_review_unknown_and_failure_remain_explicit(self):
        judgments = {key: {'status': 'unknown', 'evidence_refs': []} for key in rubric.DIMENSIONS}
        self.assertEqual(rubric.assess_review(judgments)['status'], 'unknown')
        judgments['npc_response'] = {'status': 'fail', 'evidence_refs': ['no-response-receipt']}
        result = rubric.assess_review(judgments)
        self.assertEqual(result['status'], 'fail')
        self.assertFalse(result['alpha_qualified'])
        self.assertFalse(result['reviewer_claims_verified'])
        with self.assertRaises(ValueError):
            rubric.assess_review({key: value for key, value in judgments.items() if key != 'hidden_information'})

    def test_fixture_separation_and_unmet_journey_requirements(self):
        result = rubric.validate_fixture(ROOT / 'IRGS_Catalog')
        self.assertEqual(result['cases'], 2)
        self.assertFalse(result['alpha_qualified'])
        self.assertFalse(result['semantic_inference_performed'])


class WorldAuthoringExamplesTests(unittest.TestCase):
    def test_two_original_families_are_requirements_only(self):
        examples = worlds.load()
        result = worlds.validate_fixture(ROOT / 'IRGS_Catalog')
        self.assertEqual({x['family'] for x in examples['examples']}, {'personal-adventure', 'settlement'})
        self.assertFalse(result['engine_validation_performed'])
        self.assertFalse(result['world_creation_performed'])
        self.assertFalse(result['alpha_qualified'])

    def test_invalid_references_duplicates_units_and_unsafe_extra_fields_reject(self):
        data = worlds.load()
        changes = [lambda d: d['examples'][0]['places'][1].update(id='landing'),
                   lambda d: d['examples'][0]['links'][0].update(to='missing'),
                   lambda d: d['examples'][0].update(units='guessed'),
                   lambda d: d['examples'][0]['proposed_items'][0].update(custody_actor='stranger'),
                   lambda d: d['examples'][0]['initial_knowledge'][0].update(actor='clerk'),
                   lambda d: d['examples'][0].update(executable='untrusted.py'),
                   lambda d: d['examples'][1].update(family='personal-adventure')]
        for mutate in changes:
            bad = copy.deepcopy(data); mutate(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                worlds.validate(bad)
