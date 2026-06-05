---
description: High-level project context for the DE Agent Claude skill demo
---

# DE Agent — Project Info

## Purpose
This project demonstrates and defines a **Claude skill** focused on **Data Engineering (DE)** tasks.
The primary workflow is a **data lakehouse** using a **medallion architecture** (raw → curated → …)
with **dbt Core** for transformation between layers.

## Architecture — Medallion Lakehouse
- **Sources**: Two mock Customer Relationship Management (CRM) SQLite databases (Acme CRM, Globe CRM) with deliberately different schemas.
- **Raw layer**: Python ingestion (`ingestion/load_raw.py`) loads source tables as-is into DuckDB under a `raw` schema.
- **Staging layer**: dbt views (`stg_`) — 1:1 with raw source tables, handling only column renames and type casts. One directory per source system.
- **Intermediate layer**: dbt tables (`int_`) — business logic, schema unification, and surrogate key generation. References staging models via `ref()`.
- **Warehouse**: DuckDB (`warehouse/lakehouse.duckdb`) serves as the local analytical warehouse.

## Tech Stack
- **Python ≥ 3.10** with `pandas` and `duckdb`.
- **dbt Core** with `dbt-duckdb` adapter and `dbt_utils` package.
- **SQLite** for upstream mock CRM databases.

## Project Layout
| Path | Contents |
|------|----------|
| `sources/` | Mock CRM SQLite databases and seed scripts |
| `ingestion/` | Python scripts to load sources → DuckDB raw layer |
| `warehouse/` | DuckDB lakehouse database (gitignored, generated) |
| `dbt_project/` | dbt Core project root |
| `dbt_project/models/staging/acme/` | Acme source definitions, staging models, and tests |
| `dbt_project/models/staging/globe/` | Globe source definitions, staging models, and tests |
| `dbt_project/models/intermediate/` | Unified `int_unified_customers` and `int_unified_products` models and tests |

## dbt Model Layers
```
source()          ref()                ref() (future)
  raw  ──→  staging (stg_)  ──→  intermediate (int_)  ──→  marts (dim_/fct_)
  DuckDB    views, 1:1            tables, unions            tables, dedup/MDM
```

## Running the Pipeline
```bash
python run_pipeline.py
```
This seeds both CRMs → ingests raw → runs dbt build (models + tests) → prints intermediate summary.

## Conventions
- Python code uses type hints, docstrings, and follows PEP 8.
- dbt models use standard prefixes: `stg_` (staging), `int_` (intermediate), `dim_`/`fct_` (marts).
- YAML config files use `_` prefix per source/domain: `_acme__sources.yml`, `_int_customers__models.yml`.
- Source tables use double-underscore naming: `raw_{system}__{table}`.
- `source()` is only used in staging models; all downstream models use `ref()`.
