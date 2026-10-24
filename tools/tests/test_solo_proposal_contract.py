"""Reject changed identities and unsupported claims in the compatibility record."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'IRGS_Catalog'))
import solo_proposal_compatibility as compatibility


class ProposalContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-proposal-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / compatibility.CONTRACT
        self.path.parent.mkdir(parents=True)
        self.fixture = self.root / compatibility.FIXTURE
        self.fixture.parent.mkdir(parents=True)
        shutil.copyfile(compatibility.ROOT / compatibility.FIXTURE, self.fixture)
        shutil.copyfile(compatibility.ROOT / compatibility.CONTRACT, self.path)
        self.doc = json.loads(self.path.read_text())

    def check(self):
        self.path.write_text(json.dumps(self.doc))
        return compatibility.validate_compatibility(self.root)

    def test_current_contract_preserves_original_fixture_and_defers_unimplemented_dialogue(self):
        self.assertEqual(self.check()['app_source_selections'], 2)
        self.assertFalse(self.check()['runtime_execution_verified_by_schema'])

    def test_changed_fixture_pin_and_bytes_are_rejected(self):
        self.doc['source_fixture']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'binding changed'): self.check()
        self.doc = compatibility.load_contract()
        self.fixture.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): self.check()

    def test_unknown_provider_config_and_missing_processing_classification_are_rejected(self):
        self.doc['model'] = 'forged-content-configuration'
        with self.assertRaisesRegex(ValueError, 'fields'): self.check()
        del self.doc['model']
        del self.doc['classification']
        with self.assertRaisesRegex(ValueError, 'fields'): self.check()

    def test_ambiguous_or_inexact_consumer_sources_are_rejected(self):
        self.doc['consumers']['engine_commit'] = 'main'
        with self.assertRaisesRegex(ValueError, 'Exact Engine'): self.check()
        self.doc = compatibility.load_contract()
        self.doc['consumers']['app_commits']['component_followup'] = self.doc['consumers']['app_commits']['integrated_development']
        with self.assertRaisesRegex(ValueError, 'Duplicate App'): self.check()

    def test_narration_completion_cannot_be_claimed_by_metadata(self):
        self.doc['narration_dialogue']['evaluation_status'] = 'passed'
        with self.assertRaisesRegex(ValueError, 'supported contract'): self.check()

    def test_duplicate_json_fields_are_rejected(self):
        self.path.write_text('{"schema_version": 1, "schema_version": 1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate compatibility'): compatibility.load_contract(self.root)


if __name__ == '__main__':
    unittest.main()
