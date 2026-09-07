"""Smoke test: verify all production modules import without errors.

This is the ONLY test in the project as of v1.0.0. Its purpose is to catch
syntax errors, missing dependencies, and broken import chains after a
refactor commit.

Run from repo root:
    python -m tests.test_pipeline_imports

Exit code 0 if all imports succeed; 1 otherwise.

What this test does NOT cover (intentional scope limits for v1):
- Runtime behavior of ETL scripts (requires BigQuery credentials, raw data).
- Data quality rules (covered by src.etl.validate_integrity).
- ML model accuracy (covered by docs/ml-spec.md acceptance criteria).
- Streamlit UI rendering (covered by manual click-through).

When this test should be expanded:
- Phase 2 (v2 roadmap) should add unit tests for each ETL transform function.
- Phase 3 should add integration tests with BigQuery emulator (BQ CLI local).
"""

from __future__ import annotations

import importlib
import sys
import traceback
from typing import List, Tuple

# Ensure repo root is on sys.path so 'src.*' imports resolve.
# This is the same pattern as src/etl/* modules which assume `python -m` invocation.
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# Production modules that MUST be importable for the pipeline to run.
# Order matters loosely: config and logger are imported by everything else,
# so test them first.
MODULES_TO_TEST: List[str] = [
    # Utilities — foundational, imported by all production code
    "src.utils.config",
    "src.utils.logger",
    "src.utils.bigquery_client",
    # ETL — 16 modules covering extract, populate_dim, load_*, consolidate, validate
    "src.etl.extract_data",
    "src.etl.provision_schema",
    "src.etl.populate_dim_date",
    "src.etl.populate_dim_stock",
    "src.etl.populate_dim_bank",
    "src.etl.populate_dim_trading_session",
    "src.etl.consolidate_stock_metrics",
    "src.etl.load_bank_performance",
    "src.etl.load_to_bigquery",
    "src.etl.validate_integrity",
    # ML — 8 modules covering ARIMA, LSTM, K-Means, Random Forest, Granger, DTW
    "src.models.baseline_arima",
    "src.models.train_lstm",
    "src.models.train_kmeans",
    "src.models.baseline_logistic",
    "src.models.train_random_forest",
    "src.models.dtw_analysis",
    "src.models.causal_analysis_llp",
    # Dashboard
    "src.dashboard.app",
    # Audit scripts
    "scripts.verify_looker_scorecards",
]


def _try_import(module_name: str) -> Tuple[bool, str]:
    """Attempt to import a module and capture any error.

    Args:
        module_name: Fully-qualified module path (e.g. "src.etl.extract_data").

    Returns:
        Tuple of (success: bool, error_message: str).
        On success, error_message is empty string.
    """
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:  # noqa: BLE001 — we want to see any error
        tb = traceback.format_exc(limit=3)
        return False, f"{type(exc).__name__}: {exc}\n{tb}"


def run_all() -> int:
    """Import every production module and report PASS/FAIL.

    Returns:
        Process exit code: 0 if all modules import cleanly, 1 otherwise.
    """
    print(f"Testing {len(MODULES_TO_TEST)} production modules...")
    print("=" * 70)

    results: List[Tuple[str, bool, str]] = []
    for module_name in MODULES_TO_TEST:
        ok, err = _try_import(module_name)
        results.append((module_name, ok, err))
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {module_name}")
        if not ok:
            print(f"         {err}")

    print("=" * 70)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print(f"SUMMARY: {passed} PASS, {failed} FAIL out of {len(results)}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())