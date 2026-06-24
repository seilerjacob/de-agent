---
id: TASK-025c
title: "Warehouse Expansion — Customers Mart Model"
status: todo
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

- [ ] 1. The `dbt_project/models/marts/` directory exists. Create it if absent.
- [ ] 2. `dbt_project/models/marts/customers.sql` exists. It selects from `{{ ref('unified_customers') }}` and produces one output row per unique customer email (deduplicated).
- [ ] 3. Deduplication logic: `row_number() over (partition by lower(email) order by source_system)` with a filter on `rn = 1`. When the same email appears in both Acme and Globe, Acme is retained (alphabetical `source_system` ordering: `acme` < `globe`). Document this tiebreaker decision in Implementation Notes.
- [ ] 4. The mart exposes these consumer-facing columns at minimum: `customer_id` (aliased from `customer_sk`), `first_name`, `last_name`, `full_name`, `email`, `phone_number`, `organization`, `status`, `source_system`, `created_at`. The `source_customer_id` column is excluded from the mart output.
- [ ] 5. Materialization is decided by the engineer and documented in Implementation Notes. Preferred default: view (keeps it simple for a first mart; Dynamic Table if near-real-time refresh is desired).
- [ ] 6. `dbt_project/models/marts/_mart__models.yml` exists and declares the `customers` model with column descriptions.
- [ ] 7. The `marts` layer is registered in `dbt_project/dbt_project.yml` under the `models:` block with at minimum `+schema: mart` so mart models land in the `DE_AGENT_MART` schema (or `DE_AGENT_mart` depending on case folding — verify against the existing `stg` and `int` schema config).

**Tests**

- [ ] 8. `not_null` tests on `customers`: `customer_id`, `email`, `full_name`.
- [ ] 9. `unique` test on `customers.email` (post-deduplication, every email should be unique).
- [ ] 10. `unique` test on `customers.customer_id`.
- [ ] 11. `dbt build --select marts.customers` runs clean against Snowflake.

**Schema registration**

- [ ] 12. After `dbt run`, the `customers` view (or table/dynamic table) exists in `DE_AGENT_SPIKE.DE_AGENT_MART` (or the equivalent schema per dbt's `+schema: mart` + target schema concatenation). Verify the actual schema name by checking how `stg` resolves to `DE_AGENT_STG` in the existing project config.

---

## Implementation Notes

### Mart schema config

Add the following to `dbt_project/dbt_project.yml` under `models: de_agent_lakehouse:`:

```yaml
marts:
  +schema: mart
```

This follows the same pattern as `staging: +schema: stg` and `intermediate: +schema: int`.

### Deduplication approach

The `row_number()` window function approach is preferred over `distinct` or `qualify` for clarity and portability:

```sql
with ranked as (
    select
        *,
        row_number() over (
            partition by lower(email)
            order by source_system
        ) as rn
    from {{ ref('unified_customers') }}
)

select
    customer_sk     as customer_id,
    first_name,
    last_name,
    full_name,
    email,
    phone_number,
    organization,
    status,
    source_system,
    created_at
from ranked
where rn = 1
```

### Tiebreaker rationale

When the same email exists in both Acme and Globe, Acme is preferred. `source_system = 'acme'` sorts before `source_system = 'globe'` alphabetically, so `order by source_system asc` achieves this without a `case` expression. Document this as a product decision: Acme is the system of record for customer identity when conflicts exist.

### Materialization decision

Decide between:
- **View** (default for first mart): zero storage cost, always reflects current `unified_customers` data. Appropriate if consumers query infrequently or `unified_customers` is already a Dynamic Table.
- **Dynamic Table**: near-real-time refresh, better query performance if the mart is queried heavily. Adds Snowflake credits cost.

Recommendation: start with view. Escalate to Dynamic Table if query performance or freshness becomes a concern.

---

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
