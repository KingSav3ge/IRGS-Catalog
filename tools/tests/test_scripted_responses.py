"""Typed content, grounding, whole-clause composition and player-agency checks."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import scripted_responses as responses


def context(source='host_status', state='proposal_ready', values=None, ref='status:request'):
    return dict(actor_id='founder', snapshot_id='synthetic-revision-1', source_ref=ref,
                source_kind=source, state=state, values={} if values is None else values)


def part(family, facts, variant=0):
    return {'family_id': family, 'variant': variant, 'context': facts}


class ScriptedResponseTests(unittest.TestCase):
    def setUp(self):
        self.library = responses.load_library()

    def family(self, identity):
        return next(f for f in self.library['families'] if f['id'] == identity)

    def test_large_authored_corpus_and_every_variant_renders_with_typed_facts(self):
        status = responses.validate_library(self.library)
        self.assertEqual((status['families'], status['variants'], status['recipes']), (82, 325, 12))
        for family in self.library['families']:
            values = {key: 2 if kind == 'integer' else 'synthetic received text' for key, kind in family['slots'].items()}
            facts = context(family['source_kind'], family['state'], values)
            for variant in range(len(family['variants'])):
                with self.subTest(family=family['id'], variant=variant):
                    text = responses.render_fragment(self.library, family['id'], facts, variant=variant)
                    self.assertTrue(text)
                    self.assertNotIn('{', text)

    def test_result_recipe_keeps_exact_receipt_including_negation_and_multiline_text(self):
        original = 'No goods changed hands.\nThe shelter is not complete.'
        facts = {'receipt.exact': context('committed_receipt', 'committed', {'receipt_text': original}, 'receipt:1'),
                 'elapsed.action': context('committed_receipt', 'committed', {'elapsed_seconds': 0}, 'receipt:1'),
                 'turn.next': context(state='waiting_for_player', ref='status:turn')}
        rendered = responses.compose_recipe(self.library, 'routine.result', facts)
        self.assertTrue(rendered.startswith(original + ' '))
        self.assertIn('0 seconds', rendered)

    def test_every_receipt_requires_its_anchor_and_cannot_be_rephrased_by_variants(self):
        elapsed = part('elapsed.action', context('committed_receipt', 'committed', {'elapsed_seconds': 300}))
        with self.assertRaisesRegex(ValueError, 'exact receipt'): responses.compose(self.library, [elapsed])
        with self.assertRaisesRegex(ValueError, 'required facts'):
            responses.compose_recipe(self.library, 'routine.result', {'elapsed.action': elapsed['context']})
        self.family('receipt.exact')['variants'] = ['You succeeded.']
        with self.assertRaises(ValueError): responses.validate_library(self.library)

    def test_cross_actor_or_snapshot_composition_is_rejected(self):
        first = part('proposal.ready', context())
        second = part('proposal.review', context())
        for key in ('actor_id', 'snapshot_id'):
            with self.subTest(key=key):
                altered = copy.deepcopy(second)
                altered['context'][key] = 'other'
                with self.assertRaisesRegex(ValueError, 'actors or snapshots'):
                    responses.compose(self.library, [first, altered])

    def test_wrong_source_state_extra_hidden_fields_and_missing_values_are_rejected(self):
        base = context()
        for changes in ({'source_kind': 'evaluator_only'}, {'state': 'committed'},
                        {'raw_state': {'private': 'secret'}}, {'values': {'hidden_answer': 'secret'}}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError): responses.render_fragment(self.library, 'proposal.ready', {**base, **changes})
        with self.assertRaises(ValueError):
            responses.render_fragment(self.library, 'receipt.exact', context('committed_receipt', 'committed'))

    def test_quantities_reject_boolean_negative_and_invented_string_values(self):
        for quantity in (True, -1, 'twelve', 2.5):
            with self.subTest(quantity=quantity):
                facts = context('actor_view', 'inventory_known', {'material': 'grain', 'quantity': quantity, 'unit': 'portions'})
                with self.assertRaisesRegex(ValueError, 'quantity'):
                    responses.render_fragment(self.library, 'inventory.item', facts)
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            responses.render_fragment(self.library, 'work.progress', context('actor_view', 'progress_known',
                {'worked_seconds': 3601, 'required_seconds': 3600}))

    def test_conflicting_states_or_shared_fact_values_are_rejected(self):
        active = part('work.active', context('actor_view', 'active', {'worker': 'Ari', 'project_label': 'shelter'}))
        complete = part('work.complete', context('actor_view', 'complete', {'project_label': 'shelter'}))
        with self.assertRaisesRegex(ValueError, 'Conflicting response states'):
            responses.compose(self.library, [active, complete])
        item = part('inventory.item', context('actor_view', 'inventory_known', {'material': 'grain', 'quantity': 12, 'unit': 'portions'}))
        available = part('inventory.available', context('actor_view', 'inventory_known', {'material': 'timber', 'available': 6, 'unit': 'bundles'}))
        with self.assertRaisesRegex(ValueError, 'Conflicting response facts'):
            responses.compose(self.library, [item, available])

    def test_player_drafts_remain_separate_and_do_not_combine_decisions(self):
        walk = part('player.walk_clearing', context('player_request', 'walk_clearing'))
        build = part('player.build', context('player_request', 'build', ref='other-intent'))
        system = part('proposal.ready', context())
        self.assertTrue(responses.compose(self.library, [walk]).startswith('I would like to'))
        with self.assertRaisesRegex(ValueError, 'player intentions'):
            responses.compose(self.library, [system, walk])
        with self.assertRaisesRegex(ValueError, 'combined into decisions'):
            responses.compose(self.library, [walk, build])

    def test_reordering_duplicate_facts_and_unknown_variants_fail(self):
        lead = part('proposal.ready', context())
        prompt = part('proposal.review', context())
        with self.assertRaisesRegex(ValueError, 'ordering'): responses.compose(self.library, [prompt, lead])
        with self.assertRaisesRegex(ValueError, 'Duplicate response fact'): responses.compose(self.library, [lead, lead])
        for variant in (-1, True, 4):
            with self.assertRaisesRegex(ValueError, 'variant'):
                responses.render_fragment(self.library, 'proposal.ready', context(), variant=variant)

    def test_dynamic_expressions_format_specs_and_undeclared_fields_fail_intake(self):
        original = copy.deepcopy(self.library)
        for template in ('{receipt_text.__class__}', '{receipt_text[private]}', '{receipt_text!r}',
                         '{receipt_text:>20}', '{hidden_answer}'):
            with self.subTest(template=template):
                self.library = copy.deepcopy(original)
                self.family('receipt.exact')['variants'] = [template]
                with self.assertRaises(ValueError): responses.validate_library(self.library)

    def test_duplicate_identity_changed_rights_and_effect_or_provider_claims_fail_intake(self):
        original = copy.deepcopy(self.library)
        mutations = [('rights', {}), ('authority', {**original['authority'], 'provider_dispatch': True}),
                     ('authority', {**original['authority'], 'campaign_effects': True}),
                     ('provider_model', 'forged-model')]
        for field, value in mutations:
            with self.subTest(field=field):
                with self.assertRaises(ValueError): responses.validate_library({**original, field: value})
        self.library['families'][1]['id'] = self.library['families'][0]['id']
        with self.assertRaisesRegex(ValueError, 'duplicate response family'): responses.validate_library(self.library)

    def test_uncovered_messages_return_to_host_without_automatic_dispatch_or_guessing(self):
        for identity in ('combat.win', 'npc.promise', 'hidden.truth'):
            with self.assertRaisesRegex(ValueError, 'Unknown response family'):
                responses.render_fragment(self.library, identity, context())
        with self.assertRaisesRegex(ValueError, 'Unknown response recipe'):
            responses.compose_recipe(self.library, 'invent-result', {})

    def test_source_text_is_plain_text_and_slot_contents_are_never_evaluated_again(self):
        original = '<b>not completed</b> {hidden.__class__}'
        self.assertEqual(responses.render_fragment(self.library, 'receipt.exact',
            context('committed_receipt', 'committed', {'receipt_text': original})), original)


if __name__ == '__main__':
    unittest.main()
