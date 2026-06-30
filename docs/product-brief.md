# Product Brief: Financial Data Analytics Platform

> **Status**: Executive Summary only. For full functional and non-functional requirements, refer to [`docs/prd.md`](./prd.md).

## Executive Summary

The **Financial Data Analytics Platform** is an end-to-end data solution that centralizes fragmented Vietnamese financial market data — covering stock price history for focus banks (BID, TCB, VCB, CTG) alongside 20 years of CAMELS performance data for 46 commercial banks — into a cloud-based Data Warehouse on Google BigQuery.

The platform applies three Machine Learning models to deliver actionable insights:

| Model | Task | Primary Output |
|-------|------|----------------|
| LSTM | Predict stock closing prices (T+1 to T+5) for BID, TCB, VCB, CTG | Short-term trading signals |
| K-Means + PCA | Segment 46 banks by financial behavior | Strategic bank groupings |
| Random Forest | Classify banks with NPL ≥ 3% as High Risk | Early warning for credit risk |

Results are delivered through interactive Looker Studio dashboards connected natively to BigQuery, targeting Risk Managers and Financial Analysts.

**Key Business Impact**: Reduces manual data aggregation and reporting time by 80% through automated ETL pipelines and a standardized Star Schema architecture.

## Document Index

| Document | Purpose |
|----------|---------|
| [`docs/prd.md`](./prd.md) | Full functional and non-functional requirements |
| [`docs/star-schema.md`](./star-schema.md) | Data Warehouse schema design |
| [`docs/ml-spec.md`](./ml-spec.md) | ML model specifications and acceptance criteria |
| [`docs/system-arch.md`](./system-arch.md) | System architecture and data flow |
| [`docs/etl-spec.md`](./etl-spec.md) | ETL transformation rules per source file |
| [`docs/data-dictionary.md`](./data-dictionary.md) | Variable definitions and data contracts |
| [`docs/dashboard-spec.md`](./dashboard-spec.md) | Looker Studio dashboard acceptance criteria |
| [`docs/tasks.md`](./tasks.md) | Atomic implementation task checklist |
| [`docs/env-config.md`](./env-config.md) | Environment setup guide |
| [`docs/proposal.md`](./proposal.md) | Academic research proposal (Vietnamese) |