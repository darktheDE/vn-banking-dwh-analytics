"""Verify Looker Studio scorecard values against BigQuery ground truth.

This script cross-checks the headline numbers rendered in the Looker Studio
dashboards (total banks, high-risk bank count, average NPL ratio, cluster
distribution, average CIR per cluster, NPL trajectory outliers) against the
authoritative values stored in BigQuery.

How to interpret the output:
    * PASS  - The BigQuery value matches the expected threshold.
    * WARN  - Value is borderline or informational; not blocking, but flag it.
    * FAIL  - Value deviates from the expected threshold; Looker Studio is
              either rendering stale data, applying an incorrect filter, or
              pointing at the wrong table. Investigate the dashboard config.

Exit code:
    0  - All checks PASS or WARN.
    1  - At least one check FAILed.

Usage:
    python scripts/verify_looker_scorecards.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google.cloud import bigquery

from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CREDENTIALS = "./vn-banking-dwh-analytics-67f213ad7317.json"
DEFAULT_PROJECT_ID = "vn-banking-dwh-analytics"
DEFAULT_DATASET_ID = "financial_dwh"

EXPECTED_CLUSTER_SIZES = {13, 24, 2}


class LookerScorecardVerifier:
    """Audit Looker Studio scorecards by reconciling them with BigQuery.

    Each ``verify_*`` method queries the source-of-truth BigQuery tables and
    compares the result against the published dashboard expectation.
    """

    def __init__(self, client: bigquery.Client, dataset_id: str) -> None:
        """Store the BigQuery client and dataset id for subsequent queries.

        Args:
            client: An authenticated BigQuery client.
            dataset_id: The fully resolved BigQuery dataset identifier.
        """
        self.client = client
        self.dataset_id = dataset_id

    def _query_scalar(self, sql: str):
        """Run a single-value SQL statement and return the first row's first column.

        Args:
            sql: A SQL statement that returns exactly one scalar row.

        Returns:
            The scalar value, or ``None`` when the query yields nothing.
        """
        job = self.client.query(sql)
        result = job.result()
        for row in result:
            return row[0]
        return None

    def _report(self, check_name: str, expected: str, actual, status: str) -> None:
        """Print one verification line and log it at the appropriate level.

        Args:
            check_name: Human-readable check description.
            expected: Stringified expected value or threshold description.
            actual: The measured value from BigQuery (will be stringified).
            status: One of PASS, WARN, FAIL.
        """
        line = f"[{check_name}] ... expected={expected:<22} actual={actual!s:<14} {status}"
        if status == "FAIL":
            logger.error(line)
        elif status == "WARN":
            logger.warning(line)
        else:
            logger.info(line)

    def verify_total_banks(self) -> str:
        """Total distinct banks in dim_bank must equal 45."""
        sql = f"SELECT COUNT(DISTINCT bank_key) FROM `{self.dataset_id}.dim_bank`"
        actual = int(self._query_scalar(sql) or 0)
        status = "PASS" if actual == 45 else "FAIL"
        self._report("1/6 Total banks (dim_bank)", "45", actual, status)
        return status

    def verify_high_risk_count(self) -> str:
        """High-risk bank prediction rows (risk_label=1) must equal 145."""
        sql = (
            f"SELECT COUNT(*) FROM `{self.dataset_id}.bank_risk_predictions` "
            "WHERE risk_label = 1"
        )
        actual = int(self._query_scalar(sql) or 0)
        status = "PASS" if actual == 145 else "FAIL"
        note = "  <-- LIKELY Looker bug" if status == "FAIL" else ""
        self._report("2/6 High-risk count (bank_risk_predictions)", f"145{note}", actual, status)
        return status

    def verify_avg_npl_ratio(self) -> str:
        """Average NPL ratio across fact_bank_performance must land in [0.02, 0.05]."""
        sql = f"SELECT AVG(npl_ratio) FROM `{self.dataset_id}.fact_bank_performance`"
        actual = float(self._query_scalar(sql) or 0.0)
        status = "PASS" if 0.02 <= actual <= 0.05 else "FAIL"
        self._report("3/6 Avg NPL ratio (fact_bank_performance)", "~0.035", round(actual, 4), status)
        return status

    def verify_cluster_distribution(self) -> str:
        """Cluster sizes from bank_cluster_assignments must equal {13, 24, 2}."""
        sql = (
            f"SELECT cluster_id, COUNT(*) AS n "
            f"FROM `{self.dataset_id}.bank_cluster_assignments` "
            "GROUP BY cluster_id"
        )
        sizes = {int(row.n) for row in self.client.query(sql).result()}
        status = "PASS" if sizes == EXPECTED_CLUSTER_SIZES else "FAIL"
        self._report(
            "4/6 Cluster sizes (bank_cluster_assignments)",
            str(EXPECTED_CLUSTER_SIZES),
            str(sizes),
            status,
        )
        return status

    def verify_avg_cir_per_cluster(self) -> str:
        """Average CIR per cluster must stay below 0.7; flags the L-02 quality issue."""
        sql = (
            f"SELECT p.cluster_id, AVG(f.cir) AS avg_cir "
            f"FROM `{self.dataset_id}.bank_cluster_assignments` p "
            f"JOIN `{self.dataset_id}.fact_bank_performance` f USING (bank_key) "
            "GROUP BY p.cluster_id"
        )
        rows = list(self.client.query(sql).result())
        max_cir = max(float(r.avg_cir) for r in rows) if rows else 0.0
        status = "PASS" if max_cir < 0.7 else "FAIL"
        note = "  <-- L-02 data quality" if status == "FAIL" else ""
        self._report("5/6 Avg CIR per cluster", f"<0.7{note}", round(max_cir, 4), status)
        return status

    def verify_npl_trajectory_outliers(self) -> str:
        """Any bank-year with npl_ratio > 0.10 indicates an L-03 outlier (e.g. TNB 2008)."""
        sql = (
            f"SELECT COUNT(*) FROM `{self.dataset_id}.fact_bank_performance` "
            "WHERE npl_ratio > 0.10"
        )
        actual = int(self._query_scalar(sql) or 0)
        status = "PASS" if actual == 0 else "WARN"
        note = "  <-- L-03 TNB 2008" if status == "WARN" else ""
        self._report("6/6 NPL trajectory outliers (>10%)", f"0{note}", actual, status)
        return status

    def run_all(self) -> int:
        """Execute every verification check and emit a summary.

        Returns:
            Process exit code: 0 if no FAIL, 1 otherwise.
        """
        logger.info("Starting Looker Studio scorecard verification against %s.", self.dataset_id)

        results = [
            self.verify_total_banks(),
            self.verify_high_risk_count(),
            self.verify_avg_npl_ratio(),
            self.verify_cluster_distribution(),
            self.verify_avg_cir_per_cluster(),
            self.verify_npl_trajectory_outliers(),
        ]

        passed = results.count("PASS")
        warned = results.count("WARN")
        failed = results.count("FAIL")
        logger.info(
            "SUMMARY: %d PASS, %d WARN, %d FAIL",
            passed,
            warned,
            failed,
        )

        return 0 if failed == 0 else 1


def _resolve_credentials_path() -> None:
    """Ensure GOOGLE_APPLICATION_CREDENTIALS is set, defaulting to the project key.

    Mirrors the auth bootstrap used by ``src.etl.load_to_bigquery``.
    """
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS
        logger.info(
            "GOOGLE_APPLICATION_CREDENTIALS unset; defaulting to %s.",
            DEFAULT_CREDENTIALS,
        )


def _resolve_project_and_dataset():
    """Return ``(project_id, dataset_id)`` using ``load_config`` when available.

    Returns:
        A 2-tuple ``(project_id, dataset_id)``.
    """
    try:
        from src.utils.config import load_config

        config = load_config()
        return config.gcp_project_id, config.bq_dataset_id
    except Exception as exc:
        logger.warning(
            "load_config() unavailable (%s); falling back to hardcoded project/dataset.",
            exc,
        )
        return DEFAULT_PROJECT_ID, DEFAULT_DATASET_ID


def main() -> int:
    """CLI entrypoint: bootstrap auth, run checks, return process exit code."""
    load_dotenv()
    _resolve_credentials_path()
    project_id, dataset_id = _resolve_project_and_dataset()
    client = bigquery.Client(project=project_id)
    verifier = LookerScorecardVerifier(client, dataset_id)
    return verifier.run_all()


if __name__ == "__main__":
    sys.exit(main())
