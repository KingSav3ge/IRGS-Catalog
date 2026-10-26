"""Catalog receipts over actual public App starts and Engine-selected phases."""
from concurrent.futures import ThreadPoolExecutor
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from unittest.mock import patch

from tools.tests import test_integrated_response_consumers as integrated
import phase_response_compatibility as compatibility

ENGINE = os.environ.get('IRGS_PHASE_ENGINE_SOURCE')
APP = os.environ.get('IRGS_PHASE_APP_SOURCE')


class PhaseResponseConsumerTests(integrated.IntegratedResponseConsumerTests):
    __unittest_skip__ = not bool(ENGINE and APP)
    __unittest_skip_why__ = 'Exact published phase Engine/App sources required'

    @classmethod
    def setUpClass(cls):
        cls.phase_contract = compatibility.load_contract()
        cls.followup = compatibility.baseline.baseline.load_contract()
        cls.contract = compatibility.baseline.baseline.original.load_fixture()
        consumers = cls.phase_contract['consumers']
        for source, expected in ((ENGINE, consumers['engine_commit']), (APP, consumers['app_commit'])):
            if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != expected:
                raise RuntimeError('Unselected phase consumer commit')
            if subprocess.check_output(['git', '-C', source, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Phase consumer dependencies must be clean')
        for component, expected in (('Engine', consumers['app_engine_pin']), ('Catalog', consumers['app_catalog_pin'])):
            actual = subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + component], text=True).strip()
            if actual != expected:
                raise RuntimeError('Unexpected committed App pointer: ' + component)
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(integrated.CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'process_bridge',
                     'starting_selection', 'settlement_setup', 'historical_campaigns', 'core_world',
                     'offline_responses', 'scene_actions', 'solo_provider', 'response_depot',
                     'openai_proposals', 'phase_contract'):
            module = importlib.import_module(name)
            root = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'process_bridge') else engine
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Imported another checkout; use a fresh process')
            setattr(cls, name if name != 'phase_contract' else 'phases', module)

    def prepare_rise_site(self):
        self.act('rise')
        body = self.body('rise', {'action_id': 'found', 'request_id': 'phase-fixture-found'})
        code, result = self.http('/api/rise/action', body)
        self.assertEqual((code, result['status']), (200, 'completed_successfully'))

    def start_body(self, context):
        view = self.view(context)
        packet = view['process_control']
        self.assertEqual(packet['engine_schema'], 'irgs-phase-capabilities-1')
        self.assertTrue(packet['start_available'])
        action = 'build' if context == 'rise' else 'look-quay'
        selected = next(row for row in packet['start_options'] if row['action_id'] == action)
        return {'id': self.keys[context], 'actor': view['actor_id'], 'revision': view['revision'],
            'view_token': packet['view_token'], 'request_id': uuid.uuid4().hex, 'command': 'start',
            'capability_id': selected['capability_id'],
            'intention': '  My explicit ' + context + ' attempt.\nKeep these exact words.  '}

    @staticmethod
    def acceptance(body):
        return {**{k: body[k] for k in ('id', 'actor', 'request_id')}, 'explicitly_accepted': True}

    def prepare(self, body):
        before = self.store.path(body['id']).read_bytes()
        code, prepared = self.http('/api/process/prepare', body)
        self.assertEqual(code, 200, prepared)
        self.assertEqual(self.http('/api/process/prepare', body), (200, prepared))
        self.assertEqual(prepared['intention'], body['intention'])
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)
        code, result = self.http('/api/process/execute', {**self.acceptance(body), 'explicitly_accepted': False})
        self.assertEqual(code, 400, result)
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)
        self.assert_private_free(prepared)
        return prepared

    def execute(self, context, body, prepared):
        code, result = self.http('/api/process/execute', self.acceptance(body))
        self.assertEqual(code, 200, result)
        self.assertEqual(result['process']['phase_id'], prepared['phase_id'])
        self.assertEqual(result['process']['process_id'], prepared['process_id'])
        self.assertEqual(result['process']['phase_intention'], body['intention'])
        self.assert_phase_presentation(context, result)
        return result

    def assert_phase_presentation(self, context, result):
        packet = result['presentation']
        self.assertEqual(packet['render_usage'], integrated.USAGE)
        self.assertEqual(packet['format'], 'plain_text')
        self.assertEqual(packet['actor_id'], result['actor'])
        self.assertEqual(packet['source_ref'], result['receipt']['event_id'])
        for name in ('engine_library', 'catalog_library'):
            self.assertEqual(packet[name], {'id': 'irgs-response-depot-v1', 'version': '1.0.0'})
        self.assertTrue(packet['text'].startswith(self.receipt_facts(context, result)['literal_text']))
        self.assert_private_free(result)
        for hidden in ('dependencies', 'restore_id', 'rule_digest', 'PRIVATE_PHASE_STORAGE'):
            self.assertNotIn(hidden, json.dumps(result))
        self.assertEqual(self.view(context)['completed_actions'][-1]['presentation'], packet)

    def begin(self, context):
        before = copy.deepcopy(self.store.read(self.keys[context])['state'])
        body = self.start_body(context)
        prepared = self.prepare(body)
        result = self.execute(context, body, prepared)
        self.assertEqual(result['process']['worked_seconds'], 0)
        self.assertEqual(result['process']['elapsed_seconds'], 0)
        self.assertEqual(result['process']['original_intention'], body['intention'])
        after = self.store.read(body['id'])['state']
        for field in ('stocks', 'evidence', 'elapsed_time', 'campaign_time'):
            self.assertEqual(after[field], before[field])
        return prepared['process_id'], body, result

    def command_body(self, context, process, command, details=None):
        view = self.view(context)
        received = next(row for row in view['process_control']['processes']
            if row['received']['process_id'] == process)
        self.assertEqual(received['status_basis'], 'received_phase')
        self.assertFalse(received['live_status_probed'])
        self.assertIn(command, received['commands'])
        return {'id': self.keys[context], 'actor': view['actor_id'], 'revision': view['revision'],
            'view_token': view['process_control']['view_token'], 'request_id': uuid.uuid4().hex,
            'process_id': process, 'command': command, 'details': details or {},
            'intention': '  Explicit ' + command + '.\nOnly this reviewed phase.  '}

    def phase(self, context, process, command, details=None):
        body = self.command_body(context, process, command, details)
        prepared = self.prepare(body)
        return body, self.execute(context, body, prepared)

    def test_public_discovery_matches_engine_and_private_permission_does_not_select_menu(self):
        self.prepare_rise_site()
        for context, key in self.keys.items():
            before = self.store.path(key).read_bytes()
            record = self.store.read(key)
            scope = self.process_bridge.ProcessService(self.store).scope(record)
            expected = self.phases.actor_view(self.core_world.CoreWorld(state=record['state']),
                self.view(context)['actor_id'], branch_id=scope.branch_id, restore_id=scope.restore_id)
            packet = self.view(context)['process_control']
            self.assertEqual(packet['start_options'], expected['start_options'])
            self.assertEqual(packet['processes'], [])
            self.assertEqual(self.store.path(key).read_bytes(), before)
        original = self.view('rise')['process_control']['start_options']
        record = self.store.read(self.keys['rise'])
        record['state']['grants']['founding']['active'] = False  # Evaluator-only synthetic mutation.
        self.store.write(record)
        self.assertEqual(self.view('rise')['process_control']['start_options'], original)
        body = self.start_body('rise')
        self.prepare(body)
        before = self.store.path(body['id']).read_bytes()
        code, failure = self.http('/api/process/execute', self.acceptance(body))
        self.assertEqual(code, 400, failure)
        self.assertNotIn('dependencies', json.dumps(failure))
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)

    def test_non_rise_public_observation_retains_information_boundary_and_exact_completion(self):
        process, start, started = self.begin('quay')
        evidence = copy.deepcopy(self.store.read(self.keys['quay'])['state']['evidence'])
        _, partial = self.phase('quay', process, 'advance', {'seconds': 1})
        self.assertEqual(partial['process']['worked_seconds'], 1)
        self.assertEqual(self.store.read(self.keys['quay'])['state']['evidence'], evidence)
        for command in ('pause', 'resume'):
            _, result = self.phase('quay', process, command)
            self.assertEqual(result['process']['elapsed_seconds'], 0)
        body, done = self.phase('quay', process, 'advance', {'seconds': 999})
        self.assertEqual(done['process']['status'], 'completed')
        self.assertEqual(done['process']['worked_seconds'], 20)
        self.assertEqual(done['process']['elapsed_seconds'], 19)
        state = self.store.read(self.keys['quay'])['state']
        self.assertEqual(state['elapsed_time']['seconds'], 20)
        self.assertNotEqual(state['evidence'], evidence)
        self.assertEqual(self.lookup('quay', start), (200, started))
        self.assertEqual(self.lookup('quay', body), (200, done))

    def test_rise_public_work_preserves_progress_zero_spans_and_saved_receipts(self):
        self.prepare_rise_site()
        process, start, started = self.begin('rise')
        _, partial = self.phase('rise', process, 'advance', {'seconds': 100})
        self.assertEqual(partial['process']['worked_seconds'], 100)
        for command in ('pause', 'resume'):
            _, result = self.phase('rise', process, command)
            self.assertEqual(result['process']['elapsed_seconds'], 0)
            self.assertEqual(result['process']['worked_seconds'], 100)
        for _ in range(3):
            body, done = self.phase('rise', process, 'advance', {'seconds': 3600})
            if done['process']['status'] == 'completed':
                break
        self.assertEqual(done['process']['status'], 'completed')
        self.assertEqual(self.store.read(self.keys['rise'])['state']['projects']['shelter']['worked'], 3600)
        saved = self.store.path(self.keys['rise']).read_bytes()
        self.stop(); self.start()
        for old, result in ((start, started), (body, done)):
            self.assertEqual(self.lookup('rise', old), (200, result))
            self.assertEqual(self.http('/api/process/execute', self.acceptance(old)), (200, result))
        self.assertEqual(self.store.path(self.keys['rise']).read_bytes(), saved)

    def test_start_and_advance_failed_save_restart_and_concurrent_retry_commit_once(self):
        body = self.start_body('quay')
        for command in ('start', 'advance'):
            if command == 'advance':
                body = self.command_body('quay', prepared['process_id'], 'advance', {'seconds': 1})
            prepared = self.prepare(body)
            before = self.store.path(body['id']).read_bytes()
            with patch.object(self.server.Store, 'write', side_effect=OSError('PRIVATE_PHASE_STORAGE')):
                code, failure = self.http('/api/process/execute', self.acceptance(body))
            self.assertEqual(code, 503, failure)
            self.assertNotIn('PRIVATE_PHASE_STORAGE', json.dumps(failure))
            self.assertEqual(self.store.path(body['id']).read_bytes(), before)
            self.assertEqual(self.lookup('quay', body)[0], 404)
            self.stop(); self.start()
            code, status = self.http('/api/process/status', {k: body[k] for k in ('id', 'actor', 'request_id')})
            self.assertEqual(code, 200, status)
            for key in ('process_id', 'phase_id'):
                self.assertEqual(status[key], prepared[key])
            with ThreadPoolExecutor(max_workers=2) as pool:
                replies = list(pool.map(lambda _: self.http('/api/process/execute', self.acceptance(body)), range(2)))
            self.assertEqual(replies[0], replies[1])
            self.assertEqual(replies[0][0], 200, replies)
            result = replies[0][1]
            self.assert_phase_presentation('quay', result)
            self.assertEqual(result['process']['worked_seconds'], 0 if command == 'start' else 1)
            committed = self.store.path(body['id']).read_bytes()
            self.assertEqual(self.http('/api/process/execute', self.acceptance(body)), (200, result))
            self.assertEqual(self.store.path(body['id']).read_bytes(), committed)

    def test_foreign_forged_stale_and_restored_pending_starts_cannot_execute(self):
        self.prepare_rise_site()
        body = self.start_body('quay')
        foreign = self.start_body('rise')['capability_id']
        before = self.store.path(body['id']).read_bytes()
        for changes in ({'capability_id': foreign}, {'actor': 'foreign'}, {'view_token': 'stale'},
                        {'details': {'kind': 'work'}}, {'process_id': 'forged'},
                        {'source_ref': 'forged'}, {'presentation': {'text': 'fabricated success'}}):
            code, failure = self.http('/api/process/prepare', {**body, **changes})
            self.assertIn(code, (400, 403), failure)
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)
        self.prepare(body)
        self.assertEqual(self.http('/api/process/prepare', {**body, 'intention': 'changed'})[0], 400)
        revision = self.store.read(body['id'])['revision']
        self.assertEqual(self.http('/api/delete', {'id': body['id'], 'revision': revision})[0], 200)
        self.assertEqual(self.http('/api/restore', {'id': body['id'], 'revision': revision})[0], 200)
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)
        self.assertEqual(self.http('/api/process/execute', self.acceptance(body))[0], 400)
        self.assertEqual(self.store.path(body['id']).read_bytes(), before)
        process, saved_body, saved = self.begin('quay')
        committed = self.store.path(body['id']).read_bytes()
        revision = self.store.read(body['id'])['revision']
        self.assertEqual(self.http('/api/delete', {'id': body['id'], 'revision': revision})[0], 200)
        self.assertEqual(self.http('/api/restore', {'id': body['id'], 'revision': revision})[0], 200)
        self.assertEqual(self.lookup('quay', saved_body), (200, saved))
        self.assertEqual(self.http('/api/process/execute', self.acceptance(saved_body)), (200, saved))
        self.assertEqual(self.store.path(body['id']).read_bytes(), committed)

    def test_inspect_and_cancel_are_explicit_zero_span_received_phases(self):
        process, _, _ = self.begin('quay')
        for command in ('inspect', 'cancel'):
            _, result = self.phase('quay', process, command)
            self.assertEqual(result['process']['elapsed_seconds'], 0)
            self.assertEqual(result['process']['worked_seconds'], 0)
        self.assertEqual(result['process']['status'], 'cancelled')
        self.assertTrue(result['process']['terminal'])
        packet = next(row for row in self.view('quay')['process_control']['processes']
            if row['received']['process_id'] == process)
        self.assertEqual(packet['commands'], [])

    def test_missing_catalog_keeps_complete_engine_phase_text_and_stable_saved_fallback(self):
        process, _, _ = self.begin('quay')
        body = self.command_body('quay', process, 'advance', {'seconds': 20})
        prepared = self.prepare(body)
        self.local_presentation._catalog.cache_clear()
        try:
            with patch.object(self.local_presentation, 'CATALOG_ROOT', Path(self.temp.name) / 'missing-catalog'):
                code, result = self.http('/api/process/execute', self.acceptance(body))
                self.assertEqual(code, 200, result)
                self.assertIsNone(result['presentation']['catalog_library'])
                self.assertEqual(result['presentation']['engine_library']['id'], 'irgs-response-depot-v1')
                self.assertTrue(result['presentation']['text'].startswith(self.receipt_facts('quay', result)['literal_text']))
                self.assertEqual(result['presentation']['render_usage'], integrated.USAGE)
                self.assertEqual(result['process']['phase_id'], prepared['phase_id'])
                self.assertEqual(result['process']['status'], 'completed')
        finally:
            self.local_presentation._catalog.cache_clear()
        self.assertEqual(self.view('quay')['local_responses']['catalog_library']['id'], 'irgs-response-depot-v1')
        self.assertEqual(self.lookup('quay', body), (200, result))
        self.assertEqual(self.http('/api/process/execute', self.acceptance(body)), (200, result))


if __name__ == '__main__':
    import unittest
    unittest.main()
