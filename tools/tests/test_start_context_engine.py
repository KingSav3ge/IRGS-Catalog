"""Independent Catalog checks of the published Engine contract; no App adoption claim."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import replace
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import start_context_evaluation as evaluation

ENGINE = os.environ.get('IRGS_CONTEXT_ENGINE_SOURCE')


class SyntheticCAS:
    """Test-only durable save/result envelope; Core remains the only world owner."""
    def __init__(self, path, world, contracts, core):
        self.path, self.contracts, self.core = path, contracts, core
        self.lock = threading.Lock()
        self.path.write_text(json.dumps({'save': world.save(), 'branch': 'catalog-test',
            'restore': 'restore-1', 'results': {}}))

    def read(self):
        return json.loads(self.path.read_text())

    def scope(self, world=None):
        doc = self.read(); world = world or self.core.CoreWorld.load(doc['save'])
        return self.contracts.WorldScope(world.s['campaign_id'], doc['branch'], doc['restore'], world.checksum())

    def load(self):
        return self.core.CoreWorld.load(self.read()['save'])

    def persist(self, expected, candidate, result):
        with self.lock:
            doc = self.read()
            if self.scope() != expected:
                raise RuntimeError('synthetic_host_compare_failed')
            self.core.CoreWorld.load(candidate)
            doc['save'] = candidate; doc['results'][result['request_id']] = result
            pending = self.path.with_suffix('.pending')
            with pending.open('w') as stream:
                json.dump(doc, stream); stream.flush(); os.fsync(stream.fileno())
            pending.replace(self.path)
            descriptor = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


@unittest.skipUnless(ENGINE, 'Exact published Engine source required')
class StartContextEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = evaluation.load_fixture()
        root = Path(ENGINE).resolve()
        if subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip() != evaluation.ENGINE_COMMIT:
            raise RuntimeError('Unselected start-context Engine revision')
        if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip():
            raise RuntimeError('Start-context Engine source must be clean')
        import hashlib
        for name, sha in cls.manifest['engine_contract']['files_sha256'].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != sha:
                raise RuntimeError('Published Engine contract hash mismatch')
        sys.path.insert(0, str(root / 'IRGS_3_3/runtime'))
        for name in ('core_world', 'campaign_library', 'historical_campaigns', 'starting_selection',
                     'start_readiness', 'shared_runtime', 'runtime_contracts', 'settlement_setup',
                     'solo_provider', 'openai_proposals'):
            module = importlib.import_module(name)
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Imported another Engine; use a fresh process')
            setattr(cls, name, module)
        cls.observations = {}

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('IRGS_CONTEXT_EVIDENCE_OUTPUT'):
            Path(os.environ['IRGS_CONTEXT_EVIDENCE_OUTPUT']).write_text(json.dumps(cls.observations, indent=2) + '\n')

    def setUp(self):
        stack = ExitStack(); self.addCleanup(stack.close)
        self.temp = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='irgs-context-engine-')))
        self.guards = [stack.enter_context(patch(name, side_effect=AssertionError('No provider/network in Engine checks')))
            for name in ('solo_provider.CapabilityBroker.dispatch',
                         'openai_proposals.OpenAIProposalTransport.__call__', 'socket.socket.connect')]
        self.oracle = evaluation.load_evaluator_data()

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def raw(self, entry='hyw-1415'):
        preview = self.historical_campaigns.historical_entry(entry)
        return self.campaign_library.initial_campaign('military', 'catalog-synthetic-' + entry,
            scenario_id='hundred-years-war', entry_id=entry, snapshot_sha256=preview['snapshot_sha256'])

    def create(self, case='henry-1415-observation'):
        self.actor_input = evaluation.export_actor_input(case)
        selection = self.actor_input['selection']
        if case == 'rise-r00':
            choices = json.loads((CATALOG / 'evaluation/solo_r00_v1/evaluator_only/setup.json').read_text())['choices']
            review = self.settlement_setup.preview(choices)
            self.world = self.settlement_setup.initialize(choices, review['review_digest'], 'catalog-r00-regression')
            self.review = review
        else:
            raw = self.raw(); before = raw.save()
            options = self.starting_selection.options_for_world(raw)
            self.review = self.start_readiness.review_start(raw, selection['character'])
            self.assertEqual(raw.save(), before)
            self.world = self.starting_selection.initialize_player(raw, selection['character'],
                selection_digest=options['selection_digest'], request_ref='explicit-catalog-start-' + case)
        self.actor = self.world.s['player_actor_ids'][0]
        self.host = SyntheticCAS(self.temp / (case + '.json'), self.world, self.runtime_contracts, self.core_world)

    def view(self):
        scope = self.host.scope(self.world)
        before = self.world.save(); disk = self.host.path.read_bytes()
        packet = self.start_readiness.actor_view(self.world, self.actor,
            branch_id=scope.branch_id, restore_id=scope.restore_id)
        self.assertEqual(self.world.save(), before); self.assertEqual(self.host.path.read_bytes(), disk)
        self.assertEqual(packet['schema_version'], evaluation.ENGINE_SCHEMA)
        self.assertEqual(packet['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
        self.assertFalse(packet['templates_reapplied'])
        for forbidden in (self.oracle['hidden_marker'], 'state_digest', 'historical_start', 'dependencies'):
            self.assertNotIn(forbidden, json.dumps(packet))
        return packet

    def request(self, action=None, request_id='context-observation'):
        selected = None
        if action:
            selected = next(cap.capability_id for cap in self.shared_runtime.capabilities(self.world, self.actor)
                if json.loads(cap.action_json).get('action_id') == action)
        scope = self.host.scope(self.world)
        return self.shared_runtime.prepare_intent(self.world, request_id=request_id, actor_id=self.actor,
            intention=self.actor_input['intention'], capability_id=selected,
            branch_id=scope.branch_id, restore_id=scope.restore_id, source_ref=self.actor_input['source_ref'])

    def execute(self, request, **changes):
        args = {'current_scope': self.host.scope(self.world), 'persist': self.host.persist, 'explicitly_accepted': True}
        args.update(changes)
        return self.shared_runtime.execute_intent(self.world, request, **args)

    def test_all_six_selections_distinguish_modes_receipts_and_initial_civil_checkpoint(self):
        for case in evaluation.CASES:
            self.create(case); packet = self.view(); expected = self.oracle['cases'][case]
            self.assertEqual(packet['current_mode'], expected['selected_mode'])
            if expected['historical']:
                self.assertEqual(self.review['selected_mode']['status'], expected['selected_mode'])
                civil = packet['civil_time']
                for key, value in self.oracle['civil_checkpoint'].items():
                    self.assertEqual(civil[key], value)
                self.assertEqual(civil['status'], 'received_initial_checkpoint')
                self.assertIsNone(civil['opening_hour'])
                record = next(row for row in packet['received_context'] if row['record_id'] == 'setup:civil-date')
                self.assertEqual(record['status'], 'established')
                self.assertEqual(civil['source_ref'], self.world.s['evidence']['setup:civil-date']['source_ref'])
                self.assertEqual(self.world.s['campaign_time']['day'], 0)
                if not self.actor_input['actions']:
                    self.assertEqual({r['record_id'] for r in packet['received_context']}, {'setup:civil-date'})
            else:
                self.assertIsNone(packet['civil_time'])
            self.observations[case] = {'mode': packet['current_mode'], 'civil_time': packet['civil_time'],
                'received_record_ids': [r['record_id'] for r in packet['received_context']],
                'app_acceptance': 'not_executed_pending_adoption'}

    def test_henry_observation_is_accepted_core_result_without_stock_authority_or_civil_advance(self):
        self.create(); before = copy.deepcopy(self.world.s)
        request = self.request('observe-embarkation'); result = self.execute(request)
        self.assertEqual(result['status'], 'completed_successfully')
        self.assertEqual(result['intention'], self.actor_input['intention'])
        self.assertEqual(result['receipt']['operation_id'], 'execute_player_scene_action')
        self.assertEqual(result['receipt']['elapsed_seconds'], 20)
        self.assertTrue(result['presentation']['text'].startswith(result['receipt']['exact_text']))
        self.assertEqual(self.world.s['elapsed_time']['axis'], 'selected-historical-observation-seconds')
        self.assertEqual(self.world.s['elapsed_time']['seconds'], 20)
        self.assertEqual(self.world.s['campaign_time'], before['campaign_time'])
        self.assertEqual(self.world.s['stocks'], {})
        self.assertEqual(self.world.s['orders'], {})
        self.assertFalse(self.world.s['starting_control']['institutional_mandate_granted'])
        self.assertNotIn('authored_opening', self.world.s['gameplay_started'])
        self.assertEqual(set(self.world.s['actors'][self.actor]['current']), {'location'})
        self.assertEqual(len(self.world.s['knowledge'][self.actor]), len(before['knowledge'][self.actor]) + 1)
        self.assertEqual(self.host.load().save(), self.world.save())
        self.observations['henry_operation'] = {'status': result['status'], 'elapsed_seconds': 20,
            'operation_id': result['receipt']['operation_id'], 'stocks_created': False,
            'civil_calendar_advanced': False, 'received_result': True}

    def test_all_supported_arcs_and_original_results_survive_reload_and_later_actions(self):
        for case in ('henry-1415-observation', 'new-1415-quay', 'rise-r00'):
            self.create(case); calendar = copy.deepcopy(self.world.s['campaign_time']); saved = []
            for index, action in enumerate(self.actor_input['actions']):
                request = self.request(action, 'context-' + str(index))
                saved.append((request.to_json(), self.execute(request)))
            self.assertEqual(self.world.s['elapsed_time']['seconds'], self.oracle['cases'][case]['full_elapsed_seconds'])
            self.assertEqual(self.world.s['campaign_time'], calendar)
            if case == 'new-1415-quay':
                self.assertEqual(self.world.s['stocks'][self.actor]['sealed_dispatch'], 0)
                self.assertEqual(self.world.s['stocks']['clerk-tray']['sealed_dispatch'], 1)
                self.assertEqual(sum(s['sealed_dispatch'] for s in self.world.s['stocks'].values()), 1)
                self.assertEqual(saved[1][1]['status'], 'completed_unsuccessfully')
            elif case == 'rise-r00':
                self.assertEqual(self.world.s['projects']['shelter']['worked'], 3600)
                self.assertEqual(self.world.s['stocks']['founder-home']['timber'], 3)
            self.world = self.host.load(); before = self.host.path.read_bytes()
            for raw, result in saved:
                request = self.runtime_contracts.AcceptedIntent.from_json(raw)
                self.assertEqual(self.execute(request), result)
                self.assertEqual(self.host.read()['results'][request.request_id], result)
            self.assertEqual(self.host.path.read_bytes(), before)

    def test_default_henry_john_and_new_player_retain_only_unresolved_intent_without_effects(self):
        for case in ('henry-1415-default', 'john-1415-limited', 'new-1415-default'):
            self.create(case); before = copy.deepcopy(self.world.s)
            request = self.request(); result = self.execute(request)
            self.assertEqual(result['status'], 'declared_not_resolved')
            self.assertIsNone(result['receipt']['elapsed_seconds'])
            for field in ('stocks', 'actors', 'knowledge', 'campaign_time', 'elapsed_time'):
                self.assertEqual(self.world.s.get(field), before.get(field))
            if case == 'john-1415-limited':
                self.assertEqual(self.review['playable_context']['status'], 'held')
            self.world = self.host.load(); self.assertEqual(self.execute(request), result)

    def test_no_implicit_opening_and_wrong_actor_snapshot_or_fictional_substitution_is_rejected(self):
        for actor, opening in (('HYW-JOHN-BEDFORD', 'henry-1415-embarkation-v1'),
            ('HYW-HENRY-V', 'quay-delivery-v1'), ('missing', 'henry-1415-embarkation-v1')):
            raw = self.raw(); before = raw.save(); options = self.starting_selection.options_for_world(raw)
            with self.assertRaises(ValueError):
                self.starting_selection.initialize_player(raw, {'kind': 'existing', 'actor_id': actor, 'opening_id': opening},
                    selection_digest=options['selection_digest'])
            self.assertEqual(raw.save(), before)
        raw = self.raw('hyw-1417'); options = self.starting_selection.options_for_world(raw)
        self.assertEqual(options['existing_character_openings'], [])
        with self.assertRaises(ValueError):
            self.starting_selection.initialize_player(raw, {'kind': 'existing', 'actor_id': 'HYW-HENRY-V',
                'opening_id': 'henry-1415-embarkation-v1'}, selection_digest=options['selection_digest'])
        self.create('henry-1415-default'); self.assertNotIn('scene_rules', self.world.s)

    def test_private_state_does_not_choose_review_or_actor_menu_and_control_is_enforced(self):
        raw = self.raw(); character = evaluation.export_actor_input('henry-1415-observation')['selection']['character']
        before = self.start_readiness.review_start(raw, character)
        raw.s['private_fixture'] = {'stock': 999, 'location': self.oracle['hidden_marker']}
        self.assertEqual(self.start_readiness.review_start(raw, character), before)
        self.create(); menu = self.view()['supported_capabilities']
        self.world.s['private_fixture'] = raw.s['private_fixture']
        self.assertEqual(self.view()['supported_capabilities'], menu)
        self.world.s['entity_registry']['eligibility']['individual:' + self.actor]['versions'][-1]['eligible'] = False
        with self.assertRaises(ValueError):
            self.view()

    def test_initial_civil_day_requires_actual_receipt_and_reads_never_reseed_continuing_state(self):
        self.create(); original = self.view()['civil_time']
        self.world.s['historical_start']['opening']['date'] = '1415-08-12'
        self.assertEqual(self.view()['civil_time'], original)
        self.world.s['knowledge'][self.actor].pop('setup:civil-date')
        self.world.s['gameplay_started'].pop('start_readiness')
        before = self.world.save()
        with patch.object(self.start_readiness, 'initialize_context', side_effect=AssertionError('No reseeding')), \
             patch.object(self.historical_campaigns, 'historical_entry', side_effect=AssertionError('No template read')):
            packet = self.view()
        self.assertIsNone(packet['civil_time']); self.assertIsNone(packet['selected_start'])
        self.assertEqual(self.world.save(), before)

    def test_false_acceptance_failed_save_and_changed_or_stale_requests_commit_nothing(self):
        self.create(); request = self.request('observe-embarkation'); stale = self.request('observe-embarkation', 'stale')
        before = self.world.save(); disk = self.host.path.read_bytes()
        for value in (False, 1, 'true', None):
            with self.assertRaises(self.shared_runtime.SharedActionUnavailable):
                self.execute(request, explicitly_accepted=value)
        with self.assertRaises(OSError):
            self.execute(request, persist=lambda *args: (_ for _ in ()).throw(OSError('synthetic save failure')))
        self.assertEqual(self.world.save(), before); self.assertEqual(self.host.path.read_bytes(), disk)
        result = self.execute(request); before = self.world.save()
        with self.assertRaises(self.shared_runtime.SharedActionUnavailable):
            self.execute(replace(request, intention='Changed outcome request'))
        with self.assertRaises(self.shared_runtime.SharedActionUnavailable):
            self.execute(stale)
        self.assertEqual(self.world.save(), before); self.assertEqual(self.execute(request), result)

    def test_concurrent_request_has_one_commit_and_original_result_recovers_without_repeat(self):
        self.create(); request = self.request('observe-embarkation'); save = self.world.save(); scope = self.host.scope()
        def submit(_):
            try:
                return self.shared_runtime.execute_intent(self.core_world.CoreWorld.load(save), request,
                    current_scope=scope, persist=self.host.persist, explicitly_accepted=True)
            except RuntimeError as error:
                return str(error)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(submit, range(2)))
        accepted = [r for r in results if isinstance(r, dict)]
        self.assertEqual(len(accepted), 1)
        self.world = self.host.load()
        self.assertEqual(self.world.s['elapsed_time']['seconds'], 20)
        self.assertEqual(self.execute(request), accepted[0])

    def test_restore_identity_fences_discarded_request_without_resetting_retained_state(self):
        self.create(); request = self.request('observe-embarkation'); save = self.world.save(); self.execute(request)
        doc = self.host.read(); doc.update(save=save, restore='restore-2', results={})
        self.host.path.write_text(json.dumps(doc)); self.world = self.host.load()
        with self.assertRaises(self.shared_runtime.SharedActionUnavailable):
            self.execute(request)
        self.assertEqual(self.world.save(), save)


if __name__ == '__main__':
    unittest.main()
