---
id: TASK-023
title: Port pipeline to Snowflake as a reference implementation
status: in_progress
created: 2026-06-19
updated: 2026-06-22
branch: reference/snowflake
---

## Objective

The current pipeline runs end-to-end on DuckDB — a local file-based warehouse that is ideal for development and testing but is not representative of a production cloud data warehouse environment. This task creates a long-lived `reference/snowflake` branch that ports the entire pipeline to Snowflake, serving as a canonical reference implementation for teams evaluating or adopting Snowflake as their target warehouse.

The branch is intentionally long-lived and not meant to be merged back to `dev`. Its purpose is demonstrative: show how each layer of the medallion architecture maps to Snowflake primitives, with particular emphasis on using Snowflake Dynamic Tables for the intermediate layer (replacing static dbt materializations with continuously auto-refreshing objects). This branch gives future developers a working, runnable example of the Snowflake variant alongside the DuckDB baseline.

The scope is a clean swap: SQLite sources remain unchanged, the Python ingestion layer switches from DuckDB to the Snowflake connector, dbt is reconfigured for Snowflake with `dbt-snowflake`, staging models remain views, and intermediate models are ported to Snowflake Dynamic Tables. DuckDB-specific code and the `duckdb` package are removed from this branch entirely.

## Acceptance Criteria

### Branch and credential setup
- [x] Branch `reference/snowflake` is created off `dev` and pushed to the remote
- [x] `.env.snowflake` is added to `.gitignore` (the file itself is never committed)
- [x] `.env.snowflake.example` is committed with all required variables documented, including inline comments explaining each variable's purpose and where to find the value in Snowflake (e.g., account identifier format, warehouse vs. virtual warehouse naming)
- [x] Both `ingestion/load_raw.py` and `dbt_project/profiles.yml` read credentials exclusively from `.env.snowflake` (or environment variables sourced from it) — no hardcoded values anywhere

### Python ingestion layer (`ingestion/load_raw.py`)
- [x] `duckdb` import and all DuckDB connection code are removed
- [x] `snowflake-connector-python` (with `pandas` extras) replaces `duckdb` as the warehouse write target
- [x] The function signature of `load_to_raw()` is preserved (same inputs/outputs) so callers require no changes
- [x] Each source table is written to Snowflake as `RAW.RAW_{SOURCE}__{TABLE}` (schema `RAW`, table name uppercased)
- [x] The `RAW` schema is created if it does not exist before any table writes
- [x] Each table is fully replaced on each run (DROP + write_pandas overwrite)
- [ ] Running `python -m ingestion.load_raw` completes without error and prints per-table row counts — **requires a live Snowflake account to verify**

### dbt configuration
- [x] `dbt-snowflake` added to `requirements.txt`; `dbt-duckdb` removed
- [x] `dbt_project/profiles.yml` rewritten for Snowflake — profile `de_agent_snowflake`, all params from env vars
- [x] `profiles.yml` includes both `dev` and `ci` output targets
- [ ] `dbt deps` runs successfully against the Snowflake profile — **needs live account/network to verify**

### Staging models (views)
- [x] All four staging models remain `view` (no materialization changes)
- [x] DuckDB-dialect SQL reviewed — staging models use only `cast` / renames / `case`; no changes needed
- [ ] `dbt build --select staging` completes — **requires live Snowflake**
- [ ] Source freshness / schema tests pass — **requires live Snowflake**

### Intermediate models (Dynamic Tables)
- [x] `int_unified_customers` and `int_unified_products` materialized as `dynamic_table` via per-model `config()`
- [x] Each config includes `target_lag='1 minute'` (documented) and `snowflake_warehouse=env_var('SNOWFLAKE_WAREHOUSE')`
- [x] SQL reviewed for Snowflake compatibility — `split_part`, `contains`, `position(x IN y)`, `substr`, `generate_surrogate_key` all valid unchanged (see Implementation Notes)
- [ ] `dbt build --select intermediate` completes; both Dynamic Tables created — **requires live Snowflake**
- [ ] Dynamic Tables auto-refresh on new raw data — **requires live Snowflake**

### Pipeline runner (`run_pipeline.py`)
- [x] All `duckdb` imports removed
- [x] `step_print_summary()` rewritten to query INTERMEDIATE via the Snowflake connector
- [ ] `python run_pipeline.py` runs end-to-end — **requires live Snowflake**
- [ ] Printed summary shows correct row counts — **requires live Snowflake**

### Dependency cleanup
- [x] `duckdb>=0.10.0` removed from `requirements.txt`
- [x] `snowflake-connector-python[pandas]` and `dbt-snowflake` added with version pins
- [ ] `pip install -r requirements.txt` in a clean venv — **could not run in sandbox (no network / Py3.11)**; pins chosen to be mutually compatible

