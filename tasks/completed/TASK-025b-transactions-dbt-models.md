---
id: TASK-025b
title: "Warehouse Expansion — Transactions dbt Models (Staging + Intermediate)"
status: todo
created: 2026-06-23
updated: 2026-06-23
branch: feature/TASK-025b-transactions-dbt-models
parent: TASK-025
---

## Objective

TASK-025 introduces two new transactional entities (sales and quotes) that flow through the full staging → intermediate pipeline. This subtask owns the dbt layer for those entities: the source YAML, two staging models, two intermediate models, and all associated tests (null checks and FK resolution).

The intermediate models (`unified_sales`, `unified_quotes`) are cleaned/typed Dynamic Tables. They do **not** join to `unified_customers` or `unified_products` — the intermediate layer is for cleaning and light transformation only. FK integrity is enforced by dbt tests, not enforced at query time via joins.

This task can be authored and compiled in parallel with TASK-025a (seed/ingestion) and TASK-025c (customers mart). A full `dbt build` run against Snowflake requires TASK-025a to be complete first.

---

## Acceptance Criteria

**Source YAML**

- [ ] 1. `dbt_project/models/staging/transactions/_transactions__sources.yml` exists, declares source name `transactions`, schema `de_agent_raw`, and tables `transactions__sales` and `transactions__quotes` with full column descriptions.

**Staging models**

- [ ] 2. `dbt_project/models/staging/transactions/transactions__sales.sql` exists. It is a 1:1 cast-and-rename of `{{ source('transactions', 'transactions__sales') }}`. No CTEs, no business logic. Cast guidance in Implementation Notes.
- [ ] 3. `dbt_project/models/staging/transactions/transactions__quotes.sql` exists. Same pattern — 1:1 cast-and-rename of `{{ source('transactions', 'transactions__quotes') }}`.
- [ ] 4. Both staging models are declared in `dbt_project/models/staging/transactions/_transactions__models.yml` with column descriptions.
- [ ] 5. Both staging models materialize as views (consistent with the `+materialized: view` default on the `staging` layer in `dbt_project.yml`).

**Intermediate models**

- [ ] 6. `dbt_project/models/intermediate/unified_sales.sql` exists. It materializes as a Snowflake Dynamic Table (`target_lag='1 minute'`, `snowflake_warehouse=var('snowflake_warehouse')`), selects from `{{ ref('transactions__sales') }}`, and applies only type enforcement and null handling — no joins to other intermediate models.
- [ ] 7. `dbt_project/models/intermediate/unified_quotes.sql` exists. Same pattern.
- [ ] 8. `unified_sales` is declared in `dbt_project/models/intermediate/_unified_sales__models.yml` with column descriptions and tests.
- [ ] 9. `unified_quotes` is declared in `dbt_project/models/intermediate/_unified_quotes__models.yml` with column descriptions and tests.

**Tests**

- [ ] 10. `not_null` tests declared on `unified_sales`: `sale_line_id`, `sale_id`, `customer_id`, `product_id`, `amount`.
- [ ] 11. `not_null` tests declared on `unified_quotes`: `quote_line_id`, `quote_id`, `customer_id`, `product_id`, `quoted_price`, `quantity`.
- [ ] 12. `unique` test on `unified_sales.sale_line_id` and `unified_quotes.quote_line_id`.
- [ ] 13. FK resolution: `customer_id` on `unified_sales` is tested against `customer_sk` in `unified_customers`. Use a dbt `relationships` test or a singular test in `dbt_project/tests/` — document which and why.
- [ ] 14. FK resolution: `customer_id` on `unified_quotes` is tested against `customer_sk` in `unified_customers`.
- [ ] 15. FK resolution: `product_id` on `unified_sales` is tested against `product_sk` in `unified_products`.
- [ ] 16. FK resolution: `product_id` on `unified_quotes` is tested against `product_sk` in `unified_products`.
- [ ] 17. `dbt parse` and `dbt compile` run clean with no errors or deprecation warnings.

---

## Implementation Notes

### Cast guidance for staging models

Staging models should match the column names in the raw schema (no renames needed — the raw names are already canonical). Apply casts only:

- `sale_line_id`, `sale_id`, `customer_id`, `product_id`, `stage`: `cast(... as varchar)`
- `amount`, `quoted_price`: `cast(... as double)`
- `quantity`: `cast(... as integer)`
- `close_date`, `expiry_date`: `cast(... as date)`
- `created_at`: `cast(... as timestamp)`

### Intermediate model pattern

Follow `dbt_project/models/intermediate/unified_customers.sql` exactly. The config block:

```sql
{{ config(
    materialized='dynamic_table',
    target_lag='1 minute',
    snowflake_warehouse=var('snowflake_warehouse')
) }}
```

### FK resolution test approach

Prefer the built-in `relationships` generic test — it is supported in dbt-snowflake 1.11+:

```yaml
- name: customer_id
  tests:
    - relationships:
        to: ref('unified_customers')
        field: customer_sk
```

If the Dynamic Table materialization causes the `relationships` test to fail at runtime, fall back to a singular test in `dbt_project/tests/` asserting zero orphan rows. Document the decision.

### Source schema name

The source YAML should declare `schema: de_agent_raw` (matching how `reference/snowflake` configures raw sources, e.g., `_acme__sources.yml`).

---

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
