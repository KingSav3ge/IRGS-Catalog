"""Pinned baseline diagnostics and real positive loops; missing starts remain gaps."""
from contextlib import ExitStack
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from tools.tests import test_integrated_response_consumers as http_helpers
import player_start_evaluation as evaluation

ENGINE = os.environ.get('IRGS_START_ENGINE_SOURCE')
APP = os.environ.get('IRGS_START_APP_SOURCE')
CATALOG = http_helpers.CATALOG


@unittest.skipUnless(ENGINE and APP, 'Exact evaluated Engine/App snapshots required')
class PlayerStartConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = evaluation.load_fixture()
        for path, expected in ((ENGINE, cls.manifest['consumers']['engine_commit']),
                               (APP, cls.manifest['consumers']['app_commit'])):
            if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != expected:
                raise RuntimeError('Unselected starting-context consumer')
            if subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Starting-context consumers must be clean')
        for name, expected in (('Engine', cls.manifest['consumers']['engine_commit']),
                               ('Catalog', cls.manifest['consumers']['app_catalog_pin'])):
            actual = subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + name], text=True).strip()
            if actual != expected:
                raise RuntimeError('Unexpected committed App dependency: ' + name)
        cls.engine = Path(ENGINE).resolve() / 'IRGS_3_3'
        app = Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(cls.engine), str(CATALOG)
        sys.path[:0] = [str(app), str(cls.engine / 'runtime')]
        for name in ('server', 'gameplay_views', 'local_presentation', 'solo_provider', 'openai_proposals'):
            module = importlib.import_module(name)
            expected = app if name in ('server', 'gameplay_views', 'local_presentation') else cls.engine
            if not Path(module.__file__).resolve().is_relative_to(expected):
                raise RuntimeError('Another checkout is imported; run in a fresh process')
            setattr(cls, name, module)
        cls.reports = {}

    @classmethod
    def tearDownClass(cls):
        output = os.environ.get('IRGS_START_EVIDENCE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(cls.reports, indent=2) + '\n')

    start = http_helpers.IntegratedResponseConsumerTests.start
    stop = http_helpers.IntegratedResponseConsumerTests.stop
    http = http_helpers.IntegratedResponseConsumerTests.http

    def setUp(self):
        stack = ExitStack(); self.addCleanup(stack.close)
        self.dispatch = stack.enter_context(patch('solo_provider.CapabilityBroker.dispatch',
            side_effect=AssertionError('No inference in starting-context qualification')))
        self.transport = stack.enter_context(patch('openai_proposals.OpenAIProposalTransport.__call__',
            side_effect=AssertionError('No provider transport in starting-context qualification')))
        self.temp = stack.enter_context(tempfile.TemporaryDirectory(prefix='irgs-player-starts-'))
        self.store = self.server.Store(self.temp)
        self.local_presentation._catalog.cache_clear()
        self.addCleanup(self.local_presentation._catalog.cache_clear)
        self.start(); self.addCleanup(self.stop)
        self.inputs = {case: evaluation.export_actor_input(case) for case in evaluation.CASES}
        self.keys = {}

    def tearDown(self):
        self.dispatch.assert_not_called(); self.transport.assert_not_called()

    def call(self, path, body=None):
        code, result = self.http(path, body)
        self.assertEqual(code, 200, result)
        self.assertNotIn('PRIVATE_PLAYER_START_ORACLE', json.dumps(result))
        return result

    def create(self, case):
        selection = self.inputs[case]['selection']
        if selection['kind'] == 'rise':
            choices = json.loads((CATALOG / 'evaluation/solo_r00_v1/evaluator_only/setup.json').read_text())['choices']
            review = self.call('/api/rise/preview', {'choices': choices})
            body = {'name': 'Synthetic ' + case, 'choices': choices,
                'review_digest': review['review_digest'], 'request_id': 'start-create-' + case}
            created = self.call('/api/rise/create', body)
        else:
            preview = self.call('/api/historical-entry/hyw-1415')
            self.assertTrue(preview['ready'])
            fields = {k: selection[k] for k in ('profile_id', 'scenario_id', 'entry_id')}
            fields['snapshot_sha256'] = preview['snapshot_sha256']
            review = self.call('/api/starting-options?' + urlencode(fields))
            body = {**fields, 'name': 'Synthetic ' + case, 'character': selection['character'],
                'selection_digest': review['selection_digest'], 'request_id': 'start-create-' + case}
            created = self.call('/api/create', body)
        self.keys[case] = created['id']
        return review, body

    def view(self, case):
        return self.call('/api/playthrough/' + self.keys[case])

    def action(self, case, action, index):
        view = self.view(case)
        body = {'id': self.keys[case], 'actor': view['actor_id'], 'revision': view['revision'],
            'request_id': 'start-action-' + case + '-' + str(index)}
        if case == 'rise-r00':
            body['action'] = action
            path = '/api/rise/action'
        else:
            selected = next(row for row in view['supported_actions'] if row.get('action_id') == action)
            body.update(kind='scene_action', action_id=action, text=selected['text'])
            path = '/api/action'
        result = self.call(path, body)
        self.assertIn(result['status'], ('completed_successfully', 'completed_unsuccessfully'))
        self.assertEqual(result['actor'], body['actor'])
        self.assertTrue(result['receipt']['event_id'])
        self.assertEqual(result['presentation']['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
        self.assertTrue(result['presentation']['text'].startswith(result['outcome']['summary']))
        return path, body, result

    def assert_reload_replay(self, path, body, result):
        key = body['id']; before = self.store.path(key).read_bytes()
        self.stop(); self.start()
        self.assertEqual(self.call(path, body), result)
        lookup = '/api/action-result/' + key + '/' + body['request_id'] + '?actor_id=' + body['actor']
        self.assertEqual(self.call(lookup), result)
        reloaded = self.call('/api/playthrough/' + key)
        self.assertEqual(reloaded['revision'], self.store.read(key)['revision'])
        self.assertEqual(self.store.path(key).read_bytes(), before)

    def test_four_paths_report_loop_evidence_separately_from_unimplemented_readiness_and_date(self):
        for case in evaluation.CASES:
            review, _ = self.create(case)
            before = self.view(case)
            actor = before['actor_id']
            selection = self.inputs[case]['selection']
            eligible = case != 'john-1415-existing' or any(row['id'] == actor and row['eligible'] for row in review['characters'])
            self.assertTrue(eligible)
            actions = self.inputs[case]['actions']
            confirmed = received = reload = False
            if actions:
                path, body, result = self.action(case, actions[0], 0)
                confirmed = received = True
                self.assert_reload_replay(path, body, result); reload = True
            # No readiness API is invented for the historical baseline. R00 has
            # its existing explicit template/configuration review. Empty starts
            # are diagnostics below, never positive future acceptance criteria.
            context = bool(before['scene'].get('location'))
            civil = before.get('campaign_time', {})
            evidence = {'schema_version': 1, 'case_id': case,
                'explicit_mode': 'executable_slice' if case == 'rise-r00' else 'unclassified',
                'reference_ready': True, 'actor_eligible': bool(eligible),
                'mode_confirmed': case == 'rise-r00',
                'actor_context_reviewed': case == 'rise-r00' or bool(selection.get('character', {}).get('opening_id')),
                'actor_context_received': context,
                'supported_operation_listed': bool(before['supported_actions'] or before.get('settlement', {}).get('actions')),
                'operation_confirmed': confirmed, 'result_received': received,
                'save_reload_verified': reload, 'exact_retry_verified': reload,
                'civil_date_matches_source': civil.get('date') == '1415-08-11'
                    and civil.get('calendar') == 'julian' and civil.get('precision') == 'day' and civil.get('time') is None}
            assessment = evaluation.assess_evidence(evidence)
            self.reports[case] = {'evidence': evidence, 'assessment': assessment,
                'baseline_status': 'observed_gap' if not assessment['supported_start_accepted'] else 'reviewed_regression_loop',
                'future_acceptance': evaluation.load_evaluator_data()['cases'][case]['acceptance']}
            self.assertFalse(assessment['runtime_authorization_granted'])
            if actions:
                self.assertTrue(assessment['loop_verified'])

    def test_authored_new_character_real_five_action_arc_keeps_source_date_separate(self):
        case = 'new-1415-quay'; self.create(case)
        initial = copy.deepcopy(self.store.read(self.keys[case])['state']['campaign_time'])
        saved = []
        for index, action in enumerate(self.inputs[case]['actions']):
            saved.append(self.action(case, action, index))
        self.assertEqual([result['status'] for _, _, result in saved],
            ['completed_successfully', 'completed_unsuccessfully'] + ['completed_successfully'] * 3)
        self.assertEqual([result['elapsed_time']['duration_seconds'] for _, _, result in saved], [20, 30, 45, 45, 10])
        state = self.store.read(self.keys[case])['state']; actor = self.view(case)['actor_id']
        self.assertEqual(state['stocks'][actor]['sealed_dispatch'], 0)
        self.assertEqual(state['stocks']['clerk-tray']['sealed_dispatch'], 1)
        self.assertEqual(state['elapsed_time']['seconds'], 150)
        self.assertEqual(state['campaign_time'], initial)
        for path, body, result in saved:
            self.assert_reload_replay(path, body, result)

    def test_r00_real_regression_finishes_finite_work_and_reloads(self):
        case = 'rise-r00'; self.create(case)
        for index, action in enumerate(self.inputs[case]['actions']):
            path, body, result = self.action(case, action, index)
        state = self.store.read(self.keys[case])['state']
        self.assertEqual(state['elapsed_time']['seconds'], 3900)
        self.assertEqual(state['projects']['shelter']['worked'], 3600)
        self.assertEqual(state['stocks']['founder-home']['timber'], 3)
        self.assert_reload_replay(path, body, result)

    def test_unbound_own_response_is_retained_without_invented_effects_or_elapsed_time(self):
        for case in ('john-1415-existing', 'new-1415-default'):
            self.create(case); view = self.view(case)
            initial = copy.deepcopy(self.store.read(self.keys[case])['state'])
            body = {'id': self.keys[case], 'actor': view['actor_id'], 'revision': view['revision'],
                'request_id': 'start-intent-' + case, 'declaration': self.inputs[case]['declaration']}
            result = self.call('/api/declaration', body)
            self.assertEqual(result['status'], 'declared_not_resolved')
            after = self.store.read(self.keys[case])['state']
            for field in ('stocks', 'opening_stock', 'actors', 'knowledge', 'campaign_time', 'elapsed_time'):
                self.assertEqual(after.get(field), initial.get(field))
            self.assert_reload_replay('/api/declaration', body, result)
            pending = self.view(case)
            self.call('/api/withdraw-declaration', {'id': body['id'], 'actor': body['actor'],
                'revision': pending['revision'], 'request_id': 'start-withdraw-' + case,
                'action_request_id': body['request_id']})
            self.assertEqual(self.view(case)['supported_actions'], view['supported_actions'])

    def test_private_stock_or_hidden_permission_does_not_select_a_winning_menu(self):
        for case in evaluation.CASES:
            self.create(case); before = self.view(case)
            record = self.store.read(self.keys[case])
            account = 'oren-home' if case == 'rise-r00' else 'PRIVATE_PLAYER_START_ORACLE'
            stock = record['state']['stocks'].setdefault(account, {})
            stock['timber'] = stock.get('timber', 0) + 999
            record['state']['opening_stock']['timber'] = record['state']['opening_stock'].get('timber', 0) + 999
            if case == 'rise-r00':
                record['state']['grants']['founding']['active'] = False
            self.store.write(record)
            after = self.view(case)
            self.assertEqual(after['supported_actions'], before['supported_actions'])
            self.assertEqual(after['process_control']['start_options'], before['process_control']['start_options'])
            self.assertNotIn('PRIVATE_PLAYER_START_ORACLE', json.dumps(after))

    def test_historical_person_cannot_be_given_new_human_fictional_courier_circumstances(self):
        case = 'john-1415-existing'; _, body = self.create(case)
        before = self.store.path(self.keys[case]).read_bytes()
        forged = copy.deepcopy(body)
        forged['request_id'] = 'forged-existing-courier'
        forged['character']['opening_id'] = 'quay-delivery-v1'
        code, _ = self.http('/api/create', forged)
        self.assertEqual(code, 400)
        self.assertEqual(len(self.store.listing()), 1)
        self.assertEqual(self.store.path(self.keys[case]).read_bytes(), before)

    def test_dossier_binds_actual_adopted_claims_and_catalog_description_reaches_app(self):
        dossier = json.loads((CATALOG / evaluation.FIXTURE / 'requirements/john_1415.json').read_text())
        path = Path(ENGINE) / dossier['source']['path']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), dossier['source']['sha256'])
        doc = json.loads(path.read_bytes())
        for claim in dossier['reference_claims']:
            value = doc
            for key in claim['pointer'].strip('/').split('/'):
                value = value[int(key)] if isinstance(value, list) else value[key]
            self.assertIn('HYW-SRC-APRIL-COUNCIL' if claim['id'] != 'eligibility'
                else 'authored-solo-individual-policy-v1', json.dumps(value))
        library = self.call('/api/content-library')
        record = next(row for row in library['portfolio']['entries'] if row['catalogue_id'] == 'MC-01')
        self.assertIn('reference checkpoints', record['period'])
        self.assertIn('do not establish an executable start', record['readiness']['verification'])
        self.assertFalse(record['readiness']['full_campaign_ready'])
        self.assertEqual(library['portfolio']['counts']['total'], 44)


if __name__ == '__main__':
    unittest.main()
