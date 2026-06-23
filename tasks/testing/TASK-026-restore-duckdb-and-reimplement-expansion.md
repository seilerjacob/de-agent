---
id: TASK-026
title: Restore DuckDB on dev (undo Snowflake contamination) and re-implement warehouse expansion
status: testing
created: 2026-06-23
updated: 2026-06-23
branch: fix/dev-restore-duckdb
---

## Objective

`dev` had been contaminated with the Snowflake port: commit `96aee18`
("reference(snowflake): port pipeline from DuckDB to Snowflake (TASK-023)") was
committed onto `dev` against its own stated intent ("intentionally not for merge
to dev"). As a result `dev` targeted Snowflake (profile `de_agent_snowflake`,
Dynamic Tables, `snowflake-connector-python`) instead of DuckDB. `dev` must
target DuckDB/DuckLake only; Snowflake belongs solely on `reference/snowflake`
(and in documentation about that reference branch).

This task does two things, dev-first per the standard development process:
1. Revert-forward to DuckDB on `dev` (no history rewrite), while KEEPING the
   TASK-024 naming work (prefix-free model/source names + local
   `generate_surrogate_key` macro), which was intentional and platform-agnostic.
2. Re-implement the warehouse expansion (transactions sales/quotes models +
   customers mart) that was previously built on `reference/snowflake`, now
   targeting DuckDB.

## Acceptance Criteria

- [x] `dev` dbt profile is DuckDB (`de_agent_lakehouse`), no `dbt-snowflake`/
      `snowflake-connector-python` in requirements
- [x] No Snowflake references remain in source (models, macros, ingestion,
      pipeline, tests); `.env.snowflake.example` and `docs/reference-snowflake.md`
      removed from dev (they live on `reference/snowflake`)
- [x] TASK-024 naming preserved (prefix-free names, local surrogate-key macro)
- [x] Intermediate models materialized as DuckDB tables (no `dynamic_table`)
- [x] Transactions seed + staging + intermediate models + customers mart added,
      DuckDB-targeted, refs/sources resolve (verified statically)
- [x] Raw table naming reconciled: `load_raw.py` writes `raw.{source}__{table}`
      to match the TASK-024 source YAMLs (dropped the old `raw_` prefix)
- [ ] Critical path test passes locally (`pytest tests/e2e/test_pipeline.py`) —
      MUST be run by a human; the agent harness cannot execute dbt or pytest
- [ ] Unit tests pass locally (`pytest tests/unit/`)
- [ ] PR references this task

## Implementation Notes

Two commits on `fix/dev-restore-duckdb` (cut from `dev`):
1. `revert(platform): restore DuckDB pipeline on dev (undo TASK-023 Snowflake port)`
2. `feat(TASK-025): warehouse expansion (transactions + customers mart) on DuckDB`

Key decisions:
- **Revert-forward, not history rewrite** (user choice). Snowflake commits remain
  in `dev` history; the branch tip restores DuckDB via new commits.
- **Schema naming (Option A):** kept the passthrough `generate_schema_name` macro
  so layers land in clean `staging` / `intermediate` / `marts` schemas (profile
  `schema: main`). Hence e2e/run_pipeline query `intermediate.unified_customers`,
  etc.
- **Raw naming reconciliation:** the last clean DuckDB commit (`1f7260c`) wrote
  `raw.raw_{source}__{table}`, but TASK-024 source YAMLs declare table
  `acme__contacts` in schema `raw`. So `load_raw.py` now writes
  `raw.{source}__{table}` (e.g. `raw.acme__contacts`) — verified against the
  staging models' `source()` calls.
- **dbt test-arg syntax:** dev's TASK-024 YAMLs use the nested `arguments:` form
  (dbt 1.10+). The ported TASK-025 `relationships` tests were rewritten from the
  reference branch's flat form to the nested `arguments:` form to match.
- **SQL portability:** audited all SQL — `||`, `split_part`, `contains`,
  `position(x in y)`, `substr`, `md5`, `row_number()`, casts — all DuckDB-native.
  The only Snowflake-specific constructs were the `dynamic_table` config blocks,
  which were removed (materialization now via `dbt_project.yml`).
- **Surrogate-key alignment:** the transactions seed computes FKs as
  `md5(f"{system}-{id}")`, which matches dev's local `generate_surrogate_key`
  macro for the referenced CRM rows (no null inputs). Asserted by
  `tests/unit/test_seed_transactions.py`.

## Testing Notes

The agent harness denies execution of the `dbt` binary and the Python
interpreter (even with sandbox disabled), so `dbt parse`/`dbt build` and
`pytest` could NOT be run here. Verification performed statically:
- every `ref()`/`source()` in new/changed models resolves to an existing
  model or source declaration;
- every column projected by `customers.sql` exists in `unified_customers`;
- raw table names produced by `load_raw.py` match the source YAML declarations;
- no Snowflake references remain in source directories.

A human must run, on `dev` with DuckDB installed:
```
pip install -r requirements.txt -r requirements-dev.txt
(cd dbt_project && dbt deps --profiles-dir .)   # packages.yml is empty: no-op
pytest tests/unit/ -v
pytest tests/e2e/ -v -s                           # critical path
```

## Completion Notes

*Fill in on merge to dev.*
