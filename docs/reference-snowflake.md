# Snowflake Reference Implementation

This document describes the `reference/snowflake` branch: a complete port of
the medallion pipeline from the DuckDB baseline (`dev`) to Snowflake.

## Purpose

This is a **long-lived reference implementation**, not a feature branch.

- It is intentionally **not meant to be merged into `dev` or `main`**.
- Its job is demonstrative: show how each layer of the medallion architecture
  maps onto Snowflake primitives, with particular emphasis on **Dynamic
  Tables** for the intermediate layer.
- It diverges cleanly from `dev`. DuckDB-specific code and the `duckdb` /
  `dbt-duckdb` packages are removed here entirely; do not backport.

The `reference/` branch prefix deliberately signals this longevity. Do not
rename it to `feature/` or `chore/`.

## Architecture mapping

| Layer | DuckDB baseline (`dev`) | Snowflake (`reference/snowflake`) |
|---|---|---|
| Raw | DuckDB tables in schema `raw` | Snowflake tables in schema `RAW`, written via `snowflake-connector-python` |
| Staging | dbt `view` | dbt `view` (unchanged) |
| Intermediate | dbt `table` | dbt **Dynamic Table** (`materialized='dynamic_table'`) |

The pipeline creates three schemas inside your target database: `RAW`,
`STAGING`, and `INTERMEDIATE`.

## Prerequisites

You need a Snowflake account and a role with privileges to, in the target
database:

- `CREATE SCHEMA`
- `CREATE TABLE`
- `CREATE VIEW`
- `CREATE DYNAMIC TABLE`

You also need:

- A **virtual warehouse** for compute (ingestion writes, dbt builds, and the
  Dynamic Table refresh cycle all run on it).
- A **target database**. The pipeline manages the schemas inside it; it does
  not create the database itself.

Provisioning the account, warehouse, database, and grants is **out of scope**
for this branch — it assumes they already exist.

## Credentials

All credentials are read from environment variables. Nothing is hardcoded in
`ingestion/load_raw.py` or `dbt_project/profiles.yml`.

1. Copy the example file and fill it in:

   ```bash
   cp .env.snowflake.example .env.snowflake
   ```

   `.env.snowflake` is gitignored and must never be committed.

2. Load it into your shell before running anything:

   ```bash
   set -a && source .env.snowflake && set +a
   ```

### Account identifier format

The most common source of connection failures is `SNOWFLAKE_ACCOUNT`. Use:

- Preferred: `<orgname>-<account_name>` (e.g. `myorg-myaccount`)
- Legacy: `<account>.<region>.<cloud>` (e.g. `xy12345.us-east-1.aws`)

Find it under **Admin > Accounts** in Snowsight, or derive it from the
account URL.

### Authentication

Two options, controlled by which variable is set:

- **Password** — set `SNOWFLAKE_PASSWORD`.
- **Key-pair** — set `SNOWFLAKE_PRIVATE_KEY_PATH` to the absolute path of an
  unencrypted PKCS#8 `.p8` private key. If set, it takes precedence over the
  password.

`SNOWFLAKE_ROLE` is optional; if blank, the user's default role is used.

## Why Dynamic Tables for the intermediate layer

This is the key architectural difference from the DuckDB baseline.

A **Dynamic Table** is a first-class Snowflake object that wraps a query plus
a **target lag**. Snowflake automatically refreshes it as upstream data
changes, keeping it within the lag window. The benefits:

- **No orchestration for the refresh cycle.** No dbt scheduler, no Airflow
  DAG. On `dev`, dbt re-runs the full intermediate build on every pipeline
  invocation; here, you build the Dynamic Table once and Snowflake keeps it
  fresh.
- **Native primitive.** The refresh is managed by Snowflake, not the pipeline.

Both intermediate models set their materialization in their own `config()`
block so the settings are explicit and self-documenting:

```sql
{{ config(
    materialized='dynamic_table',
    target_lag='1 minute',
    snowflake_warehouse=env_var('SNOWFLAKE_WAREHOUSE')
) }}
```

- `target_lag='1 minute'` — the maximum staleness Snowflake will allow before
  refreshing. One minute is a reasonable demo default; production values
  depend on freshness requirements vs. compute cost.
- `snowflake_warehouse` — the warehouse Snowflake uses for the refresh,
  sourced from `SNOWFLAKE_WAREHOUSE`.

### Auto-refresh

To observe the auto-refresh: run the pipeline once, change source data, run
the ingestion step again (writing new rows to `RAW`), and the Dynamic Tables
update within the target lag **without a manual `dbt run`**. (Staging views
re-resolve on read, so they reflect new raw data immediately.)

## Known differences from the DuckDB baseline

- **Schema casing.** Snowflake uppercases unquoted identifiers. Schemas are
  `RAW`, `STAGING`, `INTERMEDIATE` (vs. DuckDB's lowercase `raw`,
  `main_intermediate`). A `generate_schema_name` macro
  (`dbt_project/macros/generate_schema_name.sql`) uses the custom schema name
  verbatim instead of dbt's default `<target>_<custom>` concatenation, so the
  layers land in clean `STAGING` / `INTERMEDIATE` schemas.
- **Raw table names are uppercase.** Ingestion writes `RAW.RAW_ACME__CONTACTS`
  etc. The `load_to_raw()` return dict still uses lowercase keys
  (`raw.raw_acme__contacts`) so callers and the DuckDB-era contract are
  unchanged.
- **Intermediate is a Dynamic Table, not a static table.** See above.
- **Summary step queries Snowflake.** `run_pipeline.py`'s `step_print_summary`
  reads the intermediate tables through the Snowflake connector instead of
  opening a local DuckDB file.

### SQL dialect compatibility

All intermediate SQL functions were reviewed and are valid in Snowflake
unchanged:

- `split_part(full_name, ' ', 1)` — valid; 1-based index, same as DuckDB.
- `contains(full_name, ' ')` — valid; `CONTAINS(string, substring)`, same
  argument order.
- `position(' ' in full_name)` — valid; `POSITION(substring IN string)`.
- `substr(...)` — valid (alias of `SUBSTRING`).
- `dbt_utils.generate_surrogate_key(...)` — works with the `dbt-snowflake`
  adapter (compiles to an `md5` expression).

No staging SQL changes were needed — the staging models use only `cast`,
column renames, and `case`/`when`, all dialect-neutral.

## Running the pipeline end-to-end

With `.env.snowflake` populated and sourced:

```bash
pip install -r requirements.txt
set -a && source .env.snowflake && set +a
python run_pipeline.py
```

Steps: seed SQLite sources → ingest into `RAW` → `dbt deps` → `dbt build`
(staging views + intermediate Dynamic Tables) → print row-count summary for
`int_unified_customers` and `int_unified_products`.

## Testing

- **Unit tests** (`tests/unit/`) run fully offline — the Snowflake connection
  and pandas writer are mocked. No credentials needed:

  ```bash
  pytest tests/unit/
  ```

- **Critical-path e2e test** (`tests/e2e/`) requires Snowflake. It loads
  `.env.snowflake` if present and **skips gracefully** when credentials are
  absent, so the offline suite stays green.

## CI

`profiles.yml` includes a `ci` output target structured for GitHub Actions:
it reads the same env vars (password auth only — no private key file on
runners), suitable for injection from repository secrets. Wiring the actual
secrets into the CI workflow is out of scope for this branch.
