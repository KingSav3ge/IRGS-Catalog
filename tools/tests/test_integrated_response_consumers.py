"""Integrated App HTTP projection and persisted receipts over the original cases."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tools.tests import test_shared_response_consumers as legacy

CATALOG = legacy.CATALOG
import integrated_response_compatibility as compatibility

ENGINE = os.environ.get('IRGS_INTEGRATED_ENGINE_SOURCE')
APP = os.environ.get('IRGS_INTEGRATED_APP_SOURCE')
USAGE = {'provider_calls': 0, 'model_tokens': 0}


@unittest.skipUnless(ENGINE and APP, 'Exact integrated-response Engine/App snapshots required')
class IntegratedResponseConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.followup = compatibility.load_contract()
        # Original setup/cases keep their original consumer declarations.
        cls.contract = compatibility.original.load_fixture()
        consumers = cls.followup['consumers']
        for source, expected in [(ENGINE, consumers['engine_commit']), (APP, consumers['app_commit'])]:
            if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != expected:
                raise RuntimeError('Unselected integrated-response consumer')
            if subprocess.check_output(['git', '-C', source, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Integrated-response dependencies must be clean')
        for component, expected in [('Engine', consumers['engine_commit']), ('Catalog', consumers['app_catalog_pin'])]:
            actual = subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + component], text=True).strip()
            if actual != expected:
                raise RuntimeError('Unexpected committed App dependency pin: ' + component)
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation',
                     'starting_selection', 'settlement_setup', 'historical_campaigns',
                     'core_world', 'offline_responses', 'scene_actions', 'solo_provider',
                     'response_depot', 'openai_proposals'):
            module = importlib.import_module(name)
            expected_root = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation') else engine
            if not Path(module.__file__).resolve().is_relative_to(expected_root):
                raise RuntimeError('Consumer imported another checkout; use a fresh process')
            setattr(cls, name, module)

    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.dispatch = stack.enter_context(patch('solo_provider.CapabilityBroker.dispatch',
            side_effect=AssertionError('Routine requests must not dispatch')))
        self.transport = stack.enter_context(patch('openai_proposals.OpenAIProposalTransport.__call__',
            side_effect=AssertionError('Routine requests must not call a provider')))
        legacy.SharedResponseConsumerTests.setUp(self)
        self.local_presentation._catalog.cache_clear()
        self.addCleanup(self.local_presentation._catalog.cache_clear)
        self.start()
        self.addCleanup(self.stop)

    def tearDown(self):
        self.dispatch.assert_not_called()
        self.transport.assert_not_called()

    def start(self):
        self.host = self.server.make_server(0, self.store.folder, solo_configuration=None)
        self.thread = threading.Thread(target=self.host.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.host.server_port)
        self.token = self.http('/api/campaigns')[1]['token']

    def stop(self):
        self.host.shutdown()
        self.host.server_close()
        self.thread.join()

    def http(self, path, body=None):
        headers = {'X-IRGS-Token': getattr(self, 'token', '')}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urlopen(request, timeout=15) as reply:
                return reply.status, json.load(reply)
        except HTTPError as error:
            return error.code, json.load(error)

    def view(self, context):
        code, result = self.http('/api/playthrough/' + self.keys[context])
        self.assertEqual(code, 200, result)
        self.assert_private_free(result)
        return result

    body = legacy.SharedResponseConsumerTests.body

    def endpoint(self, context):
        return '/api/rise/action' if context == 'rise' else '/api/action'

    def act(self, context, index=0):
        case = self.inputs[context]['cases'][index]
        body = self.body(context, case)
        code, result = self.http(self.endpoint(context), body)
        self.assertEqual(code, 200, result)
        expected = self.oracle['cases'][case['case_id']]
        self.assertEqual(result['status'], expected['status'])
        duration = result['elapsed_time']['seconds' if context == 'rise' else 'duration_seconds']
        self.assertEqual(duration, expected['duration_seconds'])
        self.assertEqual(self.store.read(self.keys[context])['state']['elapsed_time']['seconds'], expected['total_seconds'])
        self.assert_private_free(result)
        return result, body

    def lookup(self, context, body):
        return self.http('/api/action-result/' + self.keys[context] + '/' + body['request_id'] + '?actor_id=' + body['actor'])

    def assert_private_free(self, value):
        text = json.dumps(value)
        for secret in (self.oracle['hidden_marker'], 'state_digest', 'PRIVATE_DEPOT_FAILURE', 'PRIVATE_RUNTIME_FAILURE'):
            self.assertNotIn(secret, text)

    def receipt_facts(self, context, result):
        world = self.core_world.CoreWorld(state=self.store.read(self.keys[context])['state'])
        before = world.save()
        facts = self.offline_responses.receipt_facts(world, result['actor'], result['receipt']['event_id'])
        self.assertEqual(world.save(), before)
        return facts

    def assert_saved_presentation(self, context, result):
        packet = result['presentation']
        self.assertEqual(packet['format'], 'plain_text')
        self.assertEqual(packet['actor_id'], result['actor'])
        self.assertEqual(packet['source_ref'], result['receipt']['event_id'])
        self.assertTrue(packet['snapshot_id'])
        self.assertEqual(packet['render_usage'], USAGE)
        self.assertEqual(packet['catalog_library'], {'id': 'irgs-response-depot-v1', 'version': '1.0.0'})
        self.assertEqual(packet['engine_library'], {'id': 'irgs-engine-routine-responses-v1', 'version': '1.0.0'})
        self.assertTrue(packet['text'].startswith(self.receipt_facts(context, result)['literal_text']))
        self.assertEqual(self.view(context)['completed_actions'][-1]['presentation'], packet)

    def test_native_presentations_match_nine_real_cases_and_all_older_receipts_stay_saved(self):
        for context in self.keys:
            calendar = copy.deepcopy(self.store.read(self.keys[context])['state']['campaign_time'])
            saved = []
            for index in range(len(self.inputs[context]['cases'])):
                result, body = self.act(context, index)
                self.assert_saved_presentation(context, result)
                saved.append((body, result))
                before = self.store.path(self.keys[context]).read_bytes()
                for prior_body, prior_result in saved:
                    self.assertEqual(self.lookup(context, prior_body), (200, prior_result))
                self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)
            self.assertEqual(self.store.read(self.keys[context])['state']['campaign_time'], calendar)
        state = self.store.read(self.keys['quay'])['state']
        actor = self.view('quay')['actor_id']
        self.assertEqual(state['stocks'][actor]['sealed_dispatch'], 0)
        self.assertEqual(state['stocks']['clerk-tray']['sealed_dispatch'], 1)
        self.assertEqual(sum(stock.get('sealed_dispatch', 0) for stock in state['stocks'].values()), 1)

    def test_local_responses_load_exact_depot_and_non_submitting_drafts_in_both_contexts(self):
        _, app_library = self.local_presentation._catalog()
        engine_bytes = self.response_depot.DEPOT.read_bytes()
        self.assertEqual(hashlib.sha256(engine_bytes).hexdigest(), compatibility.original.LIBRARY_SHA256)
        self.assertEqual(json.loads(engine_bytes), app_library)
        self.assertEqual(sum(len(f['variants']) for f in app_library['families'] if f['channel'] == 'system'), 750)
        self.assertEqual(sum(len(f['variants']) for f in app_library['families'] if f['channel'] == 'player_draft'), 250)
        self.assertEqual(len(app_library['recipes']), 32)
        for context, key in self.keys.items():
            before = self.store.path(key).read_bytes()
            first, second = self.view(context), self.view(context)
            for view in (first, second):
                packet = view['local_responses']
                self.assertEqual(packet['schema_version'], 1)
                self.assertEqual(packet['scope']['campaign_id'], key)
                self.assertEqual(packet['scope']['actor_id'], view['actor_id'])
                self.assertEqual(packet['scope']['revision'], view['revision'])
                self.assertEqual(packet['render_usage'], USAGE)
                self.assertEqual(packet['catalog_library']['id'], 'irgs-response-depot-v1')
                self.assertTrue(packet['engine_runtime'])
                self.assertEqual({d['source'] for d in packet['drafts']}, {'catalog', 'engine'})
                for draft in packet['drafts']:
                    self.assertTrue(draft['requires_explicit_submission'])
                    self.assertFalse(draft['automatic_execution'])
                    if draft['source'] == 'catalog':
                        self.assertIsNone(draft['operation_id'])
                        self.assertTrue(draft['intent_tag'])
            self.assertNotEqual(first['local_responses']['scope']['view_id'], second['local_responses']['scope']['view_id'])
            self.assertEqual(first['local_responses']['drafts'], second['local_responses']['drafts'])
            self.assertEqual(before, self.store.path(key).read_bytes())

    def test_selected_depot_draft_requires_explicit_declaration_and_has_no_physical_effect(self):
        for context, key in self.keys.items():
            view = self.view(context)
            draft = next(d for d in view['local_responses']['drafts'] if d['id'] == 'catalog:player.look_around')
            before = self.store.read(key)['state']
            code, result = self.http('/api/declaration', {'id': key, 'actor': view['actor_id'],
                'revision': view['revision'], 'request_id': 'explicit-current-draft', 'declaration': draft['text']})
            self.assertEqual((code, result['status']), (200, 'declared_not_resolved'))
            self.assertEqual(result['declaration'], draft['text'])
            after = self.store.read(key)['state']
            for field in ('stocks', 'opening_stock', 'elapsed_time', 'campaign_time', 'actors'):
                self.assertEqual(before[field], after[field])

    def test_lost_ack_restart_and_concurrent_retry_return_identical_saved_presentations(self):
        saved = {context: self.act(context) for context in self.keys}
        for context in self.keys:
            self.act(context, 1)
        before = {context: self.store.path(key).read_bytes() for context, key in self.keys.items()}
        self.stop()
        self.start()
        for context, (result, body) in saved.items():
            with ThreadPoolExecutor(max_workers=2) as pool:
                replies = list(pool.map(lambda _: self.http(self.endpoint(context), body), range(2)))
            self.assertEqual(replies, [(200, result), (200, result)])
            self.assertEqual(self.lookup(context, body), (200, result))
            self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before[context])

    def test_failed_save_commits_neither_effect_nor_presentation_and_retry_executes_once(self):
        for context, key in self.keys.items():
            body = self.body(context, self.inputs[context]['cases'][0])
            before = self.store.path(key).read_bytes()
            with patch.object(self.server.Store, 'write', side_effect=OSError('PRIVATE_STORAGE_FAILURE')):
                code, failure = self.http(self.endpoint(context), body)
            self.assertEqual(code, 503)
            self.assertNotIn('PRIVATE_STORAGE_FAILURE', json.dumps(failure))
            self.assertEqual(self.store.path(key).read_bytes(), before)
            self.assertEqual(self.lookup(context, body)[0], 404)
            code, result = self.http(self.endpoint(context), body)
            self.assertEqual(code, 200, result)
            committed = self.store.path(key).read_bytes()
            self.assert_saved_presentation(context, result)
            self.assertEqual(self.http(self.endpoint(context), body), (200, result))
            self.assertEqual(self.store.path(key).read_bytes(), committed)
            expected = self.oracle['cases'][self.inputs[context]['cases'][0]['case_id']]
            self.assertEqual(self.store.read(key)['state']['elapsed_time']['seconds'], expected['total_seconds'])
            self.assertEqual(self.store.read(key)['revision'], 1)

    def fallback(self, *, corrupt):
        root = Path(self.temp.name) / 'synthetic-catalog-failure'
        if corrupt:
            for name in ('release.json', 'scripted_responses.py', 'responses/depot_v1/library.json'):
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(CATALOG / name, destination)
            (root / 'responses/depot_v1/library.json').write_text('{}')
        saved = {}
        self.local_presentation._catalog.cache_clear()
        try:
            with patch.object(self.local_presentation, 'CATALOG_ROOT', root), \
                 patch.object(self.offline_responses, '_library', side_effect=ValueError('PRIVATE_RUNTIME_FAILURE')), \
                 patch.object(self.offline_responses, 'player_drafts', side_effect=ValueError('PRIVATE_RUNTIME_FAILURE')):
                for context in self.keys:
                    view = self.view(context)
                    self.assertTrue(view['capabilities']['can_declare'])
                    self.assertEqual(view['local_responses']['drafts'], [])
                    self.assertIsNone(view['local_responses']['catalog_library'])
                    result, body = self.act(context)
                    self.assertEqual(result['presentation']['mode'], 'literal_receipt')
                    self.assertIsNone(result['presentation']['catalog_library'])
                    self.assertEqual(result['presentation']['text'], self.receipt_facts(context, result)['literal_text'])
                    self.assertEqual(result['presentation']['render_usage'], USAGE)
                    saved[context] = (result, body)
        finally:
            self.local_presentation._catalog.cache_clear()
        for context, (result, body) in saved.items():
            self.assertEqual(self.view(context)['local_responses']['catalog_library']['id'], 'irgs-response-depot-v1')
            self.assertEqual(self.lookup(context, body), (200, result))

    def test_missing_source_and_runtime_keep_literal_results_without_paid_fallback(self):
        self.fallback(corrupt=False)

    def test_corrupt_source_and_runtime_keep_literal_results_without_paid_fallback(self):
        self.fallback(corrupt=True)

    def test_foreign_actors_forged_presentation_and_stale_requests_change_no_save(self):
        for context, key in self.keys.items():
            _, body = self.act(context)
            before = self.store.path(key).read_bytes()
            for changes in ({'request_id': 'forged', 'presentation': {'text': 'fabricated success'}},
                            {'request_id': 'stale-new'}, {'request_id': 'foreign-new', 'actor': 'foreign'}):
                code, _ = self.http(self.endpoint(context), {**body, **changes})
                self.assertIn(code, (400, 403))
            self.assertEqual(self.http('/api/playthrough/' + key + '?actor_id=foreign')[0], 403)
            self.assertEqual(self.store.path(key).read_bytes(), before)

    def test_identical_byte_restore_refreshes_view_scope_but_preserves_saved_presentation(self):
        for context, key in self.keys.items():
            result, body = self.act(context)
            scope = self.view(context)['local_responses']['scope']
            before = self.store.path(key).read_bytes()
            revision = self.store.read(key)['revision']
            self.assertEqual(self.http('/api/delete', {'id': key, 'revision': revision})[0], 200)
            self.assertEqual(self.lookup(context, body)[0], 404)
            self.assertEqual(self.http('/api/restore', {'id': key, 'revision': revision})[0], 200)
            new_scope = self.view(context)['local_responses']['scope']
            self.assertNotEqual(scope['view_id'], new_scope['view_id'])
            self.assertEqual(self.store.path(key).read_bytes(), before)
            self.assertEqual(self.lookup(context, body), (200, result))


if __name__ == '__main__':
    unittest.main()
