---
id: TASK-024
title: Align dbt naming conventions with reference/snowflake branch
status: todo
created: 2026-06-23
updated: 2026-06-23
branch: feature/TASK-024-dbt-naming-conventions
---

## Objective

The `reference/snowflake` branch introduced several non-Snowflake-specific
improvements to the dbt project structure during its development. These changes
should be applied to the trunk (`dev`) so that the DuckDB and Snowflake
implementations stay structurally aligned and the reference branch does not
drift unnecessarily from the canonical data model.

None of the changes in this task are adapter-specific — they are pure naming
and convention improvements that apply equally to DuckDB.

## Acceptance Criteria

- [ ] Staging model files renamed: `stg_*` prefix removed (e.g. `stg_acme__contacts.sql` → `acme__contacts.sql`)
- [ ] Intermediate model files renamed: `int_*` prefix removed (e.g. `int_unified_customers.sql` → `unified_customers.sql`)
- [ ] All `source()` and `ref()` calls updated to match new names
- [ ] Source YAML: source names stripped of `raw_` prefix (`raw_acme` → `acme`), table names updated accordingly
- [ ] Model YAML: model name entries updated in all `_*__models.yml` files
- [ ] `dbt_project.yml`: schema keys shortened (`staging` → `stg`, `intermediate` → `int`)
- [ ] `accepted_values` tests migrated to `arguments:` format (dbt 1.9+ convention)
- [ ] `generate_surrogate_key` macro added locally; `dbt-labs/dbt_utils` removed from `packages.yml`
- [ ] `dbt build` passes locally against DuckDB
- [ ] Critical path e2e test passes
- [ ] PR references this task

## Implementation Notes

Changes to port from `reference/snowflake` (all adapter-agnostic):

1. **Model renames** (git mv, preserves history):
   - `stg_acme__contacts.sql` → `acme__contacts.sql`
   - `stg_acme__inventory.sql` → `acme__inventory.sql`
   - `stg_globe__customers.sql` → `globe__customers.sql`
   - `stg_globe__products.sql` → `globe__products.sql`
   - `int_unified_customers.sql` → `unified_customers.sql`
   - `int_unified_products.sql` → `unified_products.sql`

2. **Source YAML** (`_acme__sources.yml`, `_globe__sources.yml`):
   - Source names: `raw_acme` → `acme`, `raw_globe` → `globe`
   - Table names: drop `raw_` prefix
   - Do NOT port `change_tracking_enabled` test (Snowflake-specific)

3. **Model YAML** — update `name:` entries in all four `_*__models.yml` files

4. **SQL content** — update `source()` and `ref()` calls in all model files

5. **`dbt_project.yml`** — `+schema: staging` → `+schema: stg`, `+schema: intermediate` → `+schema: int`

6. **Test format** — `accepted_values: values:` → `accepted_values: arguments: values:`

7. **Macro + package** — copy `macros/generate_surrogate_key.sql` from reference branch; remove `dbt-labs/dbt_utils` from `packages.yml`

Do NOT port: `change_tracking_enabled` macro/test, `vars.snowflake_warehouse`,
dynamic table materialization, profiles changes, or `dbt_project/local/`.

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
