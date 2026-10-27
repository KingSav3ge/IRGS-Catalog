"""Alpha assessment is separate from actor instructions and release approval."""
import json
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import alpha_context_evaluation as evaluation


class AlphaContextContractTests(unittest.TestCase):
    def test_distinct_campaigns_have_all_required_areas_and_remain_unqualified(self):
        result = evaluation.validate_fixture()
        self.assertFalse(result['alpha_qualified'])
        data = evaluation.load_evaluator_data()
        self.assertEqual(set(data['contexts']), set(evaluation.CASES))
        for context in data['contexts'].values():
            self.assertEqual(set(context['areas']), set(evaluation.AREAS))
            self.assertTrue(any(row['state'] == 'missing' for row in context['areas'].values()))

    def test_actor_exports_are_detached_and_exclude_private_matrix(self):
        for case in evaluation.CASES:
            doc = evaluation.export_actor_input(case)
            self.assertNotIn('PRIVATE_ALPHA_ORACLE', json.dumps(doc))
            self.assertNotIn('evaluator_only', json.dumps(doc))
            doc['selection'].clear()
            self.assertTrue(evaluation.export_actor_input(case)['selection'])

    def test_rehashed_actor_cannot_inject_privileged_world_or_private_oracle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); directory = root / evaluation.FIXTURE
            shutil.copytree(evaluation.ROOT / evaluation.FIXTURE, directory)
            path = directory / 'actor_inputs/historical-quay.json'
            doc = json.loads(path.read_text()); doc['selection']['world'] = {'stock': 999}
            path.write_text(json.dumps(doc))
            manifest = directory / 'manifest.json'; data = json.loads(manifest.read_text())
            data['files_sha256']['actor_inputs/historical-quay.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'privileged setup'):
                evaluation.load_fixture(root)


if __name__ == '__main__':
    unittest.main()
