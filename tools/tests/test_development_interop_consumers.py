"""Current development heads and the App's pinned Engine remain distinct cases."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from tools.tests import test_integrated_response_consumers as integrated

import development_interop_compatibility as compatibility

ENGINE = os.environ.get('IRGS_INTEROP_ENGINE_SOURCE')
APP = os.environ.get('IRGS_INTEROP_APP_SOURCE')
ROLE = os.environ.get('IRGS_INTEROP_ENGINE_ROLE')


class DevelopmentInteropConsumerTests(integrated.IntegratedResponseConsumerTests):
    __unittest_skip__ = not bool(ENGINE and APP and ROLE)
    __unittest_skip_why__ = 'Exact development interoperability sources and Engine role required'

    @classmethod
    def setUpClass(cls):
        cls.matrix = compatibility.load_contract()
        cls.followup = compatibility.baseline.load_contract()
        cls.contract = compatibility.baseline.original.load_fixture()
        consumers = cls.matrix['consumers']
        if ROLE not in consumers['engine_commits']:
            raise RuntimeError('Unselected Engine role')
        for source, expected in [(ENGINE, consumers['engine_commits'][ROLE]), (APP, consumers['app_commit'])]:
            if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != expected:
                raise RuntimeError('Unselected development interoperability commit')
            if subprocess.check_output(['git', '-C', source, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Interoperability dependencies must be clean')
        for component, expected in [('Engine', consumers['app_engine_pin']), ('Catalog', consumers['app_catalog_pin'])]:
            actual = subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + component], text=True).strip()
            if actual != expected:
                raise RuntimeError('Unexpected committed App pointer: ' + component)
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(integrated.CATALOG)
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'process_bridge',
                     'starting_selection', 'settlement_setup', 'historical_campaigns', 'core_world',
                     'offline_responses', 'scene_actions', 'solo_provider', 'response_depot',
                     'openai_proposals', 'process_runtime'):
            module = importlib.import_module(name)
            root = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'process_bridge') else engine
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Imported another consumer checkout; use a fresh process')
            setattr(cls, name, module)

    def install_received_processes(self):
        # Trusted synthetic initialization via existing typed Engine APIs.
        # No App process-start endpoint, rule discovery or user save is involved.
        self.act('rise', 0)
        body = self.body('rise', {'action_id': 'found', 'request_id': 'interop-fixture-found'})
        code, result = self.http('/api/rise/action', body)
        self.assertEqual((code, result['status']), (200, 'completed_successfully'))
        self.stop()
        for context, key in self.keys.items():
            record = self.store.read(key)
            world = self.core_world.CoreWorld(state=record['state'])
            actor = self.gameplay_views.controlled_actor(record['state'])
            request = self.process_runtime.prepare(world, phase_id='fixture-start-' + context,
                process_id='interop-process-' + context, actor=actor, command='start',
                details={'kind': 'work' if context == 'rise' else 'observation',
                         'action_id': 'build' if context == 'rise' else 'look-quay'},
                intention='Explicit synthetic interop process setup', source_ref='synthetic-interop-setup',
                branch_id=key, restore_id='fixture-initialization')

            def persist(expected, candidate, received):
                if expected != request.scope:
                    raise RuntimeError('Synthetic fixture scope mismatch')
                record['state'] = json.loads(candidate)
                self.store.write(record)

            self.process_runtime.execute(world, request, current_scope=request.scope,
                persist=persist, explicitly_accepted=True)
        self.start()

    def phase(self, context, command, details=None):
        view = self.view(context)
        self.assertFalse(view['process_control']['start_available'])
        before = self.store.path(self.keys[context]).read_bytes()
        body = {'id': self.keys[context], 'actor': view['actor_id'], 'revision': view['revision'],
            'view_token': view['process_control']['view_token'],
            'request_id': 'interop-' + command + '-' + str(view['revision']),
            'process_id': 'interop-process-' + context, 'command': command, 'details': details or {},
            'intention': '  Explicit interop ' + command + '.\nOnly the reviewed command.  '}
        code, prepared = self.http('/api/process/prepare', body)
        self.assertEqual(code, 200, prepared)
        self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)
        acceptance = {k: body[k] for k in ('id', 'actor', 'request_id')}
        self.assertEqual(self.http('/api/process/execute', {**acceptance, 'explicitly_accepted': False})[0], 400)
        self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)
        code, result = self.http('/api/process/execute', {**acceptance, 'explicitly_accepted': True})
        self.assertEqual(code, 200, result)
        self.assertEqual(result['process']['phase_id'], prepared['phase_id'])
        self.assertEqual(result['process']['phase_intention'], body['intention'])
        self.assertEqual(result['presentation']['render_usage'], integrated.USAGE)
        self.assertEqual(result['presentation']['catalog_library']['id'], 'irgs-response-depot-v1')
        facts = self.receipt_facts(context, result)
        exact = facts['packets']['receipt.exact']['receipt_text']
        self.assertTrue(result['presentation']['text'].startswith(exact))
        self.assert_private_free(result)
        self.assertEqual(self.view(context)['completed_actions'][-1]['presentation'], result['presentation'])
        return body, result

    def test_received_non_rise_observation_keeps_exact_completion_and_catalog_presentation(self):
        self.install_received_processes()
        key = self.keys['quay']
        initial_evidence = self.store.read(key)['state']['evidence']
        _, partial = self.phase('quay', 'advance', {'seconds': 1})
        self.assertEqual(partial['process']['worked_seconds'], 1)
        self.assertEqual(partial['process']['status'], 'active')
        self.assertEqual(self.store.read(key)['state']['evidence'], initial_evidence)
        self.phase('quay', 'pause')
        self.phase('quay', 'resume')
        body, done = self.phase('quay', 'advance', {'seconds': 999})
        self.assertEqual(done['process']['status'], 'completed')
        self.assertEqual(done['process']['worked_seconds'], 20)
        self.assertEqual(self.store.read(key)['state']['elapsed_time']['seconds'], 20)
        self.assertNotEqual(self.store.read(key)['state']['evidence'], initial_evidence)
        saved = self.store.path(key).read_bytes()
        self.assertEqual(self.lookup('quay', body), (200, done))
        self.assertEqual(self.store.path(key).read_bytes(), saved)

    def test_received_rise_work_zero_span_and_saved_phase_survive_restart_and_retry(self):
        self.install_received_processes()
        _, partial = self.phase('rise', 'advance', {'seconds': 100})
        self.assertEqual(partial['process']['worked_seconds'], 100)
        for command in ('pause', 'resume'):
            _, result = self.phase('rise', command)
            self.assertEqual(result['process']['elapsed_seconds'], 0)
            self.assertEqual(result['process']['worked_seconds'], 100)
        for _ in range(3):
            body, result = self.phase('rise', 'advance', {'seconds': 3600})
            if result['process']['status'] == 'completed':
                break
        self.assertEqual(result['process']['status'], 'completed')
        state = self.store.read(self.keys['rise'])['state']
        self.assertEqual(state['projects']['shelter']['worked'], 3600)
        saved = self.store.path(self.keys['rise']).read_bytes()
        self.stop()
        self.start()
        acceptance = {k: body[k] for k in ('id', 'actor', 'request_id')}
        self.assertEqual(self.http('/api/process/execute', {**acceptance, 'explicitly_accepted': True}), (200, result))
        self.assertEqual(self.lookup('rise', body), (200, result))
        self.assertEqual(self.store.path(self.keys['rise']).read_bytes(), saved)


if __name__ == '__main__':
    import unittest
    unittest.main()
