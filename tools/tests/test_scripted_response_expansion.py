"""Campaign-neutral depot counts, typed composition and genre-independent intent."""
import collections
import copy
import hashlib
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import scripted_responses as responses


class ResponseExpansionTests(unittest.TestCase):
    def setUp(self):
        self.library = responses.load_library()
        self.families = {f['id']: f for f in self.library['families']}

    def context(self, family, values=None):
        return {'actor_id': 'synthetic-actor', 'snapshot_id': 'synthetic-snapshot',
            'source_ref': 'fact:' + family['id'], 'source_kind': family['source_kind'],
            'state': family['state'], 'values': values if values is not None else {
                key: 2 if kind == 'integer' else 'Not complete.'
                for key, kind in family['slots'].items()}}

    def test_exact_counts_identity_and_unique_stored_strings(self):
        counts = collections.Counter()
        strings = []
        for family in self.library['families']:
            counts[family['channel']] += len(family['variants'])
            strings.extend(family['variants'])
        self.assertEqual(counts, {'system': 750, 'player_draft': 250})
        self.assertEqual(len(strings), 1000)
        self.assertEqual(len({' '.join(t.casefold().split()) for t in strings}), 1000)
        self.assertEqual(len(self.families), 127)
        self.assertEqual(self.library['library_id'], 'irgs-response-depot-v1')
        self.assertEqual(self.library['schema_version'], 2)
        self.assertEqual(self.library['version'], '1.0.0')

    def test_original_rise_compatibility_pack_remains_byte_identical_and_loadable(self):
        path = Path(responses.__file__).parent / 'responses/routine_v1/library.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         '4f0c629a6c2c11ee79a305fc5910b3f0caa7290f52d141aa3f867ed4facb361a')
        original = responses.load_library(path)
        self.assertEqual(sum(len(f['variants']) for f in original['families']), 325)
        self.assertEqual(original['schema_version'], 1)

    def test_all_1000_variants_render_and_keep_source_text_literal(self):
        for family in self.library['families']:
            context = self.context(family)
            for variant in range(len(family['variants'])):
                with self.subTest(family=family['id'], variant=variant):
                    rendered = responses.render_fragment(self.library, family['id'], context, variant=variant)
                    self.assertTrue(rendered)
                    self.assertNotIn('{', rendered)
                    for key in family['slots']:
                        self.assertIn(str(context['values'][key]), rendered)

    def test_every_recipe_composes_required_and_full_fact_sets(self):
        self.assertEqual(len(self.library['recipes']), 32)
        for recipe in self.library['recipes']:
            for selected in (recipe['required'], recipe['families']):
                with self.subTest(recipe=recipe['id'], selected=selected):
                    contexts = {key: self.context(self.families[key]) for key in selected}
                    rendered = responses.compose_recipe(self.library, recipe['id'], contexts)
                    self.assertTrue(rendered)
                    if 'receipt.exact' in selected:
                        self.assertIn(contexts['receipt.exact']['values']['receipt_text'], rendered)

    def test_all_drafts_use_unbound_semantic_intents_and_explicit_submission(self):
        drafts = [f for f in self.library['families'] if f['channel'] == 'player_draft']
        self.assertEqual(len(drafts), 32)
        self.assertEqual(sum(len(f['variants']) for f in drafts), 250)
        self.assertEqual(len({f['intent_tag'] for f in drafts}), 32)
        for family in drafts:
            self.assertEqual(family['source_kind'], 'player_request')
            self.assertEqual(family['state'], 'draft')
            self.assertRegex(family['intent_tag'], r'^[a-z][a-z0-9_]*$')
        self.assertTrue(all(f['intent_tag'] is None for f in self.library['families']
                            if f['channel'] == 'system'))
        self.assertTrue(self.library['authority']['player_drafts_require_explicit_submission'])

    def test_static_text_has_no_rise_cast_locations_or_resource_assumptions(self):
        forbidden = re.compile(r'\b(rise|elin|oren|rowan|greywater|clearing|commons|timber|grain|shelter|camp)\b', re.I)
        for family in self.library['families']:
            for variant in family['variants']:
                self.assertIsNone(forbidden.search(variant), (family['id'], variant))
        self.assertFalse(any(f['id'].startswith('camp.') for f in self.library['families']))

    def test_same_depot_renders_four_campaign_themes_from_supplied_facts(self):
        themes = [
            ('historical court', 'Chancellor', 'Royal Hall', 'review petition', 'wax', 'seals'),
            ('fantasy expedition', 'Pathfinder', 'Moon Gate', 'read runes', 'mana', 'charges'),
            ('space station', 'Navigator', 'Orbital Dock', 'repair airlock', 'oxygen', 'litres'),
            ('modern investigation', 'Detective', 'City Archive', 'review evidence', 'film', 'rolls')]
        for theme, person, place, task, resource, unit in themes:
            values = {'person_label': person, 'subject_label': task, 'target_label': place,
                'destination_label': place, 'task_label': task, 'resource_label': resource,
                'unit': unit, 'quantity': 7, 'place_label': place,
                'capacity_label': 'available spaces', 'capacity_quantity': 3,
                'shortfall_label': 'unmet spaces', 'shortfall_quantity': 0,
                'occupant_label': 'registered occupants', 'occupant_quantity': 2}
            for family_id in ('player.ask', 'player.observe', 'player.travel',
                              'player.begin_task', 'inventory.item'):
                family = self.families[family_id]
                context = self.context(family, {k: values[k] for k in family['slots']})
                context['snapshot_id'] = theme
                for index in range(len(family['variants'])):
                    output = responses.render_fragment(self.library, family_id, context, variant=index)
                    for value in context['values'].values():
                        self.assertIn(str(value), output)
            contexts = {key: self.context(self.families[key], {
                k: values[k] for k in self.families[key]['slots']})
                for key in ('place.name', 'place.capacity', 'place.occupants', 'place.shortfall')}
            self.assertIn(place, responses.compose_recipe(self.library, 'routine.place', contexts))

    def test_received_records_preserve_negation_newlines_and_placeholder_like_text(self):
        original = 'No offer was accepted. No goods changed hands.\nNot complete. {untrusted.slot}'
        for family in self.library['families']:
            if family['id'] not in ('record.offer', 'record.question', 'record.quote',
                                    'record.observation', 'record.correction', 'record.pending'):
                continue
            context = self.context(family, {'record_text': original})
            for variant in range(len(family['variants'])):
                self.assertIn(original, responses.render_fragment(self.library, family['id'], context, variant=variant))

    def test_schema_rejects_operation_bound_drafts_and_ambiguous_identity(self):
        library = copy.deepcopy(self.library)
        draft = next(f for f in library['families'] if f['channel'] == 'player_draft')
        draft['state'] = 'walk_to_clearing'
        with self.assertRaisesRegex(ValueError, 'semantic intent'):
            responses.validate_library(library)
        library = copy.deepcopy(self.library)
        library['schema_version'] = 1
        with self.assertRaisesRegex(ValueError, 'identity'):
            responses.validate_library(library)

    def test_composition_rejects_mixed_states_actors_snapshots_and_player_decisions(self):
        offer, question = (self.context(self.families[key]) for key in ('record.offer', 'record.question'))
        question['source_ref'] = offer['source_ref']
        parts = [{'family_id': 'record.offer', 'variant': 7, 'context': offer},
                 {'family_id': 'record.question', 'variant': 7, 'context': question}]
        with self.assertRaisesRegex(ValueError, 'Conflicting response states'):
            responses.compose(self.library, parts)
        question['source_ref'] = 'other-fact'
        for key in ('actor_id', 'snapshot_id'):
            question[key] = 'another-scope'
            with self.assertRaisesRegex(ValueError, 'actors or snapshots'):
                responses.compose(self.library, parts)
            question[key] = offer[key]
        player = self.context(self.families['player.wait'])
        parts[1] = {'family_id': 'player.wait', 'variant': 0, 'context': player}
        with self.assertRaisesRegex(ValueError, 'player intentions'):
            responses.compose(self.library, parts)


if __name__ == '__main__':
    unittest.main()
