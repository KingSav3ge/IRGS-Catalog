"""Same Catalog depot recipe over real non-Rise and Rise App/Core handlers."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import response_depot_compatibility as compatibility
import scripted_responses as responses
import solo_evaluation as evaluation

ENGINE = os.environ.get('IRGS_SHARED_ENGINE_SOURCE')
APP = os.environ.get('IRGS_SHARED_APP_SOURCE')


@unittest.skipUnless(ENGINE and APP, 'Exact shared-response Engine/App snapshots required')
class SharedResponseConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = compatibility.load_fixture()
        consumers = cls.contract['consumers']
        for source, expected in [(ENGINE, consumers['engine_commit']), (APP, consumers['app_commit'])]:
            if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != expected:
                raise RuntimeError('Unselected shared-response consumer commit')
            if subprocess.check_output(['git', '-C', source, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Shared-response dependencies must be clean')
        for component, expected in [('Engine', consumers['engine_commit']), ('Catalog', consumers['app_catalog_pin'])]:
            if subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + component], text=True).strip() != expected:
                raise RuntimeError('Unexpected committed App dependency pin')
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        import server
        import rise_campaigns
        import gameplay_views
        import starting_selection
        import settlement_setup
        import historical_campaigns
        import core_world
        import offline_responses
        import scene_actions
        import solo_provider
        for module, root in [(server, app), (rise_campaigns, app), (gameplay_views, app),
                             (starting_selection, engine), (settlement_setup, engine),
                             (historical_campaigns, engine), (core_world, engine),
                             (offline_responses, engine), (scene_actions, engine), (solo_provider, engine)]:
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Consumer module is from another checkout; use a fresh process')
            setattr(cls, module.__name__, module)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-shared-response-')
        self.addCleanup(self.temp.cleanup)
        self.store = self.server.Store(self.temp.name)
        self.library = responses.load_library()
        self.oracle = compatibility.load_evaluator_data()
        self.inputs = {name: compatibility.export_actor_input(name) for name in ('rise', 'quay')}
        choices = evaluation.load_evaluator_data()['setup']['choices']
        review = self.settlement_setup.preview(choices)
        rise = self.rise_campaigns.create(self.store, {'name': 'Synthetic shared Rise qualification',
            'choices': choices, 'review_digest': review['review_digest'], 'request_id': 'shared-rise-create'})
        selection = copy.deepcopy(self.contract['contexts']['quay']['selection'])
        opening = selection.pop('opening_id')
        entry = self.historical_campaigns.historical_entry(selection['entry_id'])
        selection['snapshot_sha256'] = entry['snapshot_sha256']
        options = self.starting_selection.starting_options(**selection)
        self.assertTrue(any(row['id'] == opening for row in options['playable_openings']))
        quay = self.store.create('Synthetic shared quay qualification', **selection,
            selection_digest=options['selection_digest'], request_id='shared-quay-create', creator=False,
            character={'kind': 'new', 'name': 'Synthetic shared courier', 'species': 'human',
                       'background': '', 'opening_id': opening})
        self.keys = {'rise': rise['id'], 'quay': quay['id']}
        self.assertNotEqual(self.keys['rise'], self.keys['quay'])
        for key in self.keys.values():
            record = self.store.read(key)
            record['state'].setdefault('site_conditions', {})['evaluator_only'] = {'marker': self.oracle['hidden_marker']}
            self.store.write(record)

    @contextmanager
    def no_inference(self):
        with ExitStack() as stack:
            calls = [stack.enter_context(patch(target, side_effect=AssertionError('Routine qualification must stay offline')))
                     for target in ('solo_provider.CapabilityBroker.dispatch',
                                    'openai_proposals.OpenAIProposalTransport.__call__', 'socket.socket.connect')]
            yield
            for call in calls:
                call.assert_not_called()

    def view(self, context):
        return self.gameplay_views.playthrough(self.store.read(self.keys[context]))

    def body(self, context, case):
        view = self.view(context)
        body = {'id': self.keys[context], 'actor': view['actor_id'], 'revision': view['revision'],
                'request_id': case['request_id']}
        if context == 'rise':
            return {**body, 'action': case['action_id']}
        choice = next(row for row in view['supported_actions'] if row.get('action_id') == case['action_id'])
        return {**body, 'kind': 'scene_action', 'action_id': case['action_id'], 'text': choice['text']}

    def submit(self, context, body, store=None):
        store = self.store if store is None else store
        return self.rise_campaigns.action(store, body) if context == 'rise' else store.supported_action(body)

    def act(self, context, index=0):
        case = self.inputs[context]['cases'][index]
        body = self.body(context, case)
        result = self.submit(context, body)
        expected = self.oracle['cases'][case['case_id']]
        self.assertEqual(result['status'], expected['status'])
        duration = result['elapsed_time']['seconds' if context == 'rise' else 'duration_seconds']
        self.assertEqual(duration, expected['duration_seconds'])
        self.assertEqual(self.store.read(self.keys[context])['state']['elapsed_time']['seconds'], expected['total_seconds'])
        return result, body

    def packets(self, result):
        text = '\n'.join([result['outcome']['summary'], *result['outcome'].get('observations', [])])
        scope = {'actor_id': result['actor'],
                 'snapshot_id': result['campaign_id'] + ':' + result['request_id'] + ':' + str(result['revision']),
                 'source_ref': result['receipt']['event_id'], 'source_kind': 'committed_receipt', 'state': 'committed'}
        duration = result['elapsed_time'].get('duration_seconds', result['elapsed_time'].get('seconds'))
        return {'receipt.exact': {**scope, 'values': {'receipt_text': text}},
                'elapsed.action': {**scope, 'values': {'elapsed_seconds': duration}}}

    def render(self, result, variant=0):
        before = {key: self.store.path(key).read_bytes() for key in self.keys.values()}
        output = responses.compose_recipe(self.library, 'routine.result', self.packets(result),
                                         variants={'elapsed.action': variant})
        self.assertEqual(before, {key: self.store.path(key).read_bytes() for key in self.keys.values()})
        self.assertNotIn(self.oracle['hidden_marker'], output)
        return output

    def test_same_receipt_contract_over_nine_real_actions_in_two_initialized_contexts(self):
        with self.no_inference():
            for context in self.keys:
                initial_calendar = copy.deepcopy(self.store.read(self.keys[context])['state']['campaign_time'])
                for index, case in enumerate(self.inputs[context]['cases']):
                    result, _ = self.act(context, index)
                    exact = self.packets(result)['receipt.exact']['values']['receipt_text']
                    for variant in range(8):
                        self.assertTrue(self.render(result, variant).startswith(exact + ' '))
                    event = next(e for e in self.store.read(self.keys[context])['state']['journal']
                                 if e['id'] == result['receipt']['event_id'])
                    self.assertEqual(event['op'], self.contract['contexts'][context]['operation'])
                self.assertEqual(self.store.read(self.keys[context])['state']['campaign_time'], initial_calendar)
            quay = self.store.read(self.keys['quay'])['state']
            actor = self.view('quay')['actor_id']
            self.assertEqual(quay['stocks'][actor]['sealed_dispatch'], self.oracle['quay_final']['dispatch_with_actor'])
            self.assertEqual(quay['stocks']['clerk-tray']['sealed_dispatch'], self.oracle['quay_final']['dispatch_in_tray'])
            self.assertEqual(sum(s.get('sealed_dispatch', 0) for s in quay['stocks'].values()), 1)

    def test_failed_attempt_and_empty_delivery_keep_actual_negation_and_no_extra_transfer(self):
        with self.no_inference():
            results = [self.act('quay', i)[0] for i in range(7)]
            for index, phrase in [(1, 'gate is closed'), (6, 'No dispatch was handed over.')]:
                self.assertEqual(results[index]['status'], 'completed_unsuccessfully')
                self.assertIn(phrase, self.render(results[index]))
            self.assertEqual(self.store.read(self.keys['quay'])['state']['stocks']['clerk-tray']['sealed_dispatch'], 1)

    def test_lost_ack_restart_and_concurrent_retries_recover_one_result_for_both_contexts(self):
        with self.no_inference():
            for context in self.keys:
                original, body = self.act(context)
                original_text = self.render(original)
                before = self.store.path(self.keys[context]).read_bytes()
                restarted = self.server.Store(self.temp.name)
                with ThreadPoolExecutor(max_workers=2) as pool:
                    recovered = list(pool.map(lambda _: self.submit(context, body, restarted), range(2)))
                self.assertEqual(recovered, [original, original])
                lookup = restarted.action_result(self.keys[context], body['request_id'], body['actor'])
                self.assertEqual(lookup, original)
                self.assertEqual(self.render(lookup), original_text)
                self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)

    def test_stale_new_requests_and_foreign_actors_leave_both_saves_unchanged(self):
        with self.no_inference():
            for context in self.keys:
                _, body = self.act(context)
                before = self.store.path(self.keys[context]).read_bytes()
                for changes in ({'request_id': 'stale-new'}, {'request_id': 'foreign-new', 'actor': 'uncontrolled'}):
                    with self.assertRaises((ValueError, PermissionError)):
                        self.submit(context, {**body, **changes})
                self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)

    def test_old_receipts_remain_stable_after_new_actions_and_scope_mixtures_fail(self):
        with self.no_inference():
            first = {}
            for context in self.keys:
                first[context] = self.act(context)[0]
                text = self.render(first[context])
                self.act(context, 1)
                self.assertEqual(self.render(first[context]), text)
            left, right = (self.packets(first[k]) for k in ('rise', 'quay'))
            with self.assertRaisesRegex(ValueError, 'actors or snapshots'):
                responses.compose(self.library, [
                    {'family_id': 'receipt.exact', 'variant': 0, 'context': left['receipt.exact']},
                    {'family_id': 'elapsed.action', 'variant': 0, 'context': right['elapsed.action']}])

    def test_catalog_drafts_and_engine_options_are_editable_without_submitting_or_filtering(self):
        with self.no_inference():
            for context, key in self.keys.items():
                before = self.store.path(key).read_bytes()
                view = self.view(context)
                frame = {'actor_id': view['actor_id'], 'snapshot_id': key + ':draft-0',
                         'source_ref': 'explicit-selected-draft', 'source_kind': 'player_request',
                         'state': 'draft', 'values': {}}
                for variant in range(8):
                    self.assertTrue(responses.render_fragment(self.library, 'player.look_around', frame, variant=variant))
                world = self.core_world.CoreWorld(state=self.store.read(key)['state'])
                drafts = self.offline_responses.player_drafts(world, view['actor_id'])['drafts']
                self.assertTrue(drafts)
                self.assertTrue(all(d['editable'] and d['requires_explicit_submission']
                                    and not d['automatic_execution'] for d in drafts))
                if context == 'quay':
                    self.assertEqual({d['action_id'] for d in drafts},
                                     {d['action_id'] for d in view['supported_actions']})
                    self.assertIn('quay-shortcut', {d['action_id'] for d in drafts})
                self.assertEqual(self.store.path(key).read_bytes(), before)

    def test_unbound_draft_submission_stays_a_declaration_without_physical_effects(self):
        with self.no_inference():
            for context, key in self.keys.items():
                view = self.view(context)
                frame = {'actor_id': view['actor_id'], 'snapshot_id': key + ':draft-0',
                         'source_ref': 'explicit-selected-draft', 'source_kind': 'player_request',
                         'state': 'draft', 'values': {}}
                text = responses.render_fragment(self.library, 'player.look_around', frame)
                before = self.store.read(key)['state']
                result = self.store.gameplay_request({'id': key, 'actor': view['actor_id'], 'revision': 0,
                    'request_id': 'explicit-draft-declaration', 'declaration': text})
                self.assertEqual(result['status'], 'declared_not_resolved')
                self.assertEqual(result['declaration'], text)
                after = self.store.read(key)['state']
                for field in ('stocks', 'opening_stock', 'campaign_time', 'elapsed_time', 'actors'):
                    self.assertEqual(before[field], after[field])

    def test_missing_engine_text_uses_authorized_literal_receipt_without_paid_fallback(self):
        with self.no_inference():
            for context, key in self.keys.items():
                result, _ = self.act(context)
                world = self.core_world.CoreWorld(state=self.store.read(key)['state'])
                before = world.save()
                with patch.object(self.offline_responses, '_library', side_effect=OSError('synthetic missing library')):
                    rendered = self.offline_responses.render_receipt(world, result['actor'], result['receipt']['event_id'])
                self.assertEqual(rendered['mode'], 'literal_receipt')
                self.assertIn(result['outcome']['summary'], rendered['text'])
                self.assertEqual(rendered['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
                self.assertEqual(world.save(), before)


if __name__ == '__main__':
    unittest.main()
