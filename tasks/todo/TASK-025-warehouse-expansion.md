---
id: TASK-025
title: Warehouse Expansion — Sales, Quotes, and Customers Mart
status: todo
created: 2026-06-23
updated: 2026-06-23
branch: feature/task-025-warehouse-expansion
---

## Subtasks

This task has been broken into three parallel workstreams. Each subtask has its own task file and feature branch.

| Subtask | Scope | Blocks |
|---|---|---|
| [TASK-025a](TASK-025a-transactions-seed-and-ingestion.md) | Seed data + ingestion plumbing | Final `dbt build` only |
| [TASK-025b](TASK-025b-transactions-dbt-models.md) | Transactions staging + intermediate + tests | Nothing (can author/compile independently) |
| [TASK-025c](TASK-025c-customers-mart.md) | Customers mart model | Nothing (builds on existing `unified_customers`) |

**Merge order:** 025a, 025b, and 025c can all be opened as PRs against `reference/snowflake` simultaneously. TASK-025 is complete when all three are merged and a full `dbt build` passes.

---

## Objective

The Snowflake reference pipeline currently handles two source systems (Acme CRM and Globe CRM) and covers only the customer and product entity. The warehouse has no coverage of transactional data — sales or quotes — and the mart layer does not yet exist. This task extends the pipeline with two new transactional raw tables (sales and quotes), full staging and intermediate models for each, and a new `customers` mart model that provides a consumer-facing, deduplicated view of the unified customer.

The intent is to establish the mart layer pattern in this project, prove FK integrity between transactional data and the resolved customer/product intermediates, and give downstream consumers a clean canonical customer record. No aggregations or metrics are in scope.

This task targets the `reference/snowflake` branch. The branch is long-lived and is the merge target — not `dev` or `main`. The task is complete when the feature branch merges into `reference/snowflake`.

---

## Acceptance Criteria

**Seed data**

- [ ] 1. A new SQLite database exists at `sources/transactions/transactions.db` containing two tables: `sales` and `quotes`. The schema matches the column definitions in the Implementation Notes below.
- [ ] 2. The ingest script (or equivalent pipeline step) loads `sources/transactions/transactions.db` into the Snowflake raw schema, with tables named `transactions__sales` and `transactions__quotes`, following the existing `source__table` naming convention used by `acme__contacts`, `acme__inventory`, etc.
- [ ] 3. Seed data contains enough rows to exercise tests: at minimum 10 sales rows and 10 quotes rows, with intentional variety in `stage`, `status`, and `close_date`/`expiry_date` values.

**Source YAML**

- [ ] 4. A new source YAML file exists at `dbt_project/models/staging/transactions/_transactions__sources.yml` that declares the `transactions` source and describes both raw tables and all columns.

**Staging models**

- [ ] 5. `dbt_project/models/staging/transactions/transactions__sales.sql` exists. It is a 1:1 cast-and-rename of the raw `transactions__sales` table. No business logic. Column names match the canonical schema defined in the Implementation Notes.
- [ ] 6. `dbt_project/models/staging/transactions/transactions__quotes.sql` exists. It is a 1:1 cast-and-rename of the raw `transactions__quotes` table. No business logic.
- [ ] 7. Both staging models are declared in `dbt_project/models/staging/transactions/_transactions__models.yml` with column descriptions.

**Intermediate models**

- [ ] 8. `dbt_project/models/intermediate/unified_sales.sql` exists. It materializes as a Snowflake Dynamic Table (matching the pattern used by `unified_customers` and `unified_products`) and selects from `transactions__sales` staging. It applies only cleaning and type enforcement — no joins to `unified_customers` or `unified_products`.
- [ ] 9. `dbt_project/models/intermediate/unified_quotes.sql` exists. Same pattern as unified_sales — Dynamic Table, no joins to other intermediates.
- [ ] 10. Both intermediate models are declared in their respective schema YAML files under `dbt_project/models/intermediate/` with column descriptions and tests (see Tests section).

**Mart model**

