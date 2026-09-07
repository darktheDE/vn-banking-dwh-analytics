"""Smoke test: verify production modules import without errors.

Supports tiered execution (ADR-0003) to allow running core ETL imports
in lightweight environments without ML/dashboard dependencies installed.

Usage:
    python -m tests.test_pipeline_imports --tier etl       # Core ETL only
    python -m tests.test_pipeline_imports --tier extract   # Data extractors (vnstock)
    python -m tests.test_pipeline_imports --tier ml        # ML & econometrics
    python -m tests.test_pipeline_imports --tier dashboard # Streamlit app
    python -m tests.test_pipeline_imports --tier all       # Entire repository
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import traceback
from typing import Dict, List, Tuple

# Ensure repo root is on sys.path so 'src.*' imports resolve.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

TIERS: Dict[str, List[str]] = {
    "etl": [
        # Foundational utilities
        "src.utils.config",
        "src.utils.logger",
        "src.utils.bigquery_client",
        # Core ETL DWH pipeline
        "src.etl.provision_schema",
        "src.etl.populate_dim_date",
        "src.etl.populate_dim_stock",
        "src.etl.populate_dim_bank",
        "src.etl.populate_dim_trading_session",
        "src.etl.consolidate_stock_metrics",
        "src.etl.load_bank_performance",
        "src.etl.load_to_bigquery",
        "src.etl.validate_integrity",
        # Scorecard verifier
        "scripts.verify_looker_scorecards",
    ],
    "extract": [
        "src.etl.extract_data",
    ],
    "ml": [
        "src.models.baseline_arima",
        "src.models.train_lstm",
        "src.models.train_kmeans",
        "src.models.baseline_logistic",
        "src.models.train_random_forest",
        "src.models.dtw_analysis",
        "src.models.causal_analysis_llp",
    ],
    "dashboard": [
        "src.dashboard.app",
    ],
}


def _try_import(module_name: str) -> Tuple[bool, str]:
    """Attempt to import a module and capture any error."""
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        tb = traceback.format_exc(limit=3)
        return False, f"{type(exc).__name__}: {exc}\n{tb}"


def run_tier(tier: str) -> int:
    """Import modules belonging to the specified tier and report results."""
    if tier == "all":
        modules = [m for m_list in TIERS.values() for m in m_list]
    elif tier in TIERS:
        modules = TIERS[tier]
    else:
        print(f"Error: Unknown tier '{tier}'. Choose from {list(TIERS.keys()) + ['all']}.")
        return 1

    print(f"Testing {len(modules)} modules (Tier: {tier.upper()})...")
    print("=" * 70)

    results: List[Tuple[str, bool, str]] = []
    for module_name in modules:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline import smoke test runner.")
    parser.add_argument(
        "--tier",
        choices=list(TIERS.keys()) + ["all"],
        default="etl",
        help="Target tier of modules to verify (default: etl).",
    )
    args = parser.parse_args()
    return run_tier(args.tier)


if __name__ == "__main__":
    sys.exit(main())