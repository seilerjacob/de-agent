---
id: TASK-001
title: Initial medallion pipeline — CRM sources, ingestion, dbt curated layer
status: completed
created: 2026-06-01
updated: 2026-06-08
branch: main
---

## Objective

Build a demonstration Data Engineering pipeline that illustrates a medallion architecture and schema unification problem. Two mock CRM systems (Acme and Globe) use deliberately divergent schemas for the same conceptual entities (customers, products). The pipeline ingests both into a DuckDB lakehouse at the raw layer, then uses dbt Core to stage and unify them into a consistent intermediate schema — `int_unified_customers` and `int_unified_products`.

This project serves as a Claude skill demo for data engineering workflows at WWT.

## Acceptance Criteria

- [x] Acme CRM SQLite database seeds correctly via `sources/crm_acme/seed_acme.py`
- [x] Globe CRM SQLite database seeds correctly via `sources/crm_globe/seed_globe.py`
- [x] `ingestion/load_raw.py` loads all tables from both sources into the DuckDB raw layer using `raw_{source}__{table}` naming
- [x] dbt staging models normalize column names and types per CRM
- [x] dbt intermediate models unify both CRMs into a single canonical schema with surrogate keys
- [x] Full pipeline executes end-to-end via `python run_pipeline.py`

## Implementation Notes

Two sources with schema mismatches:
- Acme uses `contacts` / `inventory` tables with `email_address`, `first_name`+`last_name`, `company_name`, `item_name`, `stock_qty`
- Globe uses `customers` / `products` tables with `email`, `full_name`, `organization`, `product_title`, `available` (0/1 flag)

Ingestion loads tables as-is (no transformation at raw layer). dbt staging models rename to canonical columns. Intermediate models union both sources and add a `customer_sk` / `product_sk` surrogate key using `dbt_utils.generate_surrogate_key`.

DuckDB lakehouse at `warehouse/lakehouse.duckdb` (gitignored — generated artifact).

## Testing Notes

Pipeline verified by running `python run_pipeline.py` end-to-end. No automated tests existed at time of completion. Testing infrastructure added as TASK-003.

## Completion Notes

Merged to main directly (pre-maker-conventions). Automated tests and containerization are tracked as follow-on tasks under the maker onboarding plan. No technical debt that is not already tracked.
