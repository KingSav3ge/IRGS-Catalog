"""Rubric applied to fake proposals and actual ordinary-world committed effects."""
from pathlib import Path
import tempfile
import threading

from tools.tests import test_grounding_quality_consumers as selected
import grounding_quality as rubric


class FakeTransportConsumers(selected.GroundingOrdinaryConsumers):
    # These belong to the separate no-provider ordinary consumer.
    test_quay_reviewed_contact_and_speech = None
    test_rise_reviewed_introductions_and_speech = None
    test_quay_receipt_grounding_against_actual_committed_result = None
    test_rise_receipt_grounding_against_actual_committed_result = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import sys
        sys.path.insert(0, str(Path(selected.APP).resolve() / 'IRGS_Web/tests'))
        import test_solo_bridge as bridge
        import assistance
        if not Path(bridge.__file__).resolve().is_relative_to(Path(selected.APP).resolve()):
            raise RuntimeError('Wrong App test source')
        cls.bridge, cls.assistance = bridge, assistance

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-grounding-fake-')
        self.addCleanup(self.temp.cleanup)
        self.store = self.server.Store(Path(self.temp.name) / 'saves')
        self.transport = self.bridge.OfflineTransport()
        private = Path(self.temp.name) / 'technical'; private.mkdir()
        provider = self.solo_provider
        route = provider.Route('offline', 'synthetic', 'none', 'in-process', 'fixture-v1', 'v1',
            'config-v1', 'synthetic-transfer-approved-v1', 'synthetic-ceiling-v1', 10,
            enabled=True, approval_ref='offline-tests-only', lifecycle='qualified',
            tested_capabilities=(provider.SCHEMA_VERSION,), operations=(provider.LOCAL_OPERATION, provider.RISE_OPERATION))
        self.config = self.assistance.SoloConfiguration(lambda scope: provider.CapabilityBroker(
            provider.SpecialistRegistry([route]), provider.AttemptLedger(private / 'attempts.sqlite',
            budget_units=100, max_inflight=2), enabled=True, scope_reader=scope), self.transport,
            'offline', 'synthetic-approved', 'synthetic-transfer-approved-v1', 'config-v1', private, 60, 512)
        self.start()
        self.addCleanup(self.stop)

    def start(self):
        self.host = self.server.make_server(0, self.store.folder, reference_config=Path(self.temp.name) / 'no-config.json',
            reference_cache=Path(self.temp.name) / 'cache', solo_configuration=self.config)
        self.thread = threading.Thread(target=self.host.serve_forever, daemon=True); self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.host.server_port)
        self.token = self.http('/api/campaigns')[1]['token']

    def check_proposal(self, context, action, intention):
        key = self.create(context); view = self.view(key); actor = view['actor_id']
        self.transport.action = action
        body = {'id': key, 'actor': actor, 'revision': view['revision'],
                'request_id': 'grounding-fake-' + context, 'intention': intention}
        saved = self.store.path(key).read_bytes()
        proposal = self.ok('/api/ai/proposal', body)
        self.assertEqual(proposal['status'], 'proposal_ready')
        self.assertEqual(self.store.path(key).read_bytes(), saved)
        model_input = self.transport.inputs[-1]
        candidate = proposal['proposal']
        annotated = {k: candidate[k] for k in ('intention', 'action_id', 'source_refs')}
        assessment = rubric.assess_proposal(model_input, annotated,
            {'status': 'pass', 'evidence_refs': ['authored-intention', 'received-action-review']})
        self.assertEqual(assessment['status'], 'reviewed_pass')
        self.assertFalse(assessment['semantic_inference_performed'])
        self.assertFalse(assessment['action_authorized'])
        self.assertEqual(annotated['action_id'], action)
        self.assertNotIn(self.marker, str(model_input))
        self.assertNotIn('state_digest', str(model_input))
        accepted_body = {**body, 'proposal_digest': candidate['proposal_digest'], 'explicitly_accepted': True}
        accepted = self.ok('/api/ai/accept', accepted_body)
        self.assertEqual(accepted['status'], 'completed_successfully')
        self.assertEqual(accepted['declaration'], intention)
        self.assertIsNone(accepted['narrative'])
        self.assertTrue(accepted['outcome']['summary'])
        event = accepted['receipt']['event_id']
        self.assertTrue(event)
        state = self.store.read(key)['state']
        expected_location = 'passage' if context == 'quay' else 'clearing'
        expected_elapsed = 45 if context == 'quay' else 300
        location = state['actors'][actor]['current']['location']
        self.assertEqual(location['value'] if context == 'quay' else location, expected_location)
        self.assertEqual(state['elapsed_time']['seconds'], expected_elapsed)
        self.assertEqual(self.http('/api/action-result/' + key + '/' + body['request_id'] + '?actor_id=' + actor),
                         (200, accepted))
        saved = self.store.path(key).read_bytes(); self.stop(); self.start()
        self.assertEqual(self.http('/api/ai/accept', accepted_body), (200, accepted))
        self.assertEqual(self.store.path(key).read_bytes(), saved)
        self.assertEqual(len(self.transport.inputs), 1)

    def test_quay_fake_proposal_and_real_receipt(self):
        self.check_proposal('quay', 'quay-passage', 'I take the passage.')

    def test_rise_fake_proposal_and_real_receipt(self):
        self.check_proposal('rise', 'walk_clearing', 'I walk to the clearing.')