- [ ] 11. `dbt_project/models/marts/customers.sql` exists. It selects from `{{ ref('unified_customers') }}` and applies: consumer-facing column renames (no raw source column names exposed), deduplication logic (if the same email appears from multiple source systems, retain one record using a deterministic tiebreaker — e.g., `row_number()` over `email` ordered by `source_system`), and no aggregations or metrics.
- [ ] 12. The `customers` mart is declared in `dbt_project/models/marts/_mart__models.yml` (create this file if the `marts/` directory or its schema file does not yet exist) with column descriptions and tests.
- [ ] 13. The mart exposes these consumer-facing columns at minimum: `customer_id` (surrogate key from `customer_sk`), `first_name`, `last_name`, `full_name`, `email`, `phone_number`, `organization`, `status`, `source_system`, `created_at`.

**Tests**

- [ ] 14. Null checks: `not_null` tests on the following fields, declared in the schema YAML files:
  - `unified_sales`: `sale_line_id`, `sale_id`, `customer_id`, `product_id`, `amount`
  - `unified_quotes`: `quote_line_id`, `quote_id`, `customer_id`, `product_id`, `quoted_price`, `quantity`
  - `customers` mart: `customer_id`, `email`, `full_name`
- [ ] 15. FK resolution — `customer_id` on `unified_sales` resolves to a `customer_sk` in `unified_customers`. Implement as a dbt `relationships` test or a custom singular test in `dbt_project/tests/`.
- [ ] 16. FK resolution — `customer_id` on `unified_quotes` resolves to a `customer_sk` in `unified_customers`. Same approach as criterion 15.
- [ ] 17. FK resolution — `product_id` on `unified_sales` resolves to a `product_sk` in `unified_products`. Same approach.
- [ ] 18. FK resolution — `product_id` on `unified_quotes` resolves to a `product_sk` in `unified_products`. Same approach.
- [ ] 19. `dbt test` runs clean (zero failures) for all new and existing models after this change.

**Pipeline integration**

- [ ] 20. `dbt run` completes without error for all new models when run against the Snowflake target.
- [ ] 21. Critical path end-to-end test passes (whatever test asserts the pipeline runs green from raw ingest through the mart layer).

---

## Implementation Notes

### Seed data design

Create a new SQLite database at `sources/transactions/transactions.db`. This is a shared "transactions" source — not CRM-source-specific — and should not be co-located with `acme_crm.db` or `globe_crm.db`.

**`sales` table — line-item grain:**

| Column | Type | Notes |
|---|---|---|
| `sale_line_id` | TEXT | Primary key. Unique per line item. |
| `sale_id` | TEXT | Header FK — groups line items into a sale event. |
| `customer_id` | TEXT | Must be a valid `customer_sk` from `unified_customers` in seed data. |
| `product_id` | TEXT | Must be a valid `product_sk` from `unified_products` in seed data. |
| `amount` | REAL | Line item dollar amount. |
| `stage` | TEXT | e.g., `closed_won`, `closed_lost`, `pending`. |
| `close_date` | TEXT | ISO 8601 date string. |
| `created_at` | TEXT | ISO 8601 datetime string. |

**`quotes` table — line-item grain:**

| Column | Type | Notes |
|---|---|---|
| `quote_line_id` | TEXT | Primary key. Unique per line item. |
| `quote_id` | TEXT | Header FK — groups line items into a quote. |
| `customer_id` | TEXT | Must be a valid `customer_sk` from `unified_customers` in seed data. |
| `product_id` | TEXT | Must be a valid `product_sk` from `unified_products` in seed data. |
| `quoted_price` | REAL | Unit quoted price. |
| `quantity` | INTEGER | Quantity quoted. |
| `status` | TEXT | e.g., `draft`, `sent`, `accepted`, `expired`. |
| `expiry_date` | TEXT | ISO 8601 date string. |
| `created_at` | TEXT | ISO 8601 datetime string. |

**Note on FK alignment in seed data:** The `customer_id` and `product_id` values in seed rows must match surrogate keys that will exist in `unified_customers` and `unified_products` after the dbt run. The surrogate key is generated by `generate_surrogate_key(['source_system', 'source_customer_id'])` for customers and `generate_surrogate_key(['source_system', 'source_product_id'])` for products. The engineer must pre-compute the expected surrogate keys from existing seed CRM data when populating transactions seed rows, or add a post-hook / seed script step that derives them programmatically.

