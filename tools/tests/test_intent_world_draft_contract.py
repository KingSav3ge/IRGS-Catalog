"""Selection integrity and actor/evaluator separation at the new version."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

CATALOG = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(CATALOG))
import intent_world_draft_evaluation as evaluation


class IntentWorldDraftContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-draft-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / evaluation.FIXTURE
        shutil.copytree(CATALOG / evaluation.FIXTURE, self.folder)
        original = self.root / evaluation.ORIGINAL
        original.parent.mkdir(parents=True)
        shutil.copyfile(CATALOG / evaluation.ORIGINAL, original)

    def save(self, path, value):
        path.write_text(json.dumps(value, indent=2) + '\n')

    def test_exact_selection_and_schema_do_not_prove_runtime(self):
        manifest = evaluation.load_fixture(self.root)
        self.assertEqual(manifest['selection'], evaluation.SELECTION)
        result = evaluation.validate_fixture(self.root)
        self.assertFalse(result['runtime_execution_verified_by_schema'])
        self.assertFalse(result['engine_validation_performed_by_schema'])
        self.assertFalse(result['alpha_qualified'])
        manifest['selection']['engine'] = '0' * 40
        self.save(self.folder / 'manifest.json', manifest)
        with self.assertRaises(ValueError): evaluation.load_fixture(self.root)

    def test_refreshed_hash_cannot_hide_private_actor_data_or_missing_gaps(self):
        for target in ('actor_inputs/cases.json', 'evaluator_only/expectations.json'):
            with self.subTest(target=target):
                manifest = evaluation.load_fixture(self.root)
                payload = evaluation.read(self.folder / target)
                if target.startswith('actor'):
                    payload['journeys']['rise'][0]['intention'] = 'PRIVATE_EVALUATOR_ONLY'
                else:
                    payload['pending'].remove('npc_decisions')
                self.save(self.folder / target, payload)
                manifest['files_sha256'][target] = hashlib.sha256((self.folder / target).read_bytes()).hexdigest()
                self.save(self.folder / 'manifest.json', manifest)
                with self.assertRaises(ValueError): evaluation.load_fixture(self.root)
                shutil.copyfile(CATALOG / evaluation.FIXTURE / target, self.folder / target)
                shutil.copyfile(CATALOG / evaluation.FIXTURE / 'manifest.json', self.folder / 'manifest.json')

    def test_original_fixture_and_selected_payload_cannot_silently_change(self):
        path = self.root / evaluation.ORIGINAL
        path.write_text('{}')
        with self.assertRaises(ValueError): evaluation.load_fixture(self.root)
        shutil.copyfile(CATALOG / evaluation.ORIGINAL, path)
        with (self.folder / 'actor_inputs/cases.json').open('a') as stream: stream.write(' ')
        with self.assertRaises(ValueError): evaluation.load_fixture(self.root)
