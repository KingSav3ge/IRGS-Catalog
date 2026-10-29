"""Independent 3.4.5 ordinary HTTP consumers; local receipts, no live model."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tools.tests import test_current_ordinary_consumers as current
sys.path.insert(0, str(current.ROOT / 'IRGS_Catalog'))
import grounding_quality as rubric

ENGINE = os.environ.get('IRGS_GROUNDING_ENGINE_SOURCE')
APP = os.environ.get('IRGS_GROUNDING_APP_SOURCE')
ENGINE_SHA = '296e46a1beed10d0ebf2841f133bb52fade83697'
APP_SHA = '7e1a5929b2f30479aa315789f75bfa6c46761438'
CATALOG_PIN = 'e97d87f0d17a16dbe0ce186badafe663188321a1'


class GroundingOrdinaryConsumers(current.CurrentOrdinaryConsumers):
    __unittest_skip__ = not bool(ENGINE and APP)
    __unittest_skip_why__ = 'Exact 3.4.5 Engine/App source roots required'

    @classmethod
    def setUpClass(cls):
        for path, sha in ((ENGINE, ENGINE_SHA), (APP, APP_SHA)):
            if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != sha:
                raise RuntimeError('Unselected 3.4.5 source revision')
            if subprocess.check_output(['git', '-C', path, 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Selected sources must be clean')
        for name, sha in (('Engine', ENGINE_SHA), ('Catalog', CATALOG_PIN)):
            if subprocess.check_output(['git', '-C', APP, 'rev-parse', 'HEAD:' + name], text=True).strip() != sha:
                raise RuntimeError('Unexpected committed App gitlink')
        engine, app = Path(ENGINE).resolve() / 'IRGS_3_3', Path(APP).resolve() / 'IRGS_Web'
        os.environ['IRGS_ENGINE_ROOT'], os.environ['IRGS_CATALOG_ROOT'] = str(engine), str(current.ROOT / 'IRGS_Catalog')
        sys.path[:0] = [str(app), str(engine / 'runtime')]
        for name, source in [('server', app), ('solo_provider', engine), ('openai_proposals', engine),
                             ('communication_runtime', engine), ('core_world', engine)]:
            module = importlib.import_module(name)
            if not Path(module.__file__).resolve().is_relative_to(source):
                raise RuntimeError('Wrong imported source; run a fresh process')
            setattr(cls, name, module)
        cls.cases = json.loads((current.FIXTURE / 'actor_inputs/cases.json').read_text())
        cls.oracle = json.loads((current.FIXTURE / 'evaluator_only/expectations.json').read_text())
        fixture = current.ROOT / 'IRGS_Catalog/evaluation/grounding_quality_v1'
        cls.grounding_cases = json.loads((fixture / 'actor_inputs/cases.json').read_text())['cases']
        cls.marker = json.loads((fixture / 'evaluator_only/requirements.json').read_text())['marker']

    def qualify_grounding(self, context, fixture_case):
        case = dict(self.cases[context]); case['words'] = self.grounding_cases[fixture_case]['intention']
        key = self.create(context); view = self.view(key); actor = view['actor_id']
        self.assertNotIn(self.marker, json.dumps(view))
        body = self.prepare(key, actor, case, 'grounding-receipt')
        code, result = self.execute(body); self.assertEqual(code, 200, result)
        self.assertNotIn(self.marker, json.dumps(result))
        communication = result['communication']; event = result['receipt']['event_id']
        self.assertEqual(event, 'communication:' + body['request_id'])
        world = self.core_world.CoreWorld(state=self.store.read(key)['state'])
        projected = self.communication_runtime.presentation(world, actor, body['request_id'])
        self.assertEqual(projected['request_id'], body['request_id'])
        committed = {'event_id': event, 'status': communication['status'],
                     'truth_status': communication['truth_status'], 'utterance': communication['utterance']}
        rendered = {'event_id': event, 'status': projected['status'],
                    'truth_status': projected['utterance_status'], 'utterance': projected['utterance']}
        report = rubric.assess_receipt(committed, rendered)
        self.assertEqual(report['status'], 'exact_structured_match')
        self.assertFalse(report['free_text_semantics_checked'])
        self.assertFalse(report['live_model_quality_verified'])
        self.assertEqual(result['presentation']['source_ref'], event)
        self.assertEqual(result['presentation']['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
        self.assertEqual(projected['committed_transfer'], None)
        self.assertEqual(communication['status'], 'testimony_received')
        self.assertEqual(communication['truth_status'], 'testimony')
        self.assertEqual(communication['utterance'], case['words'])
        saved = self.store.path(key).read_bytes(); self.stop(); self.start()
        self.assertEqual(self.execute(body), (200, result))
        self.assertEqual(self.store.path(key).read_bytes(), saved)
        review = {name: {'status': 'unknown', 'evidence_refs': []} for name in rubric.DIMENSIONS}
        review['receipt_fidelity'] = {'status': 'pass', 'evidence_refs': [event]}
        assessment = rubric.assess_review(review)
        self.assertEqual(assessment['status'], 'unknown')
        self.assertFalse(assessment['alpha_qualified'])

    def test_quay_receipt_grounding_against_actual_committed_result(self):
        self.qualify_grounding('quay', 'quay-contact')

    def test_rise_receipt_grounding_against_actual_committed_result(self):
        self.qualify_grounding('rise', 'rise-r00')


if __name__ == '__main__':
    unittest.main()
