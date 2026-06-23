---
id: TASK-025b
title: "Warehouse Expansion — Transactions dbt Models (Staging + Intermediate)"
status: completed
created: 2026-06-23
updated: 2026-06-23
branch: feature/TASK-025b-transactions-dbt-models
parent: TASK-025
---

## Objective

TASK-025 introduces two new transactional entities (sales and quotes) that flow through the full staging → intermediate pipeline. This subtask owns the dbt layer for those entities: the source YAML, two staging models, two intermediate models, and all associated tests (null checks and FK resolution).

The intermediate models (`int_unified_sales`, `int_unified_quotes`) are cleaned/typed Dynamic Tables. They do **not** join to `int_unified_customers` or `int_unified_products` — the intermediate layer is for cleaning and light transformation only. FK integrity is enforced by dbt tests, not enforced at query time via joins.

This task can be authored and compiled in parallel with TASK-025a (seed/ingestion) and TASK-025c (customers mart). A full `dbt build` run against Snowflake requires TASK-025a to be complete first.

---

## Acceptance Criteria

**Source YAML**

- [x] 1. Source YAML exists, declares source name `raw_transactions`, schema `raw`, and tables `raw_transactions__sales` and `raw_transactions__quotes` with full column descriptions. (See note 1 on naming.)

**Staging models**

- [x] 2. `stg_transactions__sales.sql` exists — 1:1 cast of the source. No CTEs, no business logic.
- [x] 3. `stg_transactions__quotes.sql` exists — same pattern.
- [x] 4. Both staging models declared in `_transactions__models.yml` with column descriptions.
- [x] 5. Both staging models materialize as views (via the `+materialized: view` default on the `staging` layer).

**Intermediate models**

- [x] 6. `int_unified_sales.sql` exists — Dynamic Table (`target_lag='1 minute'`, `snowflake_warehouse=env_var('SNOWFLAKE_WAREHOUSE')`), selects from `ref('stg_transactions__sales')`, type enforcement + null handling only, no joins.
- [x] 7. `int_unified_quotes.sql` exists — same pattern.
- [x] 8. `int_unified_sales` declared in `_int_sales__models.yml` with column descriptions and tests.
- [x] 9. `int_unified_quotes` declared in `_int_quotes__models.yml` with column descriptions and tests.

**Tests**

- [x] 10. `not_null` tests on `int_unified_sales`: `sale_line_id`, `sale_id`, `customer_id`, `product_id`, `amount`.
- [x] 11. `not_null` tests on `int_unified_quotes`: `quote_line_id`, `quote_id`, `customer_id`, `product_id`, `quoted_price`, `quantity`.
- [x] 12. `unique` test on `int_unified_sales.sale_line_id` and `int_unified_quotes.quote_line_id`.
- [x] 13. FK resolution: `int_unified_sales.customer_id` → `customer_sk` in `int_unified_customers` (relationships test).
- [x] 14. FK resolution: `int_unified_quotes.customer_id` → `customer_sk` in `int_unified_customers` (relationships test).
- [x] 15. FK resolution: `int_unified_sales.product_id` → `product_sk` in `int_unified_products` (relationships test).
- [x] 16. FK resolution: `int_unified_quotes.product_id` → `product_sk` in `int_unified_products` (relationships test).
- [ ] 17. `dbt parse` and `dbt compile` run clean — BLOCKED: Bash is denied in this environment, so I could not execute dbt. See Testing Notes.

---

## Implementation Notes

### Naming convention reconciliation (key decision)

The task prompt's literal file/source names were written against the older `main`/DuckDB checkout. The authoritative `reference/snowflake` branch (this worktree) uses a different, consistent naming scheme, which I followed for consistency (PRINCIPLES: reuse existing patterns, lowest complexity):

- Source name: `raw_transactions` (not `transactions`); source tables `raw_transactions__sales` / `raw_transactions__quotes`; schema `raw` (not `de_agent_raw`). Matches `_acme__sources.yml` / `_globe__sources.yml` and `ingestion/load_raw.py`'s `RAW_{SOURCE}__{TABLE}` naming.
- Staging models: `stg_transactions__sales` / `stg_transactions__quotes` (the `stg_` prefix is the established convention: `stg_acme__contacts`, etc.).
- Intermediate models: `int_unified_sales` / `int_unified_quotes` (the `int_unified_` prefix matches `int_unified_customers` / `int_unified_products`).
- Warehouse config uses `env_var('SNOWFLAKE_WAREHOUSE')`, matching both existing intermediate models. The prompt's `var('snowflake_warehouse')` does not exist on this branch (no `vars:` block, no `local/profiles.yml`); the profile lives at `dbt_project/profiles.yml`.
- FK relationships target `int_unified_customers` / `int_unified_products` (the real model names on this branch).

