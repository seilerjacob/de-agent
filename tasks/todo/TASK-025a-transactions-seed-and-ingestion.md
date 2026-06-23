---
id: TASK-025a
title: "Warehouse Expansion — Transactions Seed Data & Ingestion Plumbing"
status: todo
created: 2026-06-23
updated: 2026-06-23
branch: feature/TASK-025a-transactions-seed-ingestion
parent: TASK-025
---

## Objective

TASK-025 introduces two new transactional raw tables (`sales` and `quotes`) that are not CRM-source-specific. They live in a shared `transactions` source. This subtask owns everything below the dbt layer: creating the SQLite seed database, writing the seed script, and updating the ingestion pipeline to load the new source into the Snowflake raw schema.

The output of this task is that `DE_AGENT_RAW.TRANSACTIONS__SALES` and `DE_AGENT_RAW.TRANSACTIONS__QUOTES` exist in Snowflake, are populated with realistic test data, and change tracking is enabled on both — identical to how the existing CRM tables are handled.

This task can run in parallel with TASK-025b (dbt models) and TASK-025c (customers mart). It is a blocking dependency only for the final end-to-end `dbt build` run.

---

## Acceptance Criteria

- [ ] 1. `sources/transactions/seed_transactions.py` exists and, when run, creates `sources/transactions/transactions.db` containing `sales` and `quotes` tables matching the schemas below.
- [ ] 2. `sources/transactions/transactions.db` is gitignored (the generated artifact should not be committed; the seed script is the source of truth).
- [ ] 3. Seed data contains at minimum 10 `sales` rows and 10 `quotes` rows. Rows must include variety in `stage`, `status`, `close_date`, and `expiry_date`. At least two `sale_id` values must have multiple line items, and at least two `quote_id` values must have multiple line items, to exercise the header-line hierarchy.
- [ ] 4. `customer_id` values in seed rows must be valid surrogate keys that will exist in `unified_customers` after a `dbt run` against the existing Acme/Globe CRM seeds. Approach: pre-compute `md5(source_system || '-' || source_customer_id)` from the CRM seed values and hard-code those MD5 strings. Document the approach in Implementation Notes.
- [ ] 5. `product_id` values in seed rows must be valid surrogate keys from `unified_products`. Same pre-computation approach.
- [ ] 6. `ingestion/load_raw.py` is updated so that `SOURCES` includes the transactions source: `"transactions": PROJECT_ROOT / "sources" / "transactions" / "transactions.db"`.
- [ ] 7. Table naming in `load_raw.py` produces `TRANSACTIONS__SALES` and `TRANSACTIONS__QUOTES` in the raw Snowflake schema, following the existing `{SOURCE}__{TABLE}` convention.
- [ ] 8. `ALTER TABLE ... SET CHANGE_TRACKING = TRUE` is applied to both new tables after each load, consistent with the existing CRM table handling.
- [ ] 9. Running `python ingestion/load_raw.py` end-to-end loads both transactions tables into Snowflake with no errors.
- [ ] 10. Unit tests in `tests/unit/test_load_raw.py` are updated or extended to cover the new `transactions` source (mock-based, consistent with existing test patterns).

---

## Schema Reference

**`sales` table (line-item grain):**

| Column | SQLite Type | Notes |
|---|---|---|
| `sale_line_id` | TEXT | PK — unique per line item |
| `sale_id` | TEXT | Header FK — groups line items into one sale |
| `customer_id` | TEXT | Surrogate key from `unified_customers` |
| `product_id` | TEXT | Surrogate key from `unified_products` |
| `amount` | REAL | Line item dollar amount |
| `stage` | TEXT | `closed_won`, `closed_lost`, or `pending` |
| `close_date` | TEXT | ISO 8601 date string |
| `created_at` | TEXT | ISO 8601 datetime string |

**`quotes` table (line-item grain):**

| Column | SQLite Type | Notes |
|---|---|---|
| `quote_line_id` | TEXT | PK — unique per line item |
| `quote_id` | TEXT | Header FK — groups line items into one quote |
| `customer_id` | TEXT | Surrogate key from `unified_customers` |
| `product_id` | TEXT | Surrogate key from `unified_products` |
| `quoted_price` | REAL | Unit quoted price |
| `quantity` | INTEGER | Quantity quoted |
| `status` | TEXT | `draft`, `sent`, `accepted`, or `expired` |
| `expiry_date` | TEXT | ISO 8601 date string |
| `created_at` | TEXT | ISO 8601 datetime string |

---

## Implementation Notes

*Fill in during development. Record the MD5 values pre-computed for surrogate key alignment, the decision on seed data population approach, and any edge cases in the ingestion script.*

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
