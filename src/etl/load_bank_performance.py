"""Task B-13: Load fact_bank_performance.

Reads the raw CAMELS workbook, standardizes the bank performance data,
handles 2002-2005 missing values with median imputation, and prepares a
clean fact table for BigQuery and downstream feature engineering.

The raw source workbook is the `Data` sheet in:
`data/VN banks dataset (updated August 2023).xlsx`
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.utils.logger import get_logger

logger = get_logger(__name__)

WORKBOOK_NAME = "VN banks dataset (updated August 2023).xlsx"
DATA_SHEET_NAME = "Data"
BANKS_SHEET_NAME = "Banks List"

RAW_TO_CANONICAL = {
	"Bank Code": "bank_code",
	"Year": "year",
	"Classification": "bank_type",
	"Number of Employees": "num_employees",
	"Number of Branches": "num_branches",
	"Labour productivity": "labour_productivity",
	"Network productivity": "network_productivity",
	"Employees Ratio": "employees_ratio",
	"Branches Ratio": "branches_ratio",
	"Total Deposits": "total_deposits",
	"Total Shareholder's Equity": "total_equity",
	"Total Loans": "total_loans",
	"Loan Loss Provisions": "loan_loss_provision",
	"Non-performing Loans": "npl_amount",
	"Total Fixed Assets": "total_fixed_assets",
	"Liquid Assets": "liquid_assets",
	"Total Assets": "total_assets",
	"Total Deposits Ratio": "total_deposits_ratio",
	"Total Loans Ratio": "total_loans_ratio",
	"Total Assets Ratio": "total_assets_ratio",
	"Interest Expenses": "interest_expense",
	"Non-Interest Expenses": "non_interest_expense",
	"Personnel Expenses": "personnel_expense",
	"Occupancy Expenses": "occupancy_expense",
	"Other Expenses": "other_expense",
	"Total Operating Expenses": "total_operating_expenses",
	"Core Cost": "core_cost",
	"Total Cost": "total_cost",
	"Core Cost Ratio": "core_cost_ratio",
	"Total Cost Ratio": "total_cost_ratio",
	"Interest Incomes": "interest_income",
	"Non-Interest Income": "non_interest_income",
	"Other Incomes": "other_income",
	"Total Income": "total_income",
	"Total Income Ratio": "total_income_ratio",
	"Equity Over Total Assets": "eta",
	"Equity Over Total Deposits": "etd",
	"Non-performing Loans Ratio": "npl_ratio",
	"Loan Loss Provisions Ratio": "llp_ratio",
	"Returns Over Assets": "roa",
	"Returns Over Equity": "roe",
	"Net Interest Margin": "nim",
	"Cost-Income Ratios": "cir",
	"Liquid Assets Over Total Assets": "liquid_assets_over_total_assets",
	"Liquid Assets Over Total Deposits": "liquid_assets_over_total_deposits",
	"Cumulative Gaps Over Total Assets": "cumulative_gaps_over_total_assets",
	"Off-balance Sheet Activities": "off_balance_sheet",
	"Profits Before Tax": "profit_before_tax",
	"Profits After Tax": "profit_after_tax",
}

PERCENTAGE_LIKE_COLUMNS = [
	"employees_ratio",
	"branches_ratio",
	"total_deposits_ratio",
	"total_loans_ratio",
	"total_assets_ratio",
	"core_cost_ratio",
	"total_cost_ratio",
	"total_income_ratio",
	"eta",
	"etd",
	"npl_ratio",
	"llp_ratio",
	"roa",
	"roe",
	"nim",
	"cir",
	"liquid_assets_over_total_assets",
	"liquid_assets_over_total_deposits",
	"cumulative_gaps_over_total_assets",
]

IMPUTED_RATIO_COLUMNS = [
	"roa",
	"roe",
	"nim",
	"cir",
	"eta",
	"etd",
	"npl_ratio",
	"llp_ratio",
	"lta",
	"ltd",
	"gta",
]

FACT_COLUMNS = [
	"date_key",
	"bank_key",
	"total_assets",
	"total_deposits",
	"total_loans",
	"total_equity",
	"num_employees",
	"num_branches",
	"npl_amount",
	"loan_loss_provision",
	"interest_income",
	"interest_expense",
	"net_interest_income",
	"non_interest_expense",
	"personnel_expense",
	"other_expense",
	"profit_before_tax",
	"profit_after_tax",
	"off_balance_sheet",
	"npl_ratio",
	"llp_ratio",
	"roa",
	"roe",
	"nim",
	"cir",
	"eta",
	"etd",
	"lta",
	"ltd",
	"gta",
	"is_imputed",
]


def _resolve_workbook_path() -> Path:
	"""Resolve the raw workbook path from the configured raw data directory."""

	load_dotenv()
	raw_data_path = os.getenv("RAW_DATA_PATH", "./data/raw/")
	candidate_paths = [
		Path(raw_data_path) / WORKBOOK_NAME,
		Path("./data") / WORKBOOK_NAME,
		Path("./data/raw") / WORKBOOK_NAME,
	]

	for workbook_path in candidate_paths:
		if workbook_path.exists():
			return workbook_path

	raise FileNotFoundError(
		"Raw workbook not found. Looked in: "
		+ ", ".join(str(path) for path in candidate_paths)
		+ ". Check RAW_DATA_PATH."
	)


def _read_raw_frames(workbook_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Read the raw bank performance sheet and the bank lookup sheet."""

	raw_df = pd.read_excel(workbook_path, sheet_name=DATA_SHEET_NAME)
	banks_df = pd.read_excel(workbook_path, sheet_name=BANKS_SHEET_NAME)
	return raw_df, banks_df