### Casts

Staging and intermediate both apply the casts specified in the task: varchar for id/stage/status, double for amount/quoted_price, integer for quantity, date for close_date/expiry_date, timestamp for created_at. Intermediate adds `current_timestamp as loaded_at`, matching the existing intermediate models.

### FK test approach

Used the built-in `relationships` generic test in the model YAML (per the task's preferred approach). YAML style matches the existing intermediate YAMLs on this branch (bare nested keys, no `arguments:` wrapper). No singular fallback test was needed at authoring time.

### Files created

- `dbt_project/models/staging/transactions/_transactions__sources.yml`
- `dbt_project/models/staging/transactions/stg_transactions__sales.sql`
- `dbt_project/models/staging/transactions/stg_transactions__quotes.sql`
- `dbt_project/models/staging/transactions/_transactions__models.yml`
- `dbt_project/models/intermediate/int_unified_sales.sql`
- `dbt_project/models/intermediate/int_unified_quotes.sql`
- `dbt_project/models/intermediate/_int_sales__models.yml`
- `dbt_project/models/intermediate/_int_quotes__models.yml`

No existing models, ingestion code, or seed scripts were modified. No `marts/` directory created.

## Testing Notes

`dbt parse` / `dbt compile` (AC #17) could NOT be executed: the Bash tool is denied in this environment. All files were authored by directly reading and mirroring the analogous, already-parsing models on this branch (`stg_acme__*`, `int_unified_customers/products`, their YAMLs), so the structure matches known-good patterns. A `dbt parse --project-dir dbt_project --profiles-dir dbt_project` should be run by the integration agent (which has shell access) to confirm AC #17 before merge. Note the source tables `raw_transactions__*` are produced by TASK-025a, so a full `dbt build` is blocked on 025a; `parse`/`compile` only require the source declaration, which exists.

## Completion Notes

Merged into `reference/snowflake` via `--no-ff` (merge commit "merge TASK-025b:
transactions dbt models"). Completion point for a reference-scoped task per
`.project/WORKFLOW.md`.

IMPORTANT — the Implementation Notes / Acceptance Criteria above describe an
EARLIER draft that does not match what actually shipped. The names that merged
are the prefix-free forms that match the current `reference/snowflake`
convention (`acme__contacts`, `globe__customers`, `unified_customers`,
`unified_products` — no `stg_`/`int_` prefixes; schema-per-layer landed in
`1617dd4`):

| Notes above say | What actually merged |
|---|---|
| source `raw_transactions`, schema `raw` | source `transactions`, schema `de_agent_raw` |
| `stg_transactions__sales` / `..__quotes` | `transactions__sales` / `transactions__quotes` |
| `int_unified_sales` / `int_unified_quotes` | `unified_sales` / `unified_quotes` |
| `env_var('SNOWFLAKE_WAREHOUSE')` warehouse | `var('snowflake_warehouse')` (matches `unified_customers`) |
| FK targets `int_unified_customers/products` | FK targets `unified_customers/products` |

The shipped files are the correct, consistent versions. Verified by static
inspection during integration: every `ref()`/`source()` in the transactions
staging and intermediate models resolves to an existing model/source, and the
source declaration (`transactions` / `de_agent_raw` / `transactions__sales` /
`transactions__quotes`) matches the raw table names produced by TASK-025a's
`load_raw.py`.

The Implementation Notes section was left as-authored for audit transparency
rather than retroactively rewritten — this Completion Notes block is the
authoritative record of what merged.

Not run during integration (harness sandbox denies the dbt binary): `dbt parse`,
`dbt compile`, `dbt build`. AC #17 remains unverified by execution and must be
confirmed by the user. A full `dbt build` additionally requires a live Snowflake
connection and the transactions raw tables loaded by TASK-025a.
