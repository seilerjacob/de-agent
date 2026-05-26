---
description: High-level project context for the DE Agent Claude skill demo
---

# DE Agent — Project Info

## Purpose
This project demonstrates and defines a **Claude skill** focused on **Data Engineering (DE)** tasks.
The skill covers two primary domains:

1. **SQL** — Schema design, Extract-Transform-Load (ETL) patterns, query optimization, and data quality validation.
2. **Python** — ETL pipelines, data transformations, data quality frameworks, and orchestration patterns.

## Tech Stack
- **SQL dialects**: ANSI SQL, with notes for Snowflake / BigQuery / PostgreSQL where relevant.
- **Python ≥ 3.10** with libraries: `pandas`, `sqlalchemy`, `duckdb`, `great_expectations`, `polars`.
- **Orchestration reference**: Apache Airflow Directed Acyclic Graph (DAG) patterns (conceptual).

## Project Layout
| Directory | Contents |
|-----------|----------|
| `sql/` | Numbered skill modules for SQL |
| `python/` | Numbered skill modules for Python |
| `prompts/` | Reusable prompt templates that define the Claude skill |
| `examples/` | End-to-end worked examples combining SQL + Python |

## Conventions
- Each module directory has its own `README.md` explaining the skill it demonstrates.
- SQL files target ANSI SQL unless a dialect-specific comment says otherwise.
- Python code uses type hints, docstrings, and follows PEP 8.
