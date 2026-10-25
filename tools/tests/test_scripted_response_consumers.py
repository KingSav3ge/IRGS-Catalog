"""Compose from actual selected App projections/receipts with no inference call."""
from contextlib import contextmanager
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
import scripted_responses as responses
import solo_evaluation as evaluation
import solo_proposal_compatibility as compatibility

ENGINE, APP = os.environ.get('IRGS_SCRIPT_ENGINE_SOURCE'), os.environ.get('IRGS_SCRIPT_APP_SOURCE')


@unittest.skipUnless(ENGINE and APP, 'Exact scripted-response Engine/App snapshots required')
class ScriptedConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract = compatibility.load_contract()['consumers']
        for source, commits in [(ENGINE, [contract['engine_commit']]),
                                (APP, contract['app_commits'].values())]:
            commit = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip()
            if commit not in commits:
                raise RuntimeError('Unselected response consumer source')
            if subprocess.check_output(['git', '-C', source, 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
                raise RuntimeError('Response consumer source must be unedited')
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        import server
        import rise_campaigns
        import assistance
        import settlement_setup
        import settlement_runtime
        import solo_provider
        for module, root in [(server, app), (rise_campaigns, app), (assistance, app),
                             (settlement_setup, engine), (settlement_runtime, engine), (solo_provider, engine)]:
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Response consumer imported a different dependency; use a fresh process')
        cls.server, cls.rise, cls.assistance = server, rise_campaigns, assistance
        cls.setup, cls.runtime, cls.provider = settlement_setup, settlement_runtime, solo_provider

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-scripted-response-consumer-')
        self.addCleanup(self.temp.cleanup)
        self.store = self.server.Store(self.temp.name)
        self.library = responses.load_library(CATALOG / 'responses/routine_v1/library.json')
        self.evaluator = evaluation.load_evaluator_data()
        choices = self.evaluator['setup']['choices']
        review = self.setup.preview(choices)
        self.key = self.rise.create(self.store, {'name': 'Synthetic response qualification',
            'choices': choices, 'review_digest': review['review_digest'], 'request_id': 'scripted-create'})['id']

    def context(self, source, state, values=None, ref='host:turn'):
        record = self.store.read(self.key)
        return {'actor_id': 'founder', 'snapshot_id': self.key + ':' + str(record['revision']),
                'source_ref': ref, 'source_kind': source, 'state': state,
                'values': {} if values is None else values}

    @contextmanager
    def no_dispatch_or_mutation(self):
        before = self.store.path(self.key).read_bytes()
        with patch.object(self.provider.CapabilityBroker, 'dispatch', side_effect=AssertionError('Routine text must not dispatch')) as dispatch:
            yield
            dispatch.assert_not_called()
        self.assertEqual(self.store.path(self.key).read_bytes(), before)

    def act(self, case):
        return self.rise.action(self.store, {'id': self.key, 'revision': case['request_revision'],
            'actor': 'founder', 'request_id': case['request_id'], 'action': case['action_id']})

    def establish_active_work(self):
        for case in self.evaluator['oracle']['cases']:
            if case['case_id'] in ('solo-walk', 'solo-found', 'solo-build'):
                self.act(case)

    def test_five_actual_committed_results_preserve_receipt_and_elapsed_with_zero_dispatch(self):
        for index, case in enumerate(c for c in self.evaluator['oracle']['cases'] if c['kind'] == 'legitimate'):
            result = self.act(case)
            state = self.store.read(self.key)['state']
            original = state['settlement_receipts']['founder'][case['request_id']]['text']
            self.assertEqual(original, result['outcome']['summary'])
            bindings = {'receipt.exact': self.context('committed_receipt', 'committed', {'receipt_text': original}, result['receipt']['event_id']),
                        'elapsed.action': self.context('committed_receipt', 'committed', {'elapsed_seconds': result['elapsed_time']['seconds']}, result['receipt']['event_id']),
                        'turn.next': self.context('host_status', 'waiting_for_player')}
            with self.no_dispatch_or_mutation():
                output = responses.compose_recipe(self.library, 'routine.result', bindings,
                    variants={'elapsed.action': index % 4, 'turn.next': index % 4})
            self.assertTrue(output.startswith(original + ' '))
            self.assertIn(str(result['elapsed_time']['seconds']), output)
            self.assertNotIn('oren-home', output)
            for marker in self.evaluator['oracle']['hidden_markers']: self.assertNotIn(marker, output)
        self.assertEqual(self.store.read(self.key)['state']['elapsed_time']['seconds'], 3900)

    def test_real_inventory_projection_composes_only_visible_quantities_units_and_reservations(self):
        self.establish_active_work()
        view = self.rise.view(self.store.read(self.key)['state'], 'founder')
        for item in view['inventory']:
            material, unit = item['material'], item['unit']
            ref = 'view:inventory:' + material
            bindings = {
                'inventory.item': self.context('actor_view', 'inventory_known', {'material': material, 'quantity': item['quantity'], 'unit': unit}, ref),
                'inventory.available': self.context('actor_view', 'inventory_known', {'material': material, 'available': item['available'], 'unit': unit}, ref),
                'inventory.reserved': self.context('actor_view', 'inventory_known', {'material': material, 'reserved': item['reserved_for_work'], 'unit': unit}, ref)}
            if material == 'grain':
                bindings['inventory.seed'] = self.context('actor_view', 'inventory_known', {'seed': item['protected_seed']}, ref)
            with self.no_dispatch_or_mutation():
                for variant in range(4):
                    output = responses.compose_recipe(self.library, 'routine.inventory', bindings,
                        variants={family: variant for family in bindings})
                    self.assertIn(material, output)
                    self.assertNotIn('oren-home', output)

    def test_real_project_and_camp_views_compose_status_and_progress_without_hidden_world_reads(self):
        self.establish_active_work()
        view = self.rise.view(self.store.read(self.key)['state'], 'founder')
        project = next(p for p in view['projects'] if p['worker'] == 'Ari')
        camp = view['camp']
        with self.no_dispatch_or_mutation():
            work = responses.compose_recipe(self.library, 'routine.work_active', {
                'work.active': self.context('actor_view', project['status'], {'worker': project['worker'], 'project_label': project['kind']}, 'view:project:shelter:status'),
                'work.progress': self.context('actor_view', 'progress_known', {'worked_seconds': project['worked_seconds'], 'required_seconds': project['required_seconds']}, 'view:project:shelter:progress')})
            settlement = responses.compose_recipe(self.library, 'routine.camp', {
                'camp.name': self.context('actor_view', 'camp_visible', {'camp_name': camp['name']}, 'view:camp'),
                'camp.capacity': self.context('actor_view', 'camp_visible', {'places': camp['shelter_places']}, 'view:camp'),
                'camp.residents': self.context('actor_view', 'camp_visible', {'residents': camp['residents']}, 'view:camp'),
                'camp.shortfall': self.context('actor_view', 'camp_visible', {'shortfall': camp['shelter_shortfall']}, 'view:camp')})
        self.assertIn('0 of 3600', work)
        self.assertIn('Willow Camp', settlement)
        self.assertIn('shelter shortfall: 1', settlement)
        self.assertNotIn('Oren', work + settlement)

    def test_all_player_drafts_name_actual_actions_but_submit_nothing(self):
        drafts = [f for f in self.library['families'] if f['channel'] == 'player_draft']
        self.assertEqual({f['state'] for f in drafts}, {key for key, _, _ in self.runtime.ACTIONS})
        with self.no_dispatch_or_mutation():
            for family in drafts:
                for variant in range(len(family['variants'])):
                    output = responses.render_fragment(self.library, family['id'],
                        self.context('player_request', family['state']), variant=variant)
                    self.assertTrue(output.startswith('I would like to'))
        self.assertEqual(self.store.read(self.key)['revision'], 0)

    def test_received_receipt_and_unconfigured_host_text_need_no_model(self):
        view = self.rise.view(self.store.read(self.key)['state'], 'founder')
        received = view['receipts'][0]
        self.assertFalse(self.assistance.assistance_status()['available'])
        with self.no_dispatch_or_mutation():
            record = responses.compose_recipe(self.library, 'routine.received', {
                'record.received': self.context('received_record', 'received', {'record_text': received['text']}, 'view:receipt:setup'),
                'record.received_time': self.context('received_record', 'received', {'received_at': received['recorded_at']}, 'view:receipt:setup')})
            status = responses.compose_recipe(self.library, 'routine.unconfigured', {
                'request.unconfigured': self.context('host_status', 'unconfigured', ref='host:configuration'),
                'actions.choose': self.context('host_status', 'listing', ref='host:action-list')})
        self.assertIn(received['text'], record)
        self.assertIn('AI assistance is not connected.', status)
        self.assertEqual(self.store.read(self.key)['revision'], 0)


if __name__ == '__main__':
    unittest.main()
