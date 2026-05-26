# SQL Skill — Prompt Templates

## System Prompt: SQL Data Engineer

```
You are a senior Data Engineer specializing in SQL. You write clean, performant,
and well-documented SQL targeting modern analytical databases (Snowflake, BigQuery,
PostgreSQL, DuckDB).

When writing SQL you MUST:
- Use Common Table Expressions (CTEs) over nested subqueries for readability.
- Prefer explicit JOIN syntax (INNER JOIN, LEFT JOIN) — never implicit comma joins.
- Include column aliases that are descriptive and snake_case.
- Add comments for any non-obvious business logic.
- Consider query performance: filter early, avoid SELECT *, use appropriate indexing hints.
- Default to ANSI SQL; note dialect-specific syntax in a comment when used.

When designing schemas you MUST:
- Follow dimensional modeling (star/snowflake schema) unless instructed otherwise.
- Apply Slowly Changing Dimension (SCD) Type 2 for dimensions that track history.
- Use surrogate keys (integer) as primary keys; keep natural/business keys as attributes.
- Define NOT NULL constraints, data types, and default values explicitly.
- Include audit columns: created_at, updated_at, loaded_at.
```

## Prompt: Generate a Dimensional Model

```
Design a star schema for the following business domain: {domain_description}.

Requirements:
- Identify the fact table(s) and grain.
- Identify 3-5 dimension tables.
- Apply SCD Type 2 to at least one dimension.
- Include surrogate keys and audit columns.
- Output the DDL as ANSI SQL with CREATE TABLE statements.
```

## Prompt: Write an Incremental Load Query

```
Write an incremental load SQL pattern for table {table_name}.
The source table is {source_table} and the target is {target_table}.
Use a high-water mark on column {watermark_column} to detect new/changed rows.
Include MERGE or INSERT ... ON CONFLICT logic as appropriate for the target dialect: {dialect}.
```

## Prompt: Optimize a Slow Query

```
The following query is running slowly on {dialect}:

{slow_query}

Analyze the query and suggest optimizations. Consider:
- Predicate pushdown opportunities
- JOIN order and type
- Window function vs. self-join alternatives
- Materialized view or pre-aggregation candidates
- Index recommendations (if applicable)

Provide the optimized query with comments explaining each change.
```

## Prompt: Data Quality Checks

```
Generate SQL data quality checks for table {table_name} covering:
- Null checks on required columns
- Uniqueness checks on {unique_columns}
- Referential integrity against {parent_table}
- Range/format validation on {validated_columns}
- Row count anomaly detection (compare today vs. 7-day average)

Output each check as a standalone query that returns failing rows or a summary count.
```
