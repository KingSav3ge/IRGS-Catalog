"""Portable Catalog verification cannot depend on checkout import paths."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StandaloneCatalogTests(unittest.TestCase):
    def test_isolated_verifier_ignores_foreign_same_named_modules(self):
        code = """
import importlib.util, sys, types
from pathlib import Path
for name in ('response_depot_compatibility', 'integrated_response_compatibility',
             'development_interop_compatibility', 'phase_response_compatibility', 'player_start_evaluation',
             'start_context_evaluation', 'alpha_context_evaluation', 'alpha_journey_evaluation'):
    sys.modules[name] = types.ModuleType(name)  # Must never supply Catalog code.
path = Path(sys.argv[1]) / 'IRGS_Catalog/verify_catalog.py'
spec = importlib.util.spec_from_file_location('isolated_catalog', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.verify_catalog()
assert result['concepts'] == 44
assert result['integrated_response_compatibility']['status'] == 'verified'
assert result['development_interoperability']['status'] == 'verified'
assert result['phase_response_compatibility']['status'] == 'verified'
assert result['player_start_evaluation']['delivery_scope'] == 'requirements_and_baseline_diagnostics'
assert result['start_context_evaluation']['app_execution_qualified'] is False
assert result['alpha_context_evaluation']['alpha_qualified'] is False
assert result['alpha_journey_evaluation']['runtime_execution_verified_by_schema'] is False
"""
        with tempfile.TemporaryDirectory(prefix='irgs-catalog-isolated-') as directory:
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(ROOT)],
                cwd=directory, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