def _coerce_numeric(series: pd.Series) -> pd.Series:
	"""Convert a raw series to numeric, preserving missing values."""

	if series.dtype == object:
		cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
		cleaned = cleaned.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
		return pd.to_numeric(cleaned, errors="coerce")
	return pd.to_numeric(series, errors="coerce")


def _normalize_percentage_like_columns(df: pd.DataFrame) -> pd.DataFrame:
	"""Normalize percentage-like columns into fractions when values look scaled."""

	df = df.copy()
	for column in PERCENTAGE_LIKE_COLUMNS:
		if column not in df.columns:
			continue
		series = _coerce_numeric(df[column])
		max_abs = series.abs().max(skipna=True)
		if pd.notna(max_abs) and max_abs > 1.5:
			df[column] = series / 100.0
			logger.info("Normalized percentage-style column '%s' by dividing by 100.", column)
		else:
			df[column] = series
	return df


def _build_bank_lookup(banks_df: pd.DataFrame) -> pd.DataFrame:
	"""Create a deterministic bank key lookup from the workbook bank list."""

	banks_df = banks_df.copy()
	banks_df.columns = [c.strip() if isinstance(c, str) else c for c in banks_df.columns]

	required_columns = {"No.", "Bank", "Bank Code", "Type of ownership"}
	missing = required_columns - set(banks_df.columns)
	if missing:
		raise ValueError(f"Banks List sheet is missing columns: {sorted(missing)}")

	banks_df = banks_df.dropna(subset=["No.", "Bank", "Bank Code", "Type of ownership"])

	lookup = (
		banks_df.loc[:, ["No.", "Bank", "Bank Code", "Type of ownership"]]
		.rename(
			columns={
				"No.": "bank_key",
				"Bank": "bank_name",
				"Bank Code": "bank_code",
				"Type of ownership": "bank_type",
			}
		)
		.sort_values("bank_key")
		.reset_index(drop=True)
	)
	lookup["bank_key"] = pd.to_numeric(lookup["bank_key"], errors="coerce").astype("Int64")
	lookup["bank_code"] = lookup["bank_code"].astype(str).str.strip().str.upper()
	lookup["bank_name"] = lookup["bank_name"].astype(str).str.strip()
	lookup["bank_type"] = lookup["bank_type"].astype(str).str.strip().str.upper()
	lookup["charter_capital"] = pd.NA  # Raw Excel does not contain charter capital data; initialized as NULL for future extension
	lookup = lookup.dropna(subset=["bank_key", "bank_code", "bank_name", "bank_type"])
	lookup = lookup.drop_duplicates(subset=["bank_code"], keep="first").reset_index(drop=True)
	return lookup


