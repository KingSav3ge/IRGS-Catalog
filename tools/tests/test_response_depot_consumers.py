"""Neutral depot against one actual campaign adapter; no Engine/App edits."""
import unittest

from tools.tests import test_scripted_response_consumers as legacy

responses = legacy.responses


@unittest.skipUnless(legacy.ENGINE and legacy.APP, 'Exact response-depot Engine/App snapshots required')
class ResponseDepotConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy.ScriptedConsumerTests.setUpClass.__func__(cls)

    def setUp(self):
        legacy.ScriptedConsumerTests.setUp(self)
        self.library = responses.load_library()

    context = legacy.ScriptedConsumerTests.context
    no_dispatch_or_mutation = legacy.ScriptedConsumerTests.no_dispatch_or_mutation
    act = legacy.ScriptedConsumerTests.act
    establish_active_work = legacy.ScriptedConsumerTests.establish_active_work

    def test_actual_committed_sequence_keeps_exact_receipts_without_calls_or_mutation(self):
        for index, case in enumerate(c for c in self.evaluator['oracle']['cases'] if c['kind'] == 'legitimate'):
            result = self.act(case)
            state = self.store.read(self.key)['state']
            receipt = state['settlement_receipts']['founder'][case['request_id']]['text']
            self.assertEqual(receipt, result['outcome']['summary'])
            ref = result['receipt']['event_id']
            contexts = {
                'receipt.exact': self.context('committed_receipt', 'committed', {'receipt_text': receipt}, ref),
                'elapsed.action': self.context('committed_receipt', 'committed',
                    {'elapsed_seconds': result['elapsed_time']['seconds']}, ref),
                'turn.next': self.context('host_status', 'waiting_for_player')}
            with self.no_dispatch_or_mutation():
                output = responses.compose_recipe(self.library, 'routine.result', contexts,
                    variants={'elapsed.action': index, 'turn.next': index})
            self.assertTrue(output.startswith(receipt + ' '))
            for marker in self.evaluator['oracle']['hidden_markers']:
                self.assertNotIn(marker, output)
        self.assertEqual(self.store.read(self.key)['state']['elapsed_time']['seconds'], 3900)

    def test_campaign_resource_labels_and_reservations_are_adapter_supplied(self):
        self.establish_active_work()
        view = self.rise.view(self.store.read(self.key)['state'], 'founder')
        for item in view['inventory']:
            ref = 'view:inventory:' + item['material']
            shared = {'resource_label': item['material'], 'unit': item['unit']}
            contexts = {
                'inventory.item': self.context('actor_view', 'inventory_known',
                    {**shared, 'quantity': item['quantity']}, ref),
                'inventory.available': self.context('actor_view', 'inventory_known',
                    {**shared, 'available': item['available']}, ref),
                'inventory.reserved': self.context('actor_view', 'inventory_known',
                    {**shared, 'reserved': item['reserved_for_work']}, ref)}
            if 'protected_seed' in item:
                contexts['inventory.protected'] = self.context('actor_view', 'inventory_known',
                    {**shared, 'protected_quantity': item['protected_seed']}, ref)
            with self.no_dispatch_or_mutation():
                for index in range(8):
                    output = responses.compose_recipe(self.library, 'routine.inventory', contexts,
                        variants={family: index for family in contexts})
                    self.assertIn(item['material'], output)
                    self.assertIn(item['unit'], output)
                    self.assertNotIn('oren-home', output)

    def test_actual_place_projection_uses_host_labels_without_new_capacity_claims(self):
        self.establish_active_work()
        view = self.rise.view(self.store.read(self.key)['state'], 'founder')
        camp = view['camp']
        contexts = {
            'place.name': self.context('actor_view', 'place_visible', {'place_label': camp['name']}, 'view:camp'),
            'place.capacity': self.context('actor_view', 'place_visible',
                {'capacity_label': 'shelter places', 'capacity_quantity': camp['shelter_places']}, 'view:camp'),
            'place.occupants': self.context('actor_view', 'place_visible',
                {'occupant_label': 'residents', 'occupant_quantity': camp['residents']}, 'view:camp'),
            'place.shortfall': self.context('actor_view', 'place_visible',
                {'shortfall_label': 'shelter shortfall', 'shortfall_quantity': camp['shelter_shortfall']}, 'view:camp')}
        with self.no_dispatch_or_mutation():
            for index in range(8):
                output = responses.compose_recipe(self.library, 'routine.place', contexts,
                    variants={family: index for family in contexts})
                self.assertIn(camp['name'], output)
                self.assertIn('shelter shortfall', output)
                self.assertIn(str(camp['shelter_shortfall']), output)
                self.assertNotIn('Oren', output)

    def test_all_editable_intentions_render_without_submission_or_operation_inference(self):
        # Synthetic labels exercise formatting, not campaign support or automatic availability.
        count = 0
        with self.no_dispatch_or_mutation():
            for family in self.library['families']:
                if family['channel'] != 'player_draft':
                    continue
                context = self.context('player_request', 'draft', {
                    key: 'Synthetic received record.' if kind == 'source_text' else 'Synthetic known label'
                    for key, kind in family['slots'].items()})
                for index in range(len(family['variants'])):
                    self.assertTrue(responses.render_fragment(self.library, family['id'], context, variant=index))
                    count += 1
        self.assertEqual(count, 250)
        self.assertEqual(self.store.read(self.key)['revision'], 0)


if __name__ == '__main__':
    unittest.main()
