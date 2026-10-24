"""Catalog's actual R00 cases through the Engine/App proposal HTTP contract.

Select exact repository roots with IRGS_PROPOSAL_ENGINE_SOURCE and
IRGS_PROPOSAL_APP_SOURCE. Offline transport is injected only by this evaluator;
all request building, validation, execution and persistence remain in Engine/App.
"""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import solo_evaluation as evaluation
import solo_proposal_compatibility as compatibility

ENGINE = os.environ.get('IRGS_PROPOSAL_ENGINE_SOURCE')
APP = os.environ.get('IRGS_PROPOSAL_APP_SOURCE')


class OfflineReply:
    def __init__(self, reply_type):
        self.reply_type = reply_type
        self.action = 'walk_clearing'
        self.fault = None
        self.inputs = []
        self.entered, self.release = threading.Event(), threading.Event()
        self.release.set()

    def __call__(self, model_input, route, **limits):
        self.inputs.append(copy.deepcopy(model_input))
        self.entered.set()
        if not self.release.wait(5):
            raise RuntimeError('Synthetic evaluator transport was not released')
        body = {'intention': model_input['intention'], 'action_id': self.action,
                'source_refs': model_input['source_refs'][:1]}
        if self.fault == 'intent_changed': body['intention'] += ' forged'
        if self.fault == 'unknown_source': body['source_refs'] = ['unreceived-source']
        return self.reply_type('not-json' if self.fault == 'malformed_output' else json.dumps(body),
            json.dumps(route.identity()), json.dumps({'input_tokens': 20, 'output_tokens': 12}),
            'synthetic-offline-only', error='provider_denied' if self.fault == 'provider_denied' else None)