def _standardize_raw_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
	"""Rename source columns to canonical names and enforce core dtypes."""

	df = raw_df.copy()
	df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
	df = df.rename(columns=RAW_TO_CANONICAL)

	if "bank_code" not in df.columns or "year" not in df.columns:
		raise ValueError("Raw bank data must contain bank_code and year columns.")

	df["bank_code"] = df["bank_code"].astype(str).str.strip().str.upper()
	df["bank_type"] = df["bank_type"].astype(str).str.strip().str.upper()
	df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

	numeric_candidates = [column for column in df.columns if column not in {"bank_code", "bank_type"}]
	for column in numeric_candidates:
		if column == "year":
			continue
		df[column] = _coerce_numeric(df[column])

	df = _normalize_percentage_like_columns(df)

	df["date_key"] = (df["year"].astype("Int64") * 10000 + 1231).astype("Int64")
	df["net_interest_income"] = df["interest_income"] - df["interest_expense"]

	# Derive the ML-facing CAMELS ratios from the available raw financial fields.
	df["eta"] = df["eta"].where(df["eta"].notna(), df["total_equity"] / df["total_assets"])
	df["etd"] = df["etd"].where(df["etd"].notna(), df["total_equity"] / df["total_deposits"])
	df["roa"] = df["roa"].where(df["roa"].notna(), df["profit_after_tax"] / df["total_assets"])
	df["roe"] = df["roe"].where(df["roe"].notna(), df["profit_after_tax"] / df["total_equity"])
	df["nim"] = df["nim"].where(df["nim"].notna(), df["net_interest_income"] / df["total_assets"])
	df["cir"] = df["cir"].where(
		df["cir"].notna(),
		df["non_interest_expense"] / (df["net_interest_income"].abs() + df["non_interest_income"].abs()),
	)
	df["npl_ratio"] = df["npl_ratio"].where(df["npl_ratio"].notna(), df["npl_amount"] / df["total_loans"])
	df["llp_ratio"] = df["llp_ratio"].where(df["llp_ratio"].notna(), df["loan_loss_provision"] / df["total_loans"])
	df["lta"] = df["total_loans"] / df["total_assets"]
	df["ltd"] = df["total_loans"] / df["total_deposits"]
	df["gta"] = df["total_loans"] / df["total_assets"]

	return df


def _impute_missing_ratio_values(df: pd.DataFrame) -> pd.DataFrame:
	"""Impute 2002-2005 ratio gaps using bank medians, then global medians."""

	df = df.copy()
	df["is_imputed"] = False

	if "year" not in df.columns or "bank_code" not in df.columns:
		raise ValueError("Bank data must contain year and bank_code before imputation.")

	pre_2006_mask = df["year"].le(2005)

	def _fill_missing_values(column: str, missing_mask: pd.Series, bank_medians: pd.Series, global_median: float) -> None:
		"""Fill missing entries in a single ratio column and flag affected rows."""

		imputed_indices = []
		for idx in df.index[missing_mask]:
			bank_code = df.at[idx, "bank_code"]
			value = bank_medians.get(bank_code, pd.NA)
			if pd.isna(value):
				value = global_median
			df.at[idx, column] = value
			imputed_indices.append(idx)

		if imputed_indices:
			df.loc[imputed_indices, "is_imputed"] = True
			logger.info(
				"Imputed %d missing values in '%s'.",
				len(imputed_indices),
				column,
			)

	for column in IMPUTED_RATIO_COLUMNS:
		if column not in df.columns:
			continue

		bank_medians = df.loc[df["year"].ge(2006)].groupby("bank_code")[column].median()
		global_median = df.loc[df["year"].ge(2006), column].median()
		if pd.isna(global_median):
			global_median = df[column].median()
		if pd.isna(global_median):
			raise ValueError(f"Cannot compute a fallback median for '{column}'.")

		missing_mask = pre_2006_mask & df[column].isna()
		if not missing_mask.any():
			missing_mask = pd.Series(False, index=df.index)

		_fill_missing_values(column, missing_mask, bank_medians, global_median)

		remaining_mask = df[column].isna()
		if remaining_mask.any():
			bank_medians_all = df.groupby("bank_code")[column].median()
			global_median_all = df[column].median()
			if pd.isna(global_median_all):
				global_median_all = global_median
			_fill_missing_values(column, remaining_mask, bank_medians_all, global_median_all)

	return df


def _build_eda_summary(df: pd.DataFrame) -> pd.DataFrame:
	"""Summarize completeness and ranges for warehouse EDA."""

	summary_rows = []
	for column in [c for c in FACT_COLUMNS if c in df.columns]:
		series = df[column]
		summary_rows.append(
			{
				"column": column,
				"dtype": str(series.dtype),
				"missing_count": int(series.isna().sum()),
				"missing_pct": float(series.isna().mean()),
				"min": float(series.min(skipna=True)) if pd.api.types.is_numeric_dtype(series) else pd.NA,
				"max": float(series.max(skipna=True)) if pd.api.types.is_numeric_dtype(series) else pd.NA,
			}
		)
	return pd.DataFrame(summary_rows)


