"""Source pins cannot substitute for valid campaign editorial records."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('catalog_record_integrity', ROOT / 'IRGS_Catalog/verify_catalog.py')
integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity)


class CampaignRecordTests(unittest.TestCase):
    def setUp(self):
        self.portfolio = json.loads((ROOT / 'IRGS_Catalog/data/campaign_portfolio.json').read_text())
        self.listings = json.loads((ROOT / 'IRGS_Catalog/data/campaign_listings.json').read_text())

    def check(self):
        return integrity.verify_campaign_records(self.portfolio, self.listings)

    def test_current_44_concepts_validate_without_runtime_availability(self):
        result = self.check()
        self.assertEqual(result['unique_concepts'], 44)
        self.assertEqual(result['development_status_counts'],
                         {'concept_draft': 0, 'planned': 41, 'in_development': 3})
        self.assertFalse(result['runtime_availability_inferred'])

    def test_duplicate_ids_are_rejected(self):
        self.portfolio['entries'][1]['catalogue_id'] = self.portfolio['entries'][0]['catalogue_id']
        with self.assertRaisesRegex(RuntimeError, 'Duplicate campaign catalogue ID'):
            self.check()

    def test_invalid_id_types_and_formats_are_rejected(self):
        for identity in (None, 1, {}, [], 'SS-1', 'SS-01/other', 'engine-profile'):
            with self.subTest(identity=identity):
                self.portfolio['entries'][0]['catalogue_id'] = identity
                with self.assertRaisesRegex(RuntimeError, 'Invalid campaign catalogue ID'):
                    self.check()

    def test_type_and_slate_must_match_identity(self):
        original = copy.deepcopy(self.portfolio)
        for field, value in (('campaign_type', 'grand'), ('slate', 'future')):
            with self.subTest(field=field):
                self.portfolio = copy.deepcopy(original)
                self.portfolio['entries'][0][field] = value
                with self.assertRaisesRegex(RuntimeError, 'type or slate'):
                    self.check()

    def test_unknown_development_status_is_rejected(self):
        for status in ('released', 'available', '', True, None, []):
            with self.subTest(status=status):
                self.portfolio['entries'][0]['development_status'] = status
                with self.assertRaisesRegex(RuntimeError, 'development status'):
                    self.check()

    def test_concept_draft_and_disabled_preview_remain_valid_editorial_states(self):
        record = self.portfolio['entries'][0]
        record['development_status'] = 'concept_draft'
        # App filters drafts by status even if their preview flag is true.
        self.assertEqual(self.check()['development_status_counts']['concept_draft'], 1)
        record['availability']['preview'] = False
        self.assertEqual(self.check()['development_status_counts']['concept_draft'], 1)

    def test_release_and_entitlement_claims_are_rejected(self):
        for field in ('release_approved', 'entitlement_active'):
            for value in (True, 0, None, 'false'):
                with self.subTest(field=field, value=value):
                    record = self.portfolio['entries'][0]['availability']
                    record.update(release_approved=False, entitlement_active=False)
                    record[field] = value
                    with self.assertRaisesRegex(RuntimeError, 'explicit unreleased'):
                        self.check()

    def test_missing_or_nonboolean_preview_flags_are_rejected(self):
        for value in ('true', 1, None):
            with self.subTest(value=value):
                self.portfolio['entries'][0]['availability']['preview'] = value
                with self.assertRaisesRegex(RuntimeError, 'explicit unreleased'):
                    self.check()

    def test_campaign_readiness_and_runtime_certification_cannot_be_claimed(self):
        record = self.portfolio['entries'][0]
        for group, field in (('readiness', 'full_campaign_ready'), ('design_review', 'runtime_certified')):
            with self.subTest(group=group):
                record[group][field] = True
                with self.assertRaisesRegex(RuntimeError, 'uncertified'):
                    self.check()
                record[group][field] = False

    def test_runtime_derived_fields_are_rejected_even_with_false_values(self):
        record = self.portfolio['entries'][0]
        for field in ('available_slice', 'current_campaign_id', 'launch_capability', 'playable'):
            with self.subTest(field=field):
                record[field] = False
                with self.assertRaisesRegex(RuntimeError, 'Runtime availability belongs to App/Engine'):
                    self.check()
                del record[field]

    def test_discovery_ids_are_nonempty_strings_and_unique(self):
        for ids in ([], ['rise', 'rise'], ['rise', ''], [None], [{}], 'rise'):
            with self.subTest(ids=ids):
                self.listings['visible_campaign_ids'] = ids
                with self.assertRaisesRegex(RuntimeError, 'discovery IDs'):
                    self.check()

    def test_technical_registration_cannot_create_a_listing(self):
        self.listings['registration_alone_grants_listing'] = True
        with self.assertRaisesRegex(RuntimeError, 'registration cannot grant'):
            self.check()

    def test_unreconciled_start_reference_cannot_grant_launch(self):
        self.listings['starting_scenario_references'][0]['can_launch'] = True
        with self.assertRaisesRegex(RuntimeError, 'unable to grant launch'):
            self.check()

    def test_orphaned_and_duplicate_start_references_are_rejected(self):
        reference = self.listings['starting_scenario_references'][0]
        original = reference['campaign_id']
        reference['campaign_id'] = 'unlisted'
        with self.assertRaisesRegex(RuntimeError, 'unique, listed'):
            self.check()
        reference['campaign_id'] = original
        self.listings['starting_scenario_references'].append(copy.deepcopy(reference))
        with self.assertRaisesRegex(RuntimeError, 'unique, listed'):
            self.check()

    def test_malformed_documents_fail_with_catalog_errors(self):
        original = copy.deepcopy(self.portfolio)
        for document in ([], None, {'schema_version': True, 'entries': []},
                         {**original, 'entries': []}, {**original, 'entries': [None]}):
            with self.subTest(document_type=type(document).__name__):
                self.portfolio = document
                with self.assertRaises(RuntimeError):
                    self.check()

    def test_refreshing_source_pins_does_not_certify_bad_editorial_content(self):
        with tempfile.TemporaryDirectory(prefix='irgs-catalog-content-fixture-') as temp:
            root = Path(temp) / 'Catalog'
            # Small source-only fixture; no real parts, caches or user saves.
            shutil.copytree(ROOT / 'IRGS_Catalog', root,
                            ignore=shutil.ignore_patterns('parts', '__pycache__'))
            manifest = json.loads((root / 'historical_details/manifest.json').read_text())
            manifest.update(status='blocked_missing_source', parts=[],
                            source_verification='not_run_missing_source',
                            coverage={'archive_bytes': 'unavailable',
                                      'member_inventory': 'not_run', 'collections': []})
            (root / 'historical_details/manifest.json').write_text(json.dumps(manifest))
            self.portfolio['entries'][0]['availability']['release_approved'] = True
            (root / 'data/campaign_portfolio.json').write_text(json.dumps(self.portfolio))
            release = json.loads((root / 'release.json').read_text())
            release['files_sha256'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                       for name in integrity.source_files(root)}
            (root / 'release.json').write_text(json.dumps(release))
            with self.assertRaisesRegex(RuntimeError, 'explicit unreleased'):
                integrity.verify_catalog(root)


if __name__ == '__main__':
    unittest.main()