@unittest.skipUnless(ENGINE and APP, 'Exact proposal Engine/App source snapshots required')
class ProposalConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = compatibility.load_contract()
        allowed = cls.contract['consumers']
        for kind, root, commits in [('Engine', ENGINE, [allowed['engine_commit']]),
                                    ('App', APP, allowed['app_commits'].values())]:
            head = subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip()
            if head not in commits:
                raise RuntimeError('Unselected proposal consumer commit: ' + kind)
            if subprocess.check_output(['git', '-C', root, 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
                raise RuntimeError('Proposal qualification requires unedited dependency sources')
        engine = Path(ENGINE).resolve() / 'IRGS_3_3'
        app = Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        import server
        import assistance
        import solo_provider
        import solo_actions
        for module, source in [(server, app), (assistance, app),
                               (solo_provider, engine), (solo_actions, engine)]:
            if not Path(module.__file__).resolve().is_relative_to(source):
                raise RuntimeError('Consumer module is from a different checkout; use a fresh process')
        if solo_provider.SCHEMA_VERSION != cls.contract['proposal_schema']:
            raise RuntimeError('Proposal schema differs from the qualified content contract')
        if solo_provider.RISE_OPERATION != cls.contract['operation_id']:
            raise RuntimeError('Rise operation differs from the qualified content contract')
        for dependency, expected in [('Engine', allowed['engine_commit']),
                                     ('Catalog', '401df26a1f16be864dd15d7c5250da5d75f8ccca')]:
            selected = subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + dependency], text=True).strip()
            if selected != expected:
                raise RuntimeError('Unexpected committed App dependency pin: ' + dependency)
        cls.server_module, cls.api, cls.configuration = server, solo_provider, assistance.SoloConfiguration

    def setUp(self):
        evaluation.validate_fixture()
        self.evaluator = evaluation.load_evaluator_data()
        self.cases = self.evaluator['oracle']['cases']
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-catalog-proposal-http-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.server_module.Store(self.root / 'saves')
        self.technical = self.root / 'technical'
        self.technical.mkdir()
        self.transport = OfflineReply(self.api.TransportReply)
        self.route = self.api.Route('offline', 'synthetic', 'none', 'in-process', 'fixture-v1', 'v1',
            'config-v1', 'synthetic-transfer-approved-v1', 'synthetic-ceiling-v1', 10,
            enabled=True, approval_ref='offline-evaluator-only', lifecycle='qualified',
            tested_capabilities=(self.api.SCHEMA_VERSION,), operations=(self.api.RISE_OPERATION,),
            classifications=(evaluation.PROCESSING,))
        self.config = self.configuration(lambda scope: self.api.CapabilityBroker(
            self.api.SpecialistRegistry([self.route]), self.ledger(), enabled=True, scope_reader=scope),
            self.transport, 'offline', evaluation.PROCESSING, self.route.policy_ref,
            self.route.config_version, self.technical, 60, 512)
        self.server = None
        self.addCleanup(self.stop)
        self.start()
        choices = self.evaluator['setup']['choices']
        code, review = self.http('/api/rise/preview', {'choices': choices})
        self.assertEqual(code, 200)
        code, saved = self.http('/api/rise/create', {'name': 'Catalog proposal evaluation',
            'choices': choices, 'review_digest': review['review_digest'], 'request_id': 'catalog-proposal-create'})
        self.assertEqual(code, 200)
        self.key = saved['id']

    def ledger(self):
        return self.api.AttemptLedger(self.technical / 'attempts.sqlite', budget_units=100, max_inflight=2)

    def start(self):
        self.server = self.server_module.make_server(0, self.store.folder, solo_configuration=self.config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.token = self.http('/api/campaigns')[1]['token']

    def stop(self):
        self.transport.release.set()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = None

    def restart(self):
        self.stop()
        self.start()

    def http(self, path, body=None):
        headers = {'X-IRGS-Token': getattr(self, 'token', ''), 'Content-Type': 'application/json'}
        request = Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urlopen(request, timeout=10) as reply:
                return reply.status, json.load(reply)
        except HTTPError as error:
            return error.code, json.load(error)

    def body(self, case_id='solo-walk', *, request_id=None):
        case = next(c for c in self.cases if c['case_id'] == case_id)
        actor = evaluation.export_actor_input(case_id)
        return {'id': self.key, 'actor': actor['actor_id'], 'revision': case['request_revision'],
                'request_id': request_id or case['request_id'], 'intention': actor['user_intent']}

    def accept(self, body, proposal):
        return {**body, 'proposal_digest': proposal['proposal']['proposal_digest'], 'explicitly_accepted': True}

    def bytes(self):
        return self.store.path(self.key).read_bytes()

    def assert_private_absent(self, value):
        serialized = json.dumps(value)
        for marker in [*self.evaluator['oracle']['hidden_markers'], 'oren-home',
                       'opening_npc_inventory', 'evaluator_only', 'state_digest',
                       'restore_id', 'dependencies']:
            self.assertNotIn(marker, serialized)

    def assert_model_input(self, body, state):
        model = self.transport.inputs[-1]
        self.assertEqual(set(model), {'actor_id', 'intention', 'context', 'allowed_actions', 'source_refs'})
        self.assertEqual(model['intention'], body['intention'])
        self.assertEqual(model['actor_id'], 'founder')
        self.assertEqual(model['allowed_actions'], list(evaluation.SUPPORTED_ACTIONS))
        self.assertEqual(set(model['context']), {'options', 'received', 'received_window'})
        receipts = state['settlement_receipts']['founder']
        self.assertEqual(model['source_refs'], [r['id'] for r in model['context']['received']])
        for received in model['context']['received']:
            self.assertTrue(received['id'].startswith('settlement-receipt:'))
            original = receipts[received['id'].removeprefix('settlement-receipt:')]
            self.assertEqual(received['assertion'], original['text'])
            self.assertEqual(received['received_at'], original['recorded_at'])
            self.assertEqual(received['status'], 'received_outcome')
            self.assertEqual(received['source_ref'], state['rise']['source_ref'])
        self.assert_private_absent(model)

    def assert_case(self, case):
        record = self.store.read(self.key)
        state, expected = record['state'], case['expected']
        project = state['projects'].get('shelter', {})
        actual = dict(revision=record['revision'], clock=state['clock'],
            elapsed_seconds=state['elapsed_time']['seconds'], location=state['actors']['founder']['current']['location'],
            camp_established='camp' in state['settlements'], founder_timber=state['stocks']['founder-home']['timber'],
            npc_timber=state['stocks']['oren-home']['timber'], shelter_status=project.get('status', 'absent'),
            shelter_worked_seconds=project.get('worked', 0))
        self.assertEqual(actual, expected)
        for material, opening in state['opening_stock'].items():
            consumed = sum(f['quantity'] for f in state['material_flows'].values() if f['material'] == material)
            self.assertEqual(sum(stock.get(material, 0) for stock in state['stocks'].values()) + consumed, opening)

    def test_all_ten_catalog_cases_use_actual_proposals_commits_and_recovery(self):
        accepted = {}
        for case in self.cases:
            with self.subTest(case=case['case_id']):
                before, calls = self.bytes(), len(self.transport.inputs)
                state = self.store.read(self.key)['state']
                body = self.body(case['case_id'])
                self.assert_private_absent(body)
                self.transport.action = case['action_id']
                if case['kind'] == 'replay':
                    original, acceptance, result = accepted[case['replay_of']]
                    self.assertEqual(self.http('/api/ai/proposal', original), (200, result))
                    self.assertEqual(self.http('/api/ai/accept', acceptance), (200, result))
                    self.assertEqual(len(self.transport.inputs), calls)
                elif case['kind'] == 'changed_replay':
                    self.assertEqual(self.http('/api/ai/proposal', body)[0], 400)
                    original, acceptance, result = accepted[case['replay_of']]
                    self.assertEqual(self.http('/api/ai/accept', {**acceptance, 'intention': body['intention']})[0], 400)
                    self.assertEqual(len(self.transport.inputs), calls)
                else:
                    code, proposal = self.http('/api/ai/proposal', body)
                    self.assertEqual(code, 200)
                    self.assertEqual(self.bytes(), before, 'A proposal must never commit a world effect')
                    self.assert_private_absent(proposal)
                    if case['kind'] == 'stale':
                        self.assertEqual(proposal['code'], 'stale_state')
                        self.assertEqual(len(self.transport.inputs), calls)
                    else:
                        self.assert_model_input(body, state)
                        self.assertEqual(len(self.transport.inputs), calls + 1)
                        if case['kind'] == 'unsupported':
                            self.assertEqual(proposal['code'], 'unsupported_action')
                            self.assertEqual(self.http('/api/ai/proposal', body), (200, proposal))
                        else:
                            self.assertEqual(proposal['status'], 'proposal_ready')
                            self.assertEqual(proposal['proposal']['intention'], body['intention'])
                            acceptance = self.accept(body, proposal)
                            code, result = self.http('/api/ai/accept', acceptance)
                            if case['kind'] == 'denied':
                                self.assertEqual((code, result['code']), (422, 'action_unavailable'))
                                dependencies = json.loads(self.ledger().lookup(body['request_id'])['dependencies'])
                                self.assertEqual(dependencies['status'], 'rejected_no_effects')
                                self.assertEqual(dependencies['writes'], [])
                            else:
                                self.assertEqual((code, result['status']), (200, 'completed_successfully'))
                                self.assertEqual(result['declaration'], body['intention'])
                                self.assertIsNone(result['narrative'])
                                record = self.store.read(self.key)
                                event = record['state']['journal'][-1]
                                self.assertEqual(event['op'], compatibility.load_contract()['operation_id'])
                                self.assertEqual(event['params']['action'], case['action_id'])
                                self.assertIn(body['intention'], event['params']['instruction_ref'])
                                primary = record['state']['settlement_receipts']['founder'][event['params']['request_id']]
                                self.assertEqual(result['outcome']['summary'], primary['text'])
                                self.assertEqual(result['elapsed_time']['seconds'], case['expected']['elapsed_seconds'] - state['elapsed_time']['seconds'])
                                committed = self.bytes()
                                self.restart()
                                with ThreadPoolExecutor(max_workers=2) as pool:
                                    replies = list(pool.map(lambda _: self.http('/api/ai/accept', acceptance), range(2)))
                                self.assertEqual(replies, [(200, result), (200, result)])
                                lookup = '/api/ai/proposal-result/' + self.key + '/' + body['request_id'] + '?actor_id=founder'
                                self.assertEqual(self.http(lookup), (200, result))
                                self.assertEqual(self.bytes(), committed)
                                self.assertEqual(len(self.transport.inputs), calls + 1)
                                self.assert_private_absent(result)
                                accepted[case['case_id']] = (body, acceptance, result)
                if case['kind'] != 'legitimate': self.assertEqual(self.bytes(), before)
                self.assert_case(case)
                self.assert_private_absent(self.http('/api/playthrough/' + self.key + '?actor_id=founder')[1])
        self.assertEqual(len(accepted), 5)
        self.assertEqual(len(self.transport.inputs), 7)
        final = self.evaluator['oracle']['final_state']
        state = self.store.read(self.key)['state']
        self.assertEqual(state['stocks']['founder-home'], final['founder_inventory'])
        self.assertEqual(state['stocks']['oren-home'], final['npc_inventory'])
        self.assertEqual(state['assets']['shelter']['places'], final['shelter_places'])

    def test_explicit_acceptance_digest_and_exact_whitespace_intent_are_required(self):
        body = {**self.body(), 'intention': '  ' + self.body()['intention'] + '\nKeep this exact text.  '}
        before = self.bytes()
        _, proposal = self.http('/api/ai/proposal', body)
        self.assertEqual(proposal['proposal']['intention'], body['intention'])
        acceptance = self.accept(body, proposal)
        for changes, error in [({'explicitly_accepted': False}, 'acceptance_required'),
                               ({'proposal_digest': 'changed'}, 'acceptance_changed'),
                               ({'intention': body['intention'].strip()}, 'acceptance_changed')]:
            self.assertEqual(self.http('/api/ai/accept', {**acceptance, **changes})[1]['code'], error)
            self.assertEqual(self.bytes(), before)
        result = self.http('/api/ai/accept', acceptance)[1]
        self.assertEqual(result['declaration'], body['intention'])
        self.assertEqual(len(self.transport.inputs), 1)

    def test_foreign_actor_and_browser_supplied_context_cannot_dispatch(self):
        before = self.bytes()
        self.assertEqual(self.http('/api/ai/proposal', {**self.body(), 'actor': 'oren'})[0], 403)
        self.assertEqual(self.http('/api/ai/proposal', {**self.body(), 'context': {
            'oracle': self.evaluator['oracle']['hidden_markers'][0]}})[0], 400)
        self.assertEqual(self.transport.inputs, [])
        self.assertEqual(self.bytes(), before)

    def test_provider_failures_preserve_exact_intent_and_do_not_redispatch(self):
        before = self.bytes()
        for fault in ('provider_denied', 'malformed_output', 'intent_changed', 'unknown_source'):
            with self.subTest(fault=fault):
                self.transport.fault = fault
                body = self.body(request_id='failure-' + fault)
                calls = len(self.transport.inputs)
                first = self.http('/api/ai/proposal', body)
                self.assertEqual(first[1]['code'], fault)
                self.assertEqual(self.http('/api/ai/proposal', body), first)
                self.assertEqual(len(self.transport.inputs), calls + 1)
                row = self.ledger().lookup(body['request_id'])
                self.assertEqual(json.loads(row['request'])['intention'], body['intention'])
                self.assertEqual(row['reserved'], 10)
                self.assertEqual(self.bytes(), before)

    def test_identical_restore_fences_draft_and_preserves_committed_receipt(self):
        body = self.body()
        _, proposal = self.http('/api/ai/proposal', body)
        acceptance, before = self.accept(body, proposal), self.bytes()
        for path in ('/api/delete', '/api/restore'):
            self.assertEqual(self.http(path, {'id': self.key, 'revision': 0})[0], 200)
        self.assertEqual(self.bytes(), before)
        lookup = '/api/ai/proposal-result/' + self.key + '/' + body['request_id'] + '?actor_id=founder'
        self.assertEqual(self.http(lookup)[1]['code'], 'stale_scope_or_state')
        self.assertEqual(self.http('/api/ai/accept', acceptance)[1]['code'], 'stale_scope')
        self.assertEqual(len(self.transport.inputs), 1)
        fresh = self.body(request_id='after-restore')
        _, proposal = self.http('/api/ai/proposal', fresh)
        acceptance = self.accept(fresh, proposal)
        original = self.http('/api/ai/accept', acceptance)
        committed = self.bytes()
        for path in ('/api/delete', '/api/restore'):
            self.assertEqual(self.http(path, {'id': self.key, 'revision': 1})[0], 200)
        self.restart()
        self.assertEqual(self.http('/api/ai/accept', acceptance), original)
        self.assertEqual(self.bytes(), committed)
        self.assertEqual(len(self.transport.inputs), 2)

    def test_failed_persistence_retries_without_another_attempt(self):
        body = self.body()
        _, proposal = self.http('/api/ai/proposal', body)
        acceptance, before = self.accept(body, proposal), self.bytes()
        with patch.object(self.server_module.Store, 'write', side_effect=OSError('synthetic disk failure')):
            self.assertEqual(self.http('/api/ai/accept', acceptance)[0], 503)
        self.assertEqual(self.bytes(), before)
        self.assertEqual(self.http('/api/ai/accept', acceptance)[1]['status'], 'completed_successfully')
        self.assertEqual(len(self.transport.inputs), 1)
        self.assertEqual(self.store.read(self.key)['revision'], 1)

    def test_late_output_and_cancellation_cannot_commit_or_redispatch(self):
        self.transport.release.clear()
        body = self.body()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.http, '/api/ai/proposal', body)
            self.assertTrue(self.transport.entered.wait(2))
            result = self.http('/api/rise/action', {'id': self.key, 'actor': 'founder', 'revision': 0,
                'request_id': 'parallel-inspection', 'action': 'inspect'})
            self.assertEqual(result[1]['status'], 'completed_successfully')
            self.transport.release.set()
            self.assertEqual(future.result()[1]['code'], 'stale_scope_or_state')
        before = self.bytes()
        self.transport.entered.clear()
        self.transport.release.clear()
        body = {**self.body(request_id='cancelled-walk'), 'revision': 1}
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.http, '/api/ai/proposal', body)
            self.assertTrue(self.transport.entered.wait(2))
            self.assertEqual(self.http('/api/ai/cancel', {k: body[k] for k in ('id', 'actor', 'request_id')})[1]['code'], 'cancelled')
            self.transport.release.set()
            self.assertEqual(future.result()[1]['code'], 'cancelled')
        self.restart()
        self.assertEqual(self.http('/api/ai/proposal', body)[1]['code'], 'cancelled')
        self.assertEqual(len(self.transport.inputs), 2)
        self.assertEqual(self.bytes(), before)

    def test_unconfigured_host_preserves_intent_without_dispatch(self):
        self.stop()
        self.config = None
        self.start()
        before, body = self.bytes(), self.body()
        original = copy.deepcopy(body)
        self.assertEqual(self.http('/api/ai/proposal', body)[1]['code'], 'unconfigured')
        self.assertEqual(body, original)
        self.assertEqual(self.transport.inputs, [])
        self.assertEqual(self.bytes(), before)


if __name__ == '__main__':
    unittest.main()
