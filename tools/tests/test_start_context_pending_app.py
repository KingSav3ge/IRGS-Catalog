"""Known App adoption gaps are diagnostics, never successful product acceptance."""
from contextlib import ExitStack
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

from tools.tests import test_integrated_response_consumers as helpers
import start_context_evaluation as evaluation

ENGINE = os.environ.get('IRGS_CONTEXT_ENGINE_SOURCE')
APP = os.environ.get('IRGS_CONTEXT_PENDING_APP_SOURCE')
PENDING_APP = 'd8e68848454ac7be68ce87fede6d04cc57bda86a'


@unittest.skipUnless(ENGINE and APP, 'Exact Engine and pending App snapshots required for gap diagnostics')
class PendingAppStartDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for root, commit in ((ENGINE, evaluation.ENGINE_COMMIT), (APP, PENDING_APP)):
            if subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip() != commit:
                raise RuntimeError('Unselected pending-App diagnostic revision')
            if subprocess.check_output(['git', '-C', root, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Pending-App diagnostic sources must be clean')
        for name, commit in (('Engine', '91b20056e7db651966c9e92925313494917f47b1'),
                             ('Catalog', '3f921252e50a0976cb88321b6ff8249a5f12466d')):
            if subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + name], text=True).strip() != commit:
                raise RuntimeError('Unexpected old App pointer')
        engine, app = Path(ENGINE).resolve(), Path(APP).resolve()
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine / 'IRGS_3_3'), str(helpers.CATALOG)
        sys.path[:0] = [str(app / 'IRGS_Web'), str(engine / 'IRGS_3_3/runtime')]
        for name in ('server', 'start_preview', 'start_readiness', 'solo_provider', 'openai_proposals'):
            module = importlib.import_module(name)
            root = app if name in ('server', 'start_preview') else engine
            if not Path(module.__file__).resolve().is_relative_to(root):
                raise RuntimeError('Import escaped selected diagnostic sources')
            setattr(cls, name, module)
        cls.observations = {'status': 'adopted_app_acceptance_not_executed', 'app_commit': PENDING_APP,
            'engine_override': evaluation.ENGINE_COMMIT, 'app_pins_updated': False}

    @classmethod
    def tearDownClass(cls):
        output = os.environ.get('IRGS_CONTEXT_APP_DIAGNOSTIC_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(cls.observations, indent=2) + '\n')

    start = helpers.IntegratedResponseConsumerTests.start
    stop = helpers.IntegratedResponseConsumerTests.stop
    http = helpers.IntegratedResponseConsumerTests.http

    def setUp(self):
        stack = ExitStack(); self.addCleanup(stack.close)
        self.temp = stack.enter_context(tempfile.TemporaryDirectory(prefix='irgs-start-pending-app-'))
        self.guards = [stack.enter_context(patch(name, side_effect=AssertionError('No provider in diagnostics')))
            for name in ('solo_provider.CapabilityBroker.dispatch', 'openai_proposals.OpenAIProposalTransport.__call__')]
        self.store = self.server.Store(self.temp)
        self.start(); self.addCleanup(self.stop)
        code, preview = self.http('/api/historical-entry/hyw-1415'); self.assertEqual(code, 200)
        self.fields = {'profile_id': 'military', 'scenario_id': 'hundred-years-war', 'entry_id': 'hyw-1415',
            'snapshot_sha256': preview['snapshot_sha256']}
        code, options = self.http('/api/starting-options?' + urlencode(self.fields)); self.assertEqual(code, 200)
        self.options = options

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def test_engine_option_is_published_but_old_app_preflight_still_rejects_henry_selection(self):
        self.assertEqual(self.options['start_readiness']['schema_version'], evaluation.ENGINE_SCHEMA)
        self.assertTrue(any(row['actor_id'] == 'HYW-HENRY-V' for row in self.options['existing_character_openings']))
        fields = {**self.fields, 'selection_digest': self.options['selection_digest'], 'character_kind': 'existing',
            'actor_id': 'HYW-HENRY-V', 'opening_id': 'henry-1415-embarkation-v1'}
        code, _ = self.http('/api/starting-preview?' + urlencode(fields))
        self.assertEqual(code, 400)  # At this exact historical App; a blocker, not desired future behavior.
        self.assertEqual(self.store.listing(), [])
        self.observations['henry_preflight_http'] = code
        self.observations['product_acceptance'] = False

    def test_limited_modes_preflight_without_claiming_received_civil_projection_adoption(self):
        results = {}
        for case in ('henry-1415-default', 'john-1415-limited', 'new-1415-default'):
            character = evaluation.export_actor_input(case)['selection']['character']
            fields = {**self.fields, 'selection_digest': self.options['selection_digest'], 'character_kind': character['kind']}
            if character['kind'] == 'existing':
                fields['actor_id'] = character['actor_id']
            else:
                fields['species'] = 'human'
            code, result = self.http('/api/starting-preview?' + urlencode(fields))
            self.assertEqual(code, 200, result)
            self.assertEqual(result['status'], 'declaration_only')
            self.assertFalse(result['engine_start_context_contract'])
            results[case] = {'status': result['status'], 'engine_context_adopted': False,
                'campaign_time': result['campaign_time']}
        self.assertEqual(self.store.listing(), [])
        self.observations['limited_mode_previews'] = results


if __name__ == '__main__':
    unittest.main()