### Documentation
- [x] `docs/reference-snowflake.md` committed (purpose, prerequisites, credentials, Dynamic Tables rationale, known differences, how to run)
- [x] Root `README.md` updated to reference `reference/snowflake` and link the doc

### Testing
- [x] Unit tests updated to remove DuckDB dependence; Snowflake connection + `write_pandas` mocked — run fully offline, no credentials
- [x] E2E test loads `.env.snowflake` if present and `skipif`-skips gracefully when creds absent
- [ ] `pytest tests/unit/` passes offline — **logic/syntax validated; could not execute in sandbox (snowflake-connector-python not installable here)**

## Implementation Notes

**Branch / worktree:** Implemented in an isolated git worktree branch; commits to be reconciled onto `reference/snowflake` (which already exists at dev's tip). `dev` was not touched.

**Ingestion (`ingestion/load_raw.py`):**
- New `get_snowflake_connection()` reads all params from env. Key-pair auth (`SNOWFLAKE_PRIVATE_KEY_PATH` → connector's `private_key_file`) takes precedence over password; `SNOWFLAKE_ROLE` omitted when blank so the connector applies the user default.
- Writes use `snowflake.connector.pandas_tools.write_pandas` with `auto_create_table=True, overwrite=True, quote_identifiers=False`. Combined with an explicit `DROP TABLE IF EXISTS` this gives full-replace semantics matching the DuckDB baseline. `quote_identifiers=False` lets Snowflake uppercase the lowercase SQLite column names (e.g. `contact_id` → `CONTACT_ID`), which matches how the unquoted dbt staging SQL resolves them.
- `load_to_raw()` keeps its exact signature. `warehouse_path` is now unused (documented) but retained so callers need no change. Return dict keeps **lowercase** keys (`raw.raw_acme__contacts`) to preserve the prior contract even though physical tables are uppercase.

**Schema strategy:** Added `dbt_project/macros/generate_schema_name.sql` so custom schema names (`staging`, `intermediate`) are used verbatim instead of dbt's default `<target>_<custom>` concatenation. Result: clean `RAW` / `STAGING` / `INTERMEDIATE` schemas. Without this, models would land in `STAGING_STAGING` / `STAGING_INTERMEDIATE`. Removed `+materialized: table` from the intermediate group in `dbt_project.yml` since materialization is now set per-model.

**SQL dialect review (no changes required):**
- `split_part(full_name, ' ', 1)` — valid in Snowflake, 1-based index, identical to DuckDB.
- `contains(full_name, ' ')` — Snowflake `CONTAINS(string, substring)`, same argument order. Valid.
- `position(' ' in full_name)` — Snowflake `POSITION(substring IN string)`. Valid.
- `substr(...)` — alias of `SUBSTRING` in Snowflake. Valid.
- `dbt_utils.generate_surrogate_key([...])` — supported by the dbt-snowflake adapter (compiles to `md5`). No incompatibility found.
- Staging models: only `cast`, column renames, `case`/`when` — all dialect-neutral. No changes.

**Version pins:** `dbt-snowflake>=1.8.0` (dynamic_table materialization + target_lag/snowflake_warehouse config stable since the 1.6/1.7 line; >=1.8 is safely within the dbt-core 1.x family and compatible with dbt-core 1.11). `snowflake-connector-python[pandas]>=3.12.0`.

**Testing approach:** Unit tests mock the connection and `write_pandas` so they assert on executed SQL (RAW schema creation, `DROP TABLE IF EXISTS RAW.RAW_*`, uppercase table naming) and on auth-param selection — all offline, no credentials. E2E test parses `.env.snowflake` itself (no extra dependency) and `pytest.mark.skipif` skips when required vars are absent.

## Verification limitations (sandbox)

The implementation environment had no Snowflake account and no network/Python-3.11 to build a venv, so the following were validated statically only and need a live account (or a properly provisioned local venv) to confirm:
- `python -m ingestion.load_raw`, `python run_pipeline.py`, and all `dbt deps`/`dbt build` steps.
- `pytest tests/unit/` execution (syntax compiled clean via `py_compile`; mock design reviewed; but `snowflake-connector-python` could not be installed here to import the module under test).
- `pip install -r requirements.txt` in a clean venv (pins chosen for mutual compatibility but not executed).

All Python files pass `py_compile`; all YAML config files parse via `yaml.safe_load`.

## Scope

(unchanged from original — see git history / sections above)

## Notes

**On the branch:** `reference/snowflake` is long-lived and standalone; do not merge to `dev`/`main`, do not rename to `feature/`/`chore/`.
