"""Real partial multi-session journeys; unsupported Alpha requirements remain open."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode

from tools.tests import test_alpha_communication_consumers as alpha
import alpha_journey_evaluation as evaluation

ENGINE = os.environ.get('IRGS_JOURNEY_ENGINE_SOURCE')
APP = os.environ.get('IRGS_JOURNEY_APP_SOURCE')


class AlphaJourneyConsumers(alpha.AlphaCommunicationConsumers):
    __unittest_skip__ = not bool(ENGINE and APP)
    __unittest_skip_why__ = 'Exact journey Engine/App candidate roots required'
    # The old baseline's source-hash test belongs to its own exact selection.
    test_candidate_dossier_sources_are_exact_published_engine_bytes = None

    @classmethod
    def setUpClass(cls):
        contract = evaluation.load_fixture()['consumers']
        for path, sha in ((ENGINE, contract['engine_candidate']), (APP, contract['app_commit'])):
            if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != sha:
                raise RuntimeError('Unexpected journey candidate revision')
            if subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Journey candidate sources must be clean')
        for name, sha in (('Engine', contract['app_engine_pin']), ('Catalog', contract['app_catalog_pin'])):
            if subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + name], text=True).strip() != sha:
                raise RuntimeError('Unexpected committed App pin')
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(alpha.base.CATALOG)
        sys.path[:0] = [str(app / 'tests'), str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures',
                     'starting_selection', 'settlement_setup', 'historical_campaigns', 'core_world',
                     'offline_responses', 'scene_actions', 'solo_provider', 'response_depot', 'openai_proposals'):
            module = importlib.import_module(name)
            root = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures') else engine
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Imported another checkout; use a fresh process')
            setattr(cls, name, module)
        cls.contract = alpha.base.compatibility.original.load_fixture()
        cls.reports = {}

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('IRGS_JOURNEY_EVIDENCE_OUTPUT'):
            Path(os.environ['IRGS_JOURNEY_EVIDENCE_OUTPUT']).write_text(json.dumps(cls.reports, indent=2) + '\n')

    def ok(self, path, body=None):
        code, result = self.http(path, body)
        self.assertEqual(code, 200, result)
        self.assertNotIn('PRIVATE_JOURNEY_ORACLE', json.dumps(result))
        return result

    def evidence(self, case, receipts, retry, restore):
        doc = {'case_id': case, 'engine_commit': 'ea0631b8fbf94f425fa003d81b6907445a9a43c5',
            'app_commit': 'b3a53cfd11bbd3745253520b4e8ed6718c826ab8',
            'app_engine_pin': 'efc84364b86e640f5028bfac2dfd5ae3021695a9', 'sessions': 2,
            'receipt_ids': receipts, 'retry_verified': retry, 'restore_verified': restore,
            'pending_requirements': list(evaluation.REQUIRED), 'alpha_qualified': False}
        self.assertFalse(evaluation.assess_evidence(doc)['runtime_execution_verified_by_schema'])
        self.reports[case] = doc

    def action(self, key, actor, action, index, *, rise=False):
        view = self.ok('/api/playthrough/' + key + '?actor_id=' + actor)
        body = {'id': key, 'actor': actor, 'revision': view['revision'], 'request_id': 'journey-' + str(index)}
        if rise:
            path = '/api/rise/action'; body['action'] = action
        else:
            path = '/api/action'; choice = next(row for row in view['supported_actions'] if row['action_id'] == action)
            body.update(kind='scene_action', action_id=action, text=choice['text'])
        result = self.ok(path, body)
        self.assertEqual(result['presentation']['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
        self.assertTrue(result['presentation']['text'].startswith(result['outcome']['summary']))
        return path, body, result

    def restore_identical(self, key):
        revision = self.store.read(key)['revision']; before = self.store.path(key).read_bytes()
        self.ok('/api/delete', {'id': key, 'revision': revision})
        self.ok('/api/restore', {'id': key, 'revision': revision})
        self.assertEqual(self.store.path(key).read_bytes(), before)

    def test_quay_contact_real_review_speech_failure_alternate_delivery_and_resume(self):
        actor_input = evaluation.export_actor_input('quay-contact')
        oracle = evaluation.load_evaluator_data()['cases']['quay-contact']
        entry = self.ok('/api/historical-entry/hyw-1415')
        fields = {'profile_id': 'military', 'scenario_id': 'hundred-years-war', 'entry_id': 'hyw-1415',
            'snapshot_sha256': entry['snapshot_sha256']}
        options = self.ok('/api/starting-options?' + urlencode(fields))
        opening = actor_input['selection']['opening_id']
        self.assertTrue(next(row for row in options['playable_openings'] if row['id'] == opening)['fictional'])
        preview = self.ok('/api/starting-preview?' + urlencode({**fields, 'selection_digest': options['selection_digest'],
            'starting_scenario_id': 'individual', 'character_kind': 'new', 'species': 'human', 'opening_id': opening}))
        self.assertEqual(preview['status'], 'supported_slice')
        body = {**fields, 'name': 'Synthetic journey', 'request_id': 'journey-create-quay',
            'selection_digest': options['selection_digest'], 'character': {'kind': 'new', 'name': 'Synthetic courier',
                'species': 'human', 'background': '', 'opening_id': opening}}
        created = self.ok('/api/create', body); key = created['id']
        before = self.store.path(key).read_bytes(); self.assertEqual(self.ok('/api/create', body)['id'], key)
        self.assertEqual(self.store.path(key).read_bytes(), before)
        view = self.ok('/api/playthrough/' + key); actor = view['actor_id']
        channel = view['communication_control']['channels'][0]
        self.assertEqual([p['actor_id'] for p in channel['participants']], ['FICTIONAL-QUAY-CONTACT'])
        words = '  Please tell me what you know.\nNo response or consent is assumed.  '
        speech = self.prepare(key, actor, 'FICTIONAL-QUAY-CONTACT', 'quay-local', 'speak', {}, words)
        self.assertEqual(self.execute(speech, False)[0], 400)
        code, result = self.execute(speech); self.assertEqual(code, 200, result)
        self.assertEqual(result['communication']['utterance'], words)
        self.assertEqual(result['communication']['truth_status'], 'testimony')
        self.assertEqual(result['communication']['status'], oracle['speech_status'])
        self.assertIsNone(result['elapsed_time'])
        original_calendar = self.store.read(key)['state']['campaign_time']
        initial_choices = self.ok('/api/playthrough/' + key)['supported_actions']
        self.assertNotIn('passage-desk', {row['action_id'] for row in initial_choices})
        actions = actor_input['actions'][1:]; saved = []
        for index, action in enumerate(actions[:2]):
            saved.append(self.action(key, actor, action, index))
        self.assertEqual(saved[-1][2]['status'], oracle['shortcut_status'])
        self.stop(); self.start()
        self.assertEqual(self.execute(speech), (200, result))
        for index, action in enumerate(actions[2:], start=2):
            saved.append(self.action(key, actor, action, index))
        self.assertEqual(saved[-1][2]['status'], oracle['second_delivery'])
        state = self.store.read(key)['state']; self.assertEqual(state['elapsed_time']['seconds'], oracle['elapsed_seconds'])
        self.assertEqual(state['campaign_time'], original_calendar)
        self.assertEqual(state['stocks'][actor]['sealed_dispatch'], oracle['dispatch_actor'])
        self.assertEqual(state['stocks']['clerk-tray']['sealed_dispatch'], oracle['dispatch_tray'])
        view = self.ok('/api/playthrough/' + key); revision = view['revision']; raw = self.store.path(key).read_bytes()
        forged = {**saved[-1][1], 'actor': 'foreign', 'request_id': 'journey-forged', 'revision': revision}
        self.assertIn(self.http('/api/action', forged)[0], (400, 403)); self.assertEqual(self.store.path(key).read_bytes(), raw)
        self.restore_identical(key)
        restored = self.store.path(key).read_bytes()
        for path, request, original in saved:
            self.assertEqual(self.http(path, request), (200, original))
        self.assertEqual(self.execute(speech), (200, result))
        self.assertEqual(self.store.path(key).read_bytes(), restored)
        self.evidence('quay-contact', [result['receipt']['event_id']] + [r['receipt']['event_id'] for _, _, r in saved], True, True)

    def test_r00_real_review_work_sessions_and_identical_restore(self):
        oracle = evaluation.load_evaluator_data()['cases']['rise-r00']
        choices = json.loads((alpha.base.CATALOG / 'evaluation/solo_r00_v1/evaluator_only/setup.json').read_text())['choices']
        preview = self.ok('/api/rise/preview', {'choices': choices})
        created = self.ok('/api/rise/create', {'name': 'Synthetic R00 journey', 'choices': choices,
            'review_digest': preview['review_digest'], 'request_id': 'journey-create-rise'})
        key = created['id']; actions = evaluation.export_actor_input('rise-r00')['actions']; saved = []
        for index, action in enumerate(actions):
            saved.append(self.action(key, 'founder', action, index, rise=True))
            if index == 2:
                self.stop(); self.start()
        state = self.store.read(key)['state']; self.assertEqual(state['elapsed_time']['seconds'], oracle['elapsed_seconds'])
        self.assertEqual(state['projects']['shelter']['worked'], oracle['shelter_work_seconds'])
        self.assertEqual(state['stocks']['founder-home']['timber'], oracle['founder_timber'])
        self.restore_identical(key)
        restored = self.store.path(key).read_bytes()
        for path, request, original in saved:
            self.assertEqual(self.http(path, request), (200, original))
        self.assertEqual(self.store.path(key).read_bytes(), restored)
        self.evidence('rise-r00', [r['receipt']['event_id'] for _, _, r in saved], True, True)


if __name__ == '__main__':
    import unittest
    unittest.main()
