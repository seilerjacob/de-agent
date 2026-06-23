---
id: TASK-025c
title: "Warehouse Expansion — Customers Mart Model"
status: development
created: 2026-06-23
updated: 2026-06-23
branch: feature/TASK-025c-customers-mart
parent: TASK-025
---

## Objective

TASK-025 establishes the mart layer in this project. This subtask owns the first mart model: a canonical `customers` model that provides a clean, consumer-facing, deduplicated customer record for downstream consumers.

The mart selects from `unified_customers` (which already exists and unions Acme contacts + Globe customers). Its job is deduplication on email — a customer who appears in both source systems should resolve to one record — and surfacing consumer-facing column names. There are no aggregations, no metrics, and no joins to transactional data.

This subtask is fully independent of TASK-025a and TASK-025b and can be authored, compiled, and tested against existing data in Snowflake immediately.

---

## Acceptance Criteria

**Mart model**

- [x] 1. The `dbt_project/models/marts/` directory exists. Create it if absent.
- [x] 2. `dbt_project/models/marts/customers.sql` exists. It selects from `{{ ref('unified_customers') }}` and produces one output row per unique customer email (deduplicated).
- [x] 3. Deduplication logic: `row_number() over (partition by lower(email) order by source_system)` with a filter on `rn = 1`. When the same email appears in both Acme and Globe, Acme is retained (alphabetical `source_system` ordering: `acme` < `globe`). Document this tiebreaker decision in Implementation Notes.
- [x] 4. The mart exposes these consumer-facing columns at minimum: `customer_id` (aliased from `customer_sk`), `first_name`, `last_name`, `full_name`, `email`, `phone_number`, `organization`, `status`, `source_system`, `created_at`. The `source_customer_id` column is excluded from the mart output.
- [x] 5. Materialization is decided by the engineer and documented in Implementation Notes. Preferred default: view (keeps it simple for a first mart; Dynamic Table if near-real-time refresh is desired).
- [x] 6. `dbt_project/models/marts/_mart__models.yml` exists and declares the `customers` model with column descriptions.
- [x] 7. The `marts` layer is registered in `dbt_project/dbt_project.yml` under the `models:` block with at minimum `+schema: mart` so mart models land in the `DE_AGENT_MART` schema.

**Tests**

- [x] 8. `not_null` tests on `customers`: `customer_id`, `email`, `full_name`.
- [x] 9. `unique` test on `customers.email` (post-deduplication, every email should be unique).
- [x] 10. `unique` test on `customers.customer_id`.
- [ ] 11. `dbt build --select marts.customers` runs clean against Snowflake. (Deferred — Snowflake credentials not present in this environment. Integration agent to run.)

**Schema registration**

- [ ] 12. After `dbt run`, the `customers` view exists in the `*_DE_AGENT_MART` schema. (Deferred to integration agent — see #11.)

---

## Implementation Notes

### Mart schema config

Added to `dbt_project/dbt_project.yml` under `models: de_agent_lakehouse:`:

```yaml
marts:
  +schema: mart
```

This follows the same pattern as `staging: +schema: stg` and `intermediate: +schema: int`.

### Deduplication approach

Used the `row_number()` window function (preferred over `distinct`/`qualify` for clarity and portability):

```sql
row_number() over (partition by lower(email) order by source_system) as rn
```
filtered to `rn = 1`.

### Tiebreaker rationale

When the same email exists in both Acme and Globe, the Acme record is retained. `source_system = 'acme'` sorts before `'globe'` alphabetically, so `order by source_system` (ascending, default) achieves this without a `case` expression. Product decision: Acme is the system of record for customer identity when conflicts exist.

### Materialization decision

**View.** Zero storage cost and always reflects current `unified_customers` data (which is itself a Snowflake Dynamic Table refreshing on a 1-minute lag). Escalate to a Dynamic Table only if query performance or freshness becomes a concern.

### Output columns

In addition to the required consumer-facing columns, `loaded_at` is carried through from `unified_customers` (lakehouse load timestamp) for downstream lineage/observability. `source_customer_id` is excluded as an internal field.

### Verification

`dbt parse` runs clean against the project. `dbt build` against Snowflake was intentionally not run in this environment per task constraints (credentials may be absent); the integration agent owns AC #11 and #12.

---

## Testing Notes

- `dbt parse` succeeds — model graph and schema YAML compile without error.
- Schema tests declared: `not_null` on `customer_id`, `email`, `full_name`; `unique` on `customer_id` and `email`.
- Full `dbt build` against Snowflake deferred to integration agent (credentials not present here).

## Completion Notes

*Fill in on merge.*
