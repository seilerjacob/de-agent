---
id: TASK-003
title: Add automated testing foundation — pytest unit, integration, and critical path
status: testing
created: 2026-06-08
updated: 2026-06-08
branch: feature/testing-foundation
---

## Objective

The project has no automated tests. Add a pytest-based test suite covering: unit tests for the ingestion column-mapping logic in `ingestion/load_raw.py`, and a critical path end-to-end test that runs the full pipeline (seed → ingest → dbt build) and asserts the expected shape of the curated output tables. The dbt model YAML files already declare generic tests (unique, not_null, accepted_values) — these are exercised by the critical path test via `dbt build`.

## Acceptance Criteria

- [ ] `tests/unit/test_load_raw.py` exists with unit tests for `extract_sqlite_tables` covering: happy path, missing DB file returns empty or raises, table naming
- [ ] `tests/e2e/test_pipeline.py` exists with a critical path test that seeds both CRMs, runs `load_to_raw`, runs `dbt build`, and asserts `int_unified_customers` and `int_unified_products` row counts and column presence
- [ ] All tests pass locally via `pytest tests/`
- [ ] `requirements-dev.txt` (or updated `requirements.txt`) includes `pytest`
- [ ] Makefile `test`, `test-unit`, `test-e2e` targets are present (Makefile may be authored in TASK-004 if that branch lands first — coordinate)
- [ ] Critical path test passes locally

## Implementation Notes

Created a two-layer pytest test suite on branch `feature/testing-foundation`:

**`requirements-dev.txt`** — adds `pytest>=7.0` as a dev dependency.

**`tests/unit/test_load_raw.py`** — five unit tests using `tmp_path` fixtures for full isolation (no shared state, no seeded CRM databases):
- `TestExtractSqliteTables.test_single_table_columns_and_row_count` — happy path: creates a temp SQLite with one table, asserts DataFrame columns and row count.
- `TestExtractSqliteTables.test_multiple_tables_both_extracted` — creates two tables, verifies both are returned.
- `TestExtractSqliteTables.test_excludes_sqlite_internal_tables` — asserts no key starts with `sqlite_`.
- `TestExtractSqliteTables.test_empty_table_still_returned` — verifies schema-only tables are included with 0 rows.
- `TestLoadToRaw.test_skips_missing_source_returns_empty` — passes a non-existent path, asserts empty dict and no exception.
- `TestLoadToRaw.test_loads_tables_into_duckdb` — creates a temp SQLite, calls `load_to_raw`, asserts key and row count.
- `TestLoadToRaw.test_naming_convention_pattern` — verifies keys follow `raw.raw_{source}__{table}` pattern.
- `TestLoadToRaw.test_warehouse_directory_created_automatically` — verifies parent dirs are created.
- `TestLoadToRaw.test_row_count_matches_source` — loads 50 rows, verifies count in result dict.

**`tests/e2e/test_pipeline.py`** — one critical path test (`test_full_pipeline_critical_path`) that:
1. Calls `seed_acme()` and `seed_globe()` to populate the real SQLite sources.
2. Calls `load_to_raw()` with no arguments and asserts 4 tables returned.
3. Runs `dbt build --profiles-dir <dbt_project_dir>` as a subprocess from `cwd=dbt_project/`; asserts `returncode == 0` with stderr in failure message.
4. Opens `warehouse/lakehouse.duckdb` read-only and asserts row counts (22 customers, 21 products) and expected column presence on both intermediate tables.

## Testing Notes

Implementation is complete. To validate:

- Run unit tests in isolation: `pytest tests/unit/ -v`
- Run critical path end-to-end test: `pytest tests/e2e/ -v`
- Run full suite: `pytest tests/ -v`

Unit tests use `tmp_path` for full isolation — they do not touch the real warehouse or CRM databases. The e2e test exercises the real project paths and requires the full dependency stack (`dbt-duckdb`, `duckdb`, `pandas`) to be installed.

## Completion Notes

*Fill in on merge.*