**Open question for the engineer:** Decide whether the transactions seed database is populated by a hand-authored SQL/CSV script (simplest) or by a script that derives surrogate keys from the existing CRM seeds at runtime. Document the decision in the Implementation Notes section of this task file.

### Source YAML structure

Follow the pattern in `dbt_project/models/staging/acme/_acme__sources.yml`. The new file should be at `dbt_project/models/staging/transactions/_transactions__sources.yml` with source name `transactions`, schema `raw`, and tables `transactions__sales` and `transactions__quotes`.

### Staging model design

Follow the pattern in `dbt_project/models/staging/acme/acme__contacts.sql` — pure cast-and-rename, `{{ source('transactions', 'transactions__sales') }}` reference, no CTEs unless needed for clarity. Canonical column names after staging should match the column names in the seed table schema above (they are already canonical — no rename needed, only casts).

Cast guidance:
- `sale_line_id`, `sale_id`, `customer_id`, `product_id`, `stage`: `cast(... as varchar)`
- `amount`, `quoted_price`: `cast(... as double)` (or `float`)
- `quantity`: `cast(... as integer)`
- `close_date`, `expiry_date`: `cast(... as date)`
- `created_at`: `cast(... as timestamp)`

### Intermediate model design

Follow the pattern in `dbt_project/models/intermediate/unified_customers.sql`. Both `unified_sales` and `unified_quotes` should:
- Materialize as `dynamic_table` with `target_lag='1 minute'` and `snowflake_warehouse=env_var('SNOWFLAKE_WAREHOUSE')`
- Select from the corresponding staging model via `{{ ref(...) }}`
- Apply only type enforcement / light transformation (e.g., ensure nulls are handled, no business joins)
- NOT join to `unified_customers` or `unified_products` — the intermediate layer is for cleaning and unioning, not enrichment

### Mart model design

The `customers` mart lives at `dbt_project/models/marts/customers.sql`. Create the `marts/` directory if it does not exist.

The mart selects from `{{ ref('unified_customers') }}` and its job is:
1. Rename `customer_sk` to `customer_id` (consumer-facing name)
2. Deduplicate: if the same email appears from both Acme and Globe, retain one record. Suggested approach: `row_number() over (partition by lower(email) order by source_system)` and filter to `rn = 1`. Document the tiebreaker choice in the Implementation Notes.
3. Expose clean, consumer-facing column names — no raw source system column names (e.g., `source_customer_id` should be excluded or aliased if surfaced).

Materialization for the mart is a decision for the engineer — table, view, or dynamic table are all valid. Document the choice and rationale.

### Test patterns

For FK resolution tests, prefer dbt's built-in `relationships` generic test if it is available in the project's dbt version and adapter. Example YAML:

```yaml
- name: customer_id
  tests:
    - relationships:
        to: ref('unified_customers')
        field: customer_sk
```

If `relationships` tests are not supported or produce false negatives due to the dynamic table materialization, implement as a singular test in `dbt_project/tests/` that asserts zero orphan rows.

---

## Out of Scope

The following are explicitly excluded from this task:

- `mart_sales` or `mart_quotes` — no transactional mart models
- `lifetime_value` or any aggregated customer metrics
- Any aggregations on the `customers` mart (counts, sums, averages)
- Changes to `unified_customers` or `unified_products` (they already exist and are correct)
- Changes to existing staging models for Acme or Globe
- Any new source systems beyond the single shared `transactions` source

---

## Dependencies

- `unified_customers` and `unified_products` must be deployed and populated in the Snowflake environment before FK resolution tests can pass. These models already exist on `reference/snowflake`.
- Surrogate key values in the transactions seed data must align with the output of `generate_surrogate_key()` applied to the existing CRM seed data.

---

## Priority

**Medium.** This establishes the mart layer pattern and proves transactional FK integrity, both of which unblock future mart expansion tasks. Not time-critical but foundational.

---

## Testing Notes

*Fill in during testing. Record what was verified, how it was verified, and any edge cases that were checked. Note any acceptance criteria that were modified and why.*

---

## Completion Notes

*Fill in on merge. Summarize final state, identify any follow-on work, and note any technical debt incurred.*
