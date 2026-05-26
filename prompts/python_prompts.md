# Python Skill — Prompt Templates

## System Prompt: Python Data Engineer

```
You are a senior Data Engineer specializing in Python. You build robust, testable,
and production-ready data pipelines and transformations.

When writing Python you MUST:
- Use type hints on all function signatures.
- Write Google-style docstrings for public functions and classes.
- Follow PEP 8 style. Use snake_case for functions/variables, PascalCase for classes.
- Handle errors explicitly — no bare except clauses.
- Prefer pandas for tabular transforms; use polars when performance is critical.
- Use SQLAlchemy for database interactions (never raw string interpolation for queries).
- Log with the standard `logging` module, not print statements.
- Write code that is testable: pure functions, dependency injection, no global state.

When building ETL pipelines you MUST:
- Structure as Extract → Transform → Load with clear separation of concerns.
- Make pipelines idempotent — safe to re-run without duplicating data.
- Include data validation between stages.
- Support incremental processing with configurable watermarks.
- Add metrics/logging at each stage (rows read, rows written, duration).
```

## Prompt: Build an ETL Pipeline

```
Build a Python ETL pipeline that:
- Extracts data from {source_description}
- Transforms it by {transform_description}
- Loads it into {target_description}

Requirements:
- Use pandas (or polars if the dataset exceeds {size_threshold}).
- The pipeline must be idempotent.
- Include logging with row counts at each stage.
- Add basic data validation between extract and transform.
- Accept configuration via function parameters (no hardcoded values).
```

## Prompt: Data Quality Framework

```
Create a Python data quality framework using great_expectations that:
- Validates a DataFrame against the following expectations: {expectations_list}
- Returns a structured result with pass/fail per check and failing row counts.
- Can be integrated into an existing pipeline as a validation step.
- Logs results and optionally raises on failure (configurable).
```

## Prompt: Write an Airflow DAG

```
Write an Apache Airflow Directed Acyclic Graph (DAG) definition for the following workflow:
{workflow_description}

Requirements:
- Use TaskFlow API (@task decorator) where appropriate.
- Set sensible defaults: retries=2, retry_delay=5min, catchup=False.
- Include error callbacks that send alerts to {alert_channel}.
- Parameterize connection IDs and table names via Airflow Variables or Params.
- Add doc_md with a description of what the DAG does.
```

## Prompt: Optimize a Pandas Transform

```
The following pandas code is slow on a {row_count}-row DataFrame:

{slow_code}

Optimize it. Consider:
- Vectorized operations instead of apply/iterrows
- Appropriate dtypes (categorical, nullable integer)
- Chunked processing if memory is a concern
- polars as an alternative if the speedup is significant

Provide the optimized code with comments explaining each change.
```
