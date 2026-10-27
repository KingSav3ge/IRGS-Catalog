"""Catalog's independent HTTP checks against the exact 3.4.3 communication bridge."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from urllib.parse import urlencode

from tools.tests import test_integrated_response_consumers as base
import alpha_context_evaluation as evaluation

ENGINE = os.environ.get('IRGS_ALPHA_ENGINE_SOURCE')
APP = os.environ.get('IRGS_ALPHA_APP_SOURCE')


@unittest.skipUnless(ENGINE and APP, 'Exact Alpha baseline Engine/App roots required')
class AlphaCommunicationConsumers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        consumers = evaluation.load_fixture()['consumers']
        for path, commit in ((ENGINE, consumers['engine_commit']), (APP, consumers['app_commit'])):
            if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != commit:
                raise RuntimeError('Unselected Alpha baseline')
            if subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Consumer sources must be clean')
        for component, commit in (('Engine', consumers['engine_commit']), ('Catalog', consumers['app_catalog_pin'])):
            if subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + component], text=True).strip() != commit:
                raise RuntimeError('App dependency mismatch')
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(base.CATALOG)
        sys.path[:0] = [str(app / 'tests'), str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures',
                     'starting_selection', 'settlement_setup', 'historical_campaigns', 'core_world',
                     'offline_responses', 'scene_actions', 'solo_provider', 'response_depot', 'openai_proposals'):
            module = importlib.import_module(name)
            expected = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures') else engine
            if not Path(module.__file__).resolve().is_relative_to(expected):
                raise RuntimeError('Wrong source imported; run in a fresh process')
            setattr(cls, name, module)
        cls.contract = base.compatibility.original.load_fixture()

    setUp = base.IntegratedResponseConsumerTests.setUp
    tearDown = base.IntegratedResponseConsumerTests.tearDown
    start = base.IntegratedResponseConsumerTests.start
    stop = base.IntegratedResponseConsumerTests.stop
    http = base.IntegratedResponseConsumerTests.http
    view = base.IntegratedResponseConsumerTests.view
    assert_private_free = base.IntegratedResponseConsumerTests.assert_private_free

    def participant_view(self, key, actor):
        code, result = self.http('/api/playthrough/' + key + '?actor_id=' + actor)
        self.assertEqual(code, 200, result)
        return result

    def prepare(self, key, actor, recipient, channel, command, details, words):
        view = self.participant_view(key, actor)
        body = {'id': key, 'actor': actor, 'revision': view['revision'],
            'view_token': view['communication_control']['view_token'], 'request_id': uuid.uuid4().hex,
            'channel_id': channel, 'recipient': recipient, 'command': command, 'details': details, 'intention': words}
        before = self.store.path(key).read_bytes()
        code, packet = self.http('/api/communication/prepare', body)
        self.assertEqual(code, 200, packet)
        self.assertEqual(packet['intention'], words)
        self.assertEqual(self.store.path(key).read_bytes(), before)
        return body

    def execute(self, body, accepted=True):
        data = {k: body[k] for k in ('id', 'actor', 'request_id')}; data['explicitly_accepted'] = accepted
        return self.http('/api/communication/execute', data)

    def test_ordinary_creation_reports_actual_communication_availability(self):
        code, entry = self.http('/api/historical-entry/hyw-1415'); self.assertEqual(code, 200)
        selected = {'profile_id': 'military', 'scenario_id': 'hundred-years-war', 'entry_id': 'hyw-1415',
            'snapshot_sha256': entry['snapshot_sha256']}
        code, options = self.http('/api/starting-options?' + urlencode(selected)); self.assertEqual(code, 200)
        review = {**selected, 'selection_digest': options['selection_digest'], 'starting_scenario_id': 'individual',
                  'character_kind': 'new', 'species': 'human', 'opening_id': 'quay-delivery-v1'}
        code, preview = self.http('/api/starting-preview?' + urlencode(review))
        self.assertEqual(code, 200, preview); self.assertEqual(preview['status'], 'supported_slice')
        body = {**selected, 'name': 'Synthetic ordinary quay', 'starting_scenario_id': 'individual',
            'selection_digest': options['selection_digest'], 'request_id': 'alpha-ordinary-quay',
            'character': {'kind': 'new', 'name': 'Synthetic courier', 'species': 'human',
                          'background': '', 'opening_id': 'quay-delivery-v1'}}
        code, quay = self.http('/api/create', body); self.assertEqual(code, 200, quay)
        choices = json.loads((base.CATALOG / 'evaluation/solo_r00_v1/evaluator_only/setup.json').read_text())['choices']
        code, review = self.http('/api/rise/preview', {'choices': choices}); self.assertEqual(code, 200, review)
        code, rise = self.http('/api/rise/create', {'name': 'Synthetic ordinary Rise', 'choices': choices,
            'review_digest': review['review_digest'], 'request_id': 'alpha-ordinary-rise'})
        self.assertEqual(code, 200, rise)
        for key in (quay['id'], rise['id']):
            before = self.store.path(key).read_bytes()
            code, view = self.http('/api/playthrough/' + key); self.assertEqual(code, 200, view)
            packet = view['communication_control']
            self.assertEqual(packet['schema_version'], 'irgs-communication-capabilities-1')
            self.assertEqual(packet['channels'], [])
            self.assertEqual(self.store.path(key).read_bytes(), before)

    def test_candidate_dossier_sources_are_exact_published_engine_bytes(self):
        expected = {
            'data/hyw_1415_opening.json': 'eb182aef5f15ad199e8a54a8d9a7c6890b78ae26631c0125d04f6bb58dc43f34',
            'data/solo_quay_opening.json': '6af64700fc4fd23193a1bd9df2a8b4e8ef8aca6a0a6471939df86cc4bf11a8f5',
            'runtime/settlement_setup.py': 'd942b135ba8eac8f0a6d3b160f36a146219f399da8a7035e095f12c599566f27',
            'runtime/settlement_runtime.py': '77703de381e8b4e8724d9fdde4b502b50da9bb3f8948f03cf4da3f0e87c9915b',
        }
        for name, sha in expected.items():
            self.assertEqual(hashlib.sha256((Path(ENGINE) / 'IRGS_3_3' / name).read_bytes()).hexdigest(), sha)

    def test_selected_fixture_speech_preserves_testimony_acceptance_and_recovery(self):
        key = self.app_communication_fixtures.install(self.store)['quay']
        view = self.participant_view(key, 'pc'); channel = view['communication_control']['channels'][0]
        self.assertEqual([p['actor_id'] for p in channel['participants']], ['witness'])
        self.assertNotIn('PRIVATE_CHANNEL_ROSTER', json.dumps(view))
        text = '  I accept.\nOnly my exact testimony.  '
        body = self.prepare(key, 'pc', 'witness', 'quay', 'speak', {}, text)
        before = self.store.path(key).read_bytes()
        self.assertEqual(self.execute(body, False)[0], 400)
        self.assertEqual(self.store.path(key).read_bytes(), before)
        code, result = self.execute(body); self.assertEqual(code, 200, result)
        self.assertEqual(result['communication']['utterance'], text)
        self.assertEqual(result['communication']['truth_status'], 'testimony')
        self.assertEqual(result['communication']['status'], 'testimony_received')
        self.assertIsNone(result['elapsed_time'])
        self.assertEqual(result['presentation']['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
        saved = self.store.path(key).read_bytes(); self.stop(); self.start()
        self.assertEqual(self.execute(body), (200, result))
        self.assertEqual(self.store.path(key).read_bytes(), saved)

    def test_selected_fixture_offer_refusal_consent_and_competing_retries(self):
        key = self.app_communication_fixtures.install(self.store)['rise']
        terms = {'from': 'founder-home', 'to': 'oren-home', 'material': 'grain', 'quantity': 2,
                 'authority_id': 'founder-custody'}
        original = copy.deepcopy(self.store.read(key)['state']['stocks'])
        body = self.prepare(key, 'founder', 'oren', 'local', 'offer', {'terms': terms}, 'I propose these terms.')
        code, offered = self.execute(body); self.assertEqual(code, 200, offered)
        self.assertEqual(offered['communication']['status'], 'offered')
        self.assertEqual(offered['communication']['terms'], terms)
        self.assertEqual(self.store.read(key)['state']['stocks'], original)
        details = {'offer_id': offered['communication']['offer_id'], 'terms_digest': offered['communication']['terms_digest']}
        refused = self.prepare(key, 'oren', 'founder', 'local', 'decline', details, 'I decline.')
        code, result = self.execute(refused); self.assertEqual(code, 200, result)
        self.assertEqual(result['communication']['status'], 'declined')
        self.assertEqual(self.store.read(key)['state']['stocks'], original)
        body = self.prepare(key, 'founder', 'oren', 'local', 'offer', {'terms': terms}, 'A second offer.')
        code, offered = self.execute(body); self.assertEqual(code, 200, offered)
        details = {'offer_id': offered['communication']['offer_id'], 'terms_digest': offered['communication']['terms_digest']}
        accepted = self.prepare(key, 'oren', 'founder', 'local', 'accept', details, 'I accept these terms.')
        competitor = self.prepare(key, 'oren', 'founder', 'local', 'accept', details, 'I separately accept these terms.')
        forged = {**accepted, 'actor': 'elin', 'request_id': uuid.uuid4().hex}
        before = self.store.path(key).read_bytes()
        self.assertIn(self.http('/api/communication/prepare', forged)[0], (400, 403))
        self.assertEqual(self.store.path(key).read_bytes(), before)
        with ThreadPoolExecutor(2) as pool:
            replies = list(pool.map(self.execute, (accepted, competitor)))
        self.assertEqual(sorted(code for code, _ in replies), [200, 400])
        winner = accepted if replies[0][0] == 200 else competitor
        result = next(result for code, result in replies if code == 200)
        self.assertEqual(result['communication']['status'], 'fulfilled')
        with ThreadPoolExecutor(2) as pool:
            duplicates = list(pool.map(lambda _: self.execute(winner), range(2)))
        self.assertEqual(duplicates, [(200, result), (200, result)])
        stocks = self.store.read(key)['state']['stocks']
        self.assertEqual(stocks['founder-home']['grain'], original['founder-home']['grain'] - 2)
        self.assertEqual(stocks['oren-home']['grain'], original['oren-home']['grain'] + 2)
        self.assertEqual(sum(row.get('grain', 0) for row in stocks.values()), sum(row.get('grain', 0) for row in original.values()))
        self.assertEqual(self.http('/api/action-result/' + key + '/' + body['request_id'] + '?actor_id=founder'), (200, offered))

    def test_adopted_henry_start_receives_initial_day_and_exact_observation(self):
        code, entry = self.http('/api/historical-entry/hyw-1415'); self.assertEqual(code, 200)
        fields = {'profile_id': 'military', 'scenario_id': 'hundred-years-war', 'entry_id': 'hyw-1415',
                  'snapshot_sha256': entry['snapshot_sha256']}
        code, options = self.http('/api/starting-options?' + urlencode(fields)); self.assertEqual(code, 200)
        common = {**fields, 'selection_digest': options['selection_digest'], 'starting_scenario_id': 'individual'}
        character = {'kind': 'existing', 'actor_id': 'HYW-HENRY-V', 'opening_id': 'henry-1415-embarkation-v1'}
        code, preview = self.http('/api/starting-preview?' + urlencode({**common, 'character_kind': 'existing',
            'actor_id': character['actor_id'], 'opening_id': character['opening_id']}))
        self.assertEqual(code, 200, preview); self.assertEqual(preview['status'], 'supported_slice')
        code, created = self.http('/api/create', {**common, 'name': 'Synthetic Henry', 'character': character,
            'request_id': 'alpha-henry-create'}); self.assertEqual(code, 200, created)
        key = created['id']; code, view = self.http('/api/playthrough/' + key); self.assertEqual(code, 200)
        civil = view['start_context']['civil_time']
        self.assertEqual((civil['date'], civil['calendar'], civil['precision']), ('1415-08-11', 'julian', 'day'))
        self.assertIsNone(civil['opening_hour']); self.assertFalse(civil['current_calendar_binding'])
        action = next(row for row in view['supported_actions'] if row['action_id'] == 'observe-embarkation')
        body = {'id': key, 'actor': character['actor_id'], 'revision': view['revision'], 'kind': 'scene_action',
            'action_id': action['action_id'], 'text': action['text'], 'request_id': 'alpha-henry-observe'}
        code, result = self.http('/api/action', body); self.assertEqual(code, 200, result)
        self.assertEqual(result['elapsed_time']['duration_seconds'], 20)
        self.assertTrue(result['presentation']['text'].startswith(result['outcome']['summary']))
        state = self.store.read(key)['state']; self.assertEqual(state['stocks'], {})
        before = self.store.path(key).read_bytes(); self.stop(); self.start()
        self.assertEqual(self.http('/api/action', body), (200, result))
        self.assertEqual(self.store.path(key).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
