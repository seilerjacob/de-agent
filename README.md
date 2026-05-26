# DE Agent — Claude Skill for Data Engineering

A project that defines, demonstrates, and tests a **Claude skill** purpose-built for
**Data Engineering (DE)** work — specifically SQL authoring and Python pipeline development.

## What Is This?

This repository is a **skill demo** — a structured collection of prompts, examples, and
reference implementations that teach Claude how to act as a senior Data Engineer.
The skill covers:

| Domain | Key Capabilities |
|--------|-----------------|
| **SQL** | Dimensional modeling, Slowly Changing Dimension (SCD) Type 2, incremental loads, Common Table Expression (CTE) patterns, window functions, data quality checks |
| **Python** | ETL pipelines with `pandas`/`polars`, `duckdb` local analytics, `SQLAlchemy` integration, data quality with `great_expectations`, Airflow DAG patterns |

## Quick Start

```bash
# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run an example pipeline
python examples/end_to_end_pipeline/extract.py
```

## Project Structure

```
├── prompts/            Reusable prompt templates defining the Claude skill
├── sql/                SQL skill modules (numbered)
│   ├── 01_schema_design/
│   ├── 02_etl_patterns/
│   ├── 03_query_optimization/
│   └── 04_data_quality/
├── python/             Python skill modules (numbered)
│   ├── 01_etl_pipeline/
│   ├── 02_data_transforms/
│   ├── 03_data_quality/
│   └── 04_orchestration/
└── examples/           End-to-end worked examples
    ├── end_to_end_pipeline/
    └── data_warehouse_design/
```

## Prompt Templates

The `prompts/` directory contains markdown templates that define how Claude should
behave when assisting with DE tasks. Import these into your Claude project or
reference them as system prompts.

## Contributing

1. Each new skill module goes in a numbered subdirectory under `sql/` or `python/`.
2. Every module must include a `README.md` explaining the skill demonstrated.
3. SQL defaults to ANSI SQL; note dialect-specific syntax in comments.
4. Python follows PEP 8, uses type hints, and includes docstrings.
