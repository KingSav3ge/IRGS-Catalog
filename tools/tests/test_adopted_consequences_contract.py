"""Independent selection guards and evaluator-only requirement checks."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2] / 'IRGS_Catalog'
sys.path.insert(0, str(ROOT))
import adopted_consequences_evaluation as evaluation


class AdoptedConsequencesContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ww-adopted-contract-'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.folder = self.root / evaluation.FIXTURE
        shutil.copytree(ROOT / evaluation.FIXTURE, self.folder)
        original = self.root / evaluation.BASELINE; original.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / evaluation.BASELINE, original)

    def save(self, path, doc): path.write_text(json.dumps(doc, indent=2) + '\n')

    def test_exact_pins_and_schema_do_not_establish_execution_or_semantic_truth(self):
        doc = evaluation.load_fixture(self.root)
        self.assertEqual(doc['selection'], evaluation.SELECTION)
        result = evaluation.validate_fixture(self.root)
        self.assertFalse(result['runtime_execution_verified_by_schema'])
        self.assertFalse(result['semantic_judgments_verified']); self.assertFalse(result['alpha_qualified'])
        doc['selection']['app_engine_pin'] = '0' * 40
        self.save(self.folder / 'manifest.json', doc)
        with self.assertRaises(ValueError): evaluation.load_fixture(self.root)

    def test_private_instructions_or_missing_owners_fail_even_with_refreshed_hash(self):
        for name in ('actor_inputs/cases.json', 'evaluator_only/expectations.json'):
            with self.subTest(name=name):
                manifest = evaluation.load_fixture(self.root); payload = evaluation.read(self.folder / name)
                if name.startswith('actor'): payload['journeys']['quay'][0]['intention'] = 'PRIVATE_EVALUATOR'
                else: del payload['unmet_requirements']['npc_decisions']
                self.save(self.folder / name, payload)
                manifest['files_sha256'][name] = hashlib.sha256((self.folder / name).read_bytes()).hexdigest()
                self.save(self.folder / 'manifest.json', manifest)
                with self.assertRaises(ValueError): evaluation.load_fixture(self.root)
                shutil.copyfile(ROOT / evaluation.FIXTURE / name, self.folder / name)
                shutil.copyfile(ROOT / evaluation.FIXTURE / 'manifest.json', self.folder / 'manifest.json')

    def test_prior_fixture_bytes_are_bound(self):
        (self.root / evaluation.BASELINE).write_text('{}')
        with self.assertRaises(ValueError): evaluation.load_fixture(self.root)
