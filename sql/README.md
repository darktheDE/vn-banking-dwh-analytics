# sql/

This directory contains SQL scripts for provisioning and managing the Google BigQuery Data Warehouse.

## File Index

| File | Description |
|------|-------------|
| `bigquery_schema.sql` | DDL statements to create all 5 Dimension Tables and 5 Fact Tables with correct partitioning and clustering. |

## Usage

The SQL in `bigquery_schema.sql` can be executed via:
1. The **BigQuery Console** (GCP Web UI) — paste and run.
2. The **`bq` CLI tool**: `bq query --use_legacy_sql=false < sql/bigquery_schema.sql`
3. The Python ETL setup scripts in `src/etl/` which use the BigQuery Python client API.

## Schema Reference

For the full schema specification including all field types, foreign key relationships, and optimization rationale, see [`docs/star-schema.md`](../docs/star-schema.md).