def transform_bank_performance(
	raw_df: pd.DataFrame,
	banks_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""Transform raw CAMELS data into fact and dimension DataFrames."""

	dim_bank_df = _build_bank_lookup(banks_df)
	df = _standardize_raw_frame(raw_df)

	df = df.merge(
		dim_bank_df.loc[:, ["bank_key", "bank_code"]],
		on="bank_code",
		how="left",
		validate="many_to_one",
	)
	if df["bank_key"].isna().any():
		missing_codes = sorted(df.loc[df["bank_key"].isna(), "bank_code"].dropna().unique())
		raise ValueError(f"Unable to map bank_key for bank codes: {missing_codes}")
	df["bank_key"] = df["bank_key"].astype("Int64")

	df = _impute_missing_ratio_values(df)

	# Audit checks before writing to the warehouse.
	ratio_columns = [column for column in IMPUTED_RATIO_COLUMNS if column in df.columns]
	if df[ratio_columns].isna().any().any():
		null_columns = df[ratio_columns].columns[df[ratio_columns].isna().any()].tolist()
		raise ValueError(f"Null values remain after imputation in: {null_columns}")

	if (df["npl_ratio"] < 0).any() or (df["npl_ratio"] > 1).any():
		logger.warning("npl_ratio contains values outside the [0, 1] range after normalization.")

	if df["date_key"].isna().any() or df["bank_key"].isna().any():
		raise ValueError("date_key and bank_key must be fully populated after transformation.")

	fact_df = df.loc[:, [column for column in FACT_COLUMNS if column in df.columns]].copy()
	fact_df = fact_df.drop_duplicates(subset=["date_key", "bank_key"], keep="first").reset_index(drop=True)

	eda_df = _build_eda_summary(df)
	return fact_df, dim_bank_df, eda_df


def save_processed_outputs(
	fact_df: pd.DataFrame,
	dim_bank_df: pd.DataFrame,
	eda_df: pd.DataFrame,
	output_dir: Path,
) -> tuple[Path, Path, Path]:
	"""Persist cleaned outputs for downstream checks and review."""

	output_dir.mkdir(parents=True, exist_ok=True)
	fact_path = output_dir / "fact_bank_performance_clean.csv"
	dim_path = output_dir / "dim_bank_clean.csv"
	eda_path = output_dir / "fact_bank_performance_eda_summary.csv"

	fact_df.to_csv(fact_path, index=False)
	# dim_bank_df.to_csv(dim_path, index=False) # Do not overwrite SCD Type 2 version
	eda_df.to_csv(eda_path, index=False)

	logger.info("Saved cleaned fact data to %s.", fact_path)
	logger.info("Saved EDA summary to %s.", eda_path)

	return fact_path, dim_path, eda_path


def run_bank_performance_etl() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""Execute the raw extraction, cleaning, and EDA pipeline for banks."""

	workbook_path = _resolve_workbook_path()
	raw_df, banks_df = _read_raw_frames(workbook_path)
	logger.info("Read %d raw rows from the bank performance workbook.", len(raw_df))
	fact_df, dim_bank_df, eda_df = transform_bank_performance(raw_df, banks_df)

	logger.info(
		"Cleaned bank performance fact rows: %d, bank dimensions: %d.",
		len(fact_df),
		len(dim_bank_df),
	)
	if len(dim_bank_df) != 46:
		logger.warning(
			"Bank lookup contains %d rows; project spec expects 46 banks. Check the raw workbook for a missing bank record.",
			len(dim_bank_df),
		)
	logger.info("Imputed rows: %d.", int(fact_df["is_imputed"].sum()))
	logger.info(
		"Year coverage: %d-%d.",
		int(raw_df["Year"].min()),
		int(raw_df["Year"].max()),
	)
	return fact_df, dim_bank_df, eda_df


def main() -> int:
	"""CLI entrypoint for bank performance cleaning and EDA."""

	parser = argparse.ArgumentParser(description="Clean CAMELS bank data and build EDA outputs.")
	parser.add_argument(
		"--output-dir",
		default=None,
		help="Directory for cleaned CSV outputs. Defaults to PROCESSED_DATA_PATH.",
	)
	args = parser.parse_args()

	load_dotenv()
	processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
	output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)

	import datetime
	now = datetime.datetime.utcnow()
	audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

	fact_df, dim_bank_df, eda_df = run_bank_performance_etl()
	
	# Append dynamic auditing columns
	fact_df["audit_key"] = audit_key
	fact_df["_created_at"] = now
	fact_df["_updated_at"] = now
	fact_df["_source_file"] = WORKBOOK_NAME

	save_processed_outputs(fact_df, dim_bank_df, eda_df, output_dir)

	logger.info("Bank ETL and EDA complete.")
	logger.info("Fact columns: %s", list(fact_df.columns))
	logger.info("Fact shape: %s", fact_df.shape)
	logger.info("EDA summary rows: %d", len(eda_df))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
