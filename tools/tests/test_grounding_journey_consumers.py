"""Re-run independent journeys against the separately selected adopted 3.4.5 set."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from tools.tests import test_alpha_journey_consumers as prior
from tools.tests import test_grounding_quality_consumers as selected


class AdoptedJourneyConsumers(prior.AlphaJourneyConsumers):
    __unittest_skip__ = not bool(selected.ENGINE and selected.APP)
    __unittest_skip_why__ = 'Exact 3.4.5 Engine/App source roots required'
    # Previous baseline checks assert old absent-channel behavior and have their
    # own historical selection; do not reinterpret or repin those tests.
    test_ordinary_creation_reports_actual_communication_availability = None
    test_selected_fixture_speech_preserves_testimony_acceptance_and_recovery = None
    test_selected_fixture_offer_refusal_consent_and_competing_retries = None
    test_adopted_henry_start_receives_initial_day_and_exact_observation = None

    @classmethod
    def setUpClass(cls):
        for path, sha in ((selected.ENGINE, selected.ENGINE_SHA), (selected.APP, selected.APP_SHA)):
            if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != sha:
                raise RuntimeError('Wrong adopted source revision')
            if subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Selected sources must be clean')
        for name, sha in (('Engine', selected.ENGINE_SHA), ('Catalog', selected.CATALOG_PIN)):
            if subprocess.check_output(['git', '-C', selected.APP, 'rev-parse', 'HEAD:' + name], text=True).strip() != sha:
                raise RuntimeError('Unexpected App gitlink')
        engine = Path(selected.ENGINE).resolve() / 'IRGS_3_3'
        app = Path(selected.APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(prior.alpha.base.CATALOG)
        sys.path[:0] = [str(app / 'tests'), str(app), str(engine / 'runtime')]
        for name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures',
                     'starting_selection', 'settlement_setup', 'historical_campaigns', 'core_world',
                     'offline_responses', 'scene_actions', 'solo_provider', 'response_depot', 'openai_proposals'):
            module = importlib.import_module(name)
            source = app if name in ('server', 'rise_campaigns', 'gameplay_views', 'local_presentation', 'app_communication_fixtures') else engine
            if not Path(module.__file__).resolve().is_relative_to(source):
                raise RuntimeError('Wrong import; run in a fresh process')
            setattr(cls, name, module)
        cls.contract = prior.alpha.base.compatibility.original.load_fixture()
        cls.reports = {}

    def evidence(self, case, receipts, retry, restore):
        self.assertTrue(retry and restore)
        self.assertEqual(len(receipts), len(set(receipts)))
        self.reports[case] = {'case_id': case, 'engine_commit': selected.ENGINE_SHA,
            'app_commit': selected.APP_SHA, 'app_catalog_pin': selected.CATALOG_PIN,
            'catalog_selection': 'candidate containing this test', 'sessions': 2,
            'receipt_ids': receipts, 'retry_verified': retry, 'identical_byte_restore_verified': restore,
            'pending_requirements': list(prior.evaluation.REQUIRED), 'alpha_qualified': False}

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('IRGS_GROUNDING_JOURNEY_OUTPUT'):
            Path(os.environ['IRGS_GROUNDING_JOURNEY_OUTPUT']).write_text(json.dumps(cls.reports, indent=2) + '\n')
