"""Qualify synthetic content against exact, unedited Engine/App source snapshots.

Set IRGS_SOLO_ENGINE_SOURCE and IRGS_SOLO_APP_SOURCE to repository roots. All
state is Engine-initialized and temporary; no user save or provider is opened.
"""
import copy
from concurrent.futures import ThreadPoolExecutor
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
import solo_evaluation as evaluation

ENGINE_SOURCE = os.environ.get('IRGS_SOLO_ENGINE_SOURCE')
APP_SOURCE = os.environ.get('IRGS_SOLO_APP_SOURCE')


@unittest.skipUnless(ENGINE_SOURCE and APP_SOURCE, 'Exact Engine/App source snapshots required')
class SoloConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = evaluation.load_manifest()
        for kind, root in [('engine', ENGINE_SOURCE), ('app', APP_SOURCE)]:
            head = subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip()
            if head != cls.manifest['contracts'][kind + '_commit']:
                raise RuntimeError('Consumer source does not match fixture dependency: ' + kind)
            if subprocess.check_output(['git', '-C', root, 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
                raise RuntimeError('Consumer qualification requires unedited dependency sources')
        engine = Path(ENGINE_SOURCE).resolve() / 'IRGS_3_3'
        app = Path(APP_SOURCE).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'] = str(engine)
        os.environ['IRGS_CATALOG_ROOT'] = str(CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        import core_world
        import irgs_reference
        import settlement_runtime
        import settlement_setup
        import rise_campaigns
        import server
        for module in (core_world, settlement_runtime, settlement_setup, irgs_reference):
            if not Path(module.__file__).resolve().is_relative_to(engine):
                raise RuntimeError('A different Engine is already imported; run consumers in a fresh process')
        for module in (rise_campaigns, server):
            if not Path(module.__file__).resolve().is_relative_to(app):
                raise RuntimeError('A different App is already imported; run consumers in a fresh process')
        cls.engine, cls.setup, cls.app = settlement_runtime, settlement_setup, rise_campaigns
        cls.Store, cls.InvalidEvent = server.Store, irgs_reference.InvalidEvent

    def setUp(self):
        self.evaluator = evaluation.load_evaluator_data()
        self.cases = self.evaluator['oracle']['cases']
        self.choices = self.evaluator['setup']['choices']
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-synthetic-solo-consumer-')
        self.addCleanup(self.temp.cleanup)

    def world(self):
        review = self.setup.preview(self.choices)
        return self.setup.initialize(self.choices, review['review_digest'], evaluation.FIXTURE_ID)

    def store(self):
        store = self.Store(self.temp.name)
        review = self.setup.preview(self.choices)
        saved = self.app.create(store, {'name': 'Synthetic Solo evaluation',
            'choices': self.choices, 'review_digest': review['review_digest'],
            'request_id': 'solo-eval-create'})
        return store, saved['id']

    def body(self, case, campaign):
        return {'id': campaign, 'revision': case['request_revision'], 'actor': 'founder',
                'request_id': case['request_id'], 'action': case['action_id']}

    def check_state(self, state, expected, revision=None):
        if revision is not None: self.assertEqual(revision, expected['revision'])
        self.assertEqual(state['clock'], expected['clock'])
        self.assertEqual(state['elapsed_time']['seconds'], expected['elapsed_seconds'])
        self.assertEqual(self.engine.location(state, 'founder'), expected['location'])
        self.assertEqual('camp' in state['settlements'], expected['camp_established'])
        self.assertEqual(state['stocks']['founder-home']['timber'], expected['founder_timber'])
        self.assertEqual(state['stocks']['oren-home']['timber'], expected['npc_timber'])
        project = state['projects'].get('shelter', {})
        self.assertEqual(project.get('status', 'absent'), expected['shelter_status'])
        self.assertEqual(project.get('worked', 0), expected['shelter_worked_seconds'])
        # Actual finite accounts plus accepted consumption must equal opening stock.
        for material, quantity in state['opening_stock'].items():
            remaining = sum(account.get(material, 0) for account in state['stocks'].values())
            consumed = sum(flow['quantity'] for flow in state['material_flows'].values()
                           if flow['material'] == material and flow['kind'] == 'consumption')
            self.assertEqual(remaining + consumed, quantity)

    def check_context(self, state, actor_input, revision):
        visible = self.app.view(state, 'founder')
        context = actor_input['context']
        self.assertEqual(context['revision'], revision)
        self.assertEqual(context['location'], visible['location'])
        self.assertEqual(context['elapsed_seconds'], visible['elapsed_seconds'])
        self.assertEqual(context['own_inventory'], {item['material']: item['quantity'] for item in visible['inventory']})
        self.assertEqual(context['reserved_for_work'], {item['material']: item['reserved_for_work'] for item in visible['inventory']})
        self.assertEqual(context['protected_seed_grain'], visible['seed_reserve'])
        self.assertEqual(context['camp_established'], visible['camp'] is not None)
        own = next((p for p in visible['projects'] if p['worker'] == self.choices['founder_name']), None)
        self.assertEqual(context['shelter_worked_seconds'], own['worked_seconds'] if own else 0)
        self.assertEqual(context['accepted_rights'], state['grants']['founding']['rights'])
        serialized = json.dumps(actor_input)
        for hidden in [*self.evaluator['oracle']['hidden_markers'], 'oren-home', 'opening_npc_inventory', 'oren-repair']:
            self.assertNotIn(hidden, serialized)
        self.assertNotIn('oren-home', json.dumps(visible))

    def test_fixture_uses_actual_registered_operations_and_engine_owned_opening(self):
        from core_world import SUPPORTED_OPS
        self.assertIn(evaluation.OPERATION, SUPPORTED_OPS)
        self.assertEqual(list(evaluation.SUPPORTED_ACTIONS), [row[0] for row in self.engine.ACTIONS])
        world = self.world()
        self.assertEqual(world.s['player_actor_ids'], ['founder'])
        self.assertEqual(world.s['stocks']['founder-home'], {'grain': 12, 'timber': 6, 'axe': 1})
        self.assertEqual(world.s['stocks']['oren-home'], self.evaluator['oracle']['hidden_facts']['opening_npc_inventory'])
        self.assertEqual(world.s['grants']['founding']['status'], 'accepted')
        self.check_context(world.s, evaluation.export_actor_input('solo-walk'), 0)

    def test_actual_engine_sequence_atomic_failures_and_conserved_resources(self):
        world = self.world()
        for case in self.cases:
            if case['kind'] not in ('legitimate', 'denied', 'unsupported'): continue
            with self.subTest(case=case['case_id']):
                before = copy.deepcopy(world.s)
                if case['kind'] == 'legitimate':
                    self.engine.execute(world, case['request_id'], 'founder', case['action_id'], case['intent_ref'])
                    event = world.s['journal'][-1]
                    self.assertEqual(event['op'], evaluation.OPERATION)
                    self.assertEqual(event['params']['instruction_ref'], case['intent_ref'])
                else:
                    with self.assertRaises(self.InvalidEvent):
                        self.engine.execute(world, case['request_id'], 'founder', case['action_id'], case['intent_ref'])
                    self.assertEqual(world.s, before)
                self.check_state(world.s, case['expected'])
        final = self.evaluator['oracle']['final_state']
        self.assertEqual(world.s['stocks']['founder-home'], final['founder_inventory'])
        self.assertEqual(world.s['stocks']['oren-home'], final['npc_inventory'])
        self.assertEqual(world.s['assets']['shelter']['places'], final['shelter_places'])
        self.assertEqual({material: sum(flow['quantity'] for flow in world.s['material_flows'].values()
            if flow['material'] == material) for material in final['material_consumption']}, final['material_consumption'])

    def test_engine_rejects_foreign_control_and_recovers_exact_core_event_replay(self):
        world = self.world()
        before = copy.deepcopy(world.s)
        with self.assertRaises(self.InvalidEvent):
            self.engine.execute(world, 'foreign-control', 'oren', 'walk_clearing', evaluation.SOURCE_REF)
        self.assertEqual(world.s, before)
        case = next(c for c in self.cases if c['case_id'] == 'solo-walk')
        self.engine.execute(world, case['request_id'], 'founder', case['action_id'], case['intent_ref'])
        event = copy.deepcopy(world.s['journal'][-1])
        before = copy.deepcopy(world.s)
        self.assertFalse(world.apply(event['id'], event['at'], event['op'], **event['params']))
        self.assertEqual(world.s, before)
        event['params']['action'] = 'wait_hour'
        with self.assertRaises(self.InvalidEvent):
            world.apply(event['id'], event['at'], event['op'], **event['params'])
        self.assertEqual(world.s, before)

    def test_actual_app_sequence_stale_replay_restart_and_hidden_boundary(self):
        store, campaign = self.store()
        results = {}
        for case in self.cases:
            with self.subTest(case=case['case_id']):
                store = self.Store(self.temp.name)  # New host object; saved receipts must survive.
                before = store.path(campaign).read_bytes()
                current = store.read(campaign)
                actor = evaluation.export_actor_input(case['case_id'])
                self.check_context(current['state'], actor, current['revision'])
                original_intent = copy.deepcopy(actor)
                self.assertEqual(store.path(campaign).read_bytes(), before)
                body = self.body(case, campaign)
                if case['kind'] in ('legitimate', 'replay'):
                    result = self.app.action(store, body)
                    if case['kind'] == 'replay':
                        self.assertEqual(result, results[case['replay_of']])
                        self.assertEqual(store.path(campaign).read_bytes(), before)
                    else:
                        results[case['case_id']] = result
                        record = store.read(campaign)
                        receipt = record['state']['settlement_receipts']['founder'][case['request_id']]
                        self.assertEqual(result['narrative'], receipt['text'])
                        self.assertEqual(result['status'], 'completed_successfully')
                        self.assertEqual(self.Store(self.temp.name).action_result(campaign, case['request_id'], 'founder'), result)
                        elapsed = result['elapsed_time']
                        self.assertEqual(elapsed['seconds'], case['expected']['elapsed_seconds'] - current['state']['elapsed_time']['seconds'])
                    for hidden in [*self.evaluator['oracle']['hidden_markers'], 'oren-home', 'dependencies', 'certificate']:
                        self.assertNotIn(hidden, json.dumps(result))
                else:
                    with self.assertRaises((ValueError, self.InvalidEvent)):
                        self.app.action(store, body)
                    self.assertEqual(store.path(campaign).read_bytes(), before)
                self.assertEqual(actor, original_intent)
                record = store.read(campaign)
                self.check_state(record['state'], case['expected'], record['revision'])
        self.assertEqual(len(store.read(campaign)['gameplay_requests']), 5)

    def test_app_concurrent_duplicate_requests_commit_one_effect(self):
        store, campaign = self.store()
        case = next(c for c in self.cases if c['case_id'] == 'solo-walk')
        body = self.body(case, campaign)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.app.action(store, copy.deepcopy(body)), range(2)))
        self.assertEqual(results[0], results[1])
        record = store.read(campaign)
        self.check_state(record['state'], case['expected'], record['revision'])
        self.assertEqual(len(record['gameplay_requests']), 1)

    def test_app_failed_save_does_not_accept_request_or_repeat_effect_on_retry(self):
        store, campaign = self.store()
        case = next(c for c in self.cases if c['case_id'] == 'solo-walk')
        before = store.path(campaign).read_bytes()
        with patch.object(store, 'write', side_effect=OSError('synthetic write failure')):
            with self.assertRaises(OSError): self.app.action(store, self.body(case, campaign))
        self.assertEqual(store.path(campaign).read_bytes(), before)
        self.app.action(store, self.body(case, campaign))
        record = store.read(campaign)
        self.check_state(record['state'], case['expected'], record['revision'])
        self.assertEqual(len(record['gameplay_requests']), 1)


if __name__ == '__main__':
    unittest.main()
