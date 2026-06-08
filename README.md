# DE Agent — Claude Skill for Data Engineering

A **Claude skill demo** focused on **Data Engineering (DE)** within a
**data lakehouse** using a **medallion architecture** and **dbt Core** for
transformation between layers.

## Architecture

Two mock Customer Relationship Management (CRM) systems with deliberately
different schemas feed into a DuckDB lakehouse via a medallion pattern:

```
┌──────────────┐     ┌──────────────┐
│  Acme CRM    │     │  Globe CRM   │
│  (SQLite)    │     │  (SQLite)    │
│  - contacts  │     │  - customers │
│  - inventory │     │  - products  │
└──────┬───────┘     └──────┬───────┘
       │    Python ingestion│
       └────────┬───────────┘
                ▼
     ┌─────────────────────┐
     │   Raw Layer (DuckDB) │
     │  raw_acme__contacts  │
     │  raw_acme__inventory │
     │  raw_globe__customers│
     │  raw_globe__products │
     └──────────┬──────────┘
                │  dbt Core
                ▼
     ┌─────────────────────┐
     │ Curated Layer (dbt)  │
     │  curated_customers   │  ← unified schema
     │  curated_products    │  ← unified schema
     └─────────────────────┘
```

## Prerequisites

- **Docker** (for `make run` / `docker compose up`), or
- **Python 3.11+** and `pip` (for local venv setup)

## Quick Start

**Option A (Docker):**

```bash
make run
# or equivalently:
docker compose up
```

**Option B (Local venv):**

```bash
bash scripts/bootstrap.sh
source .venv/bin/activate
python run_pipeline.py
```

## Local Development

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-unit` | Unit tests only |
| `make test-e2e` | Critical path end-to-end test |

## Rebuild from Scratch

```bash
make clean       # destroy containers and volumes
make build       # rebuild image from scratch
make run         # start fresh
```

## Project Structure

```
├── sources/                  Mock upstream CRM databases
│   ├── crm_acme/             Acme CRM seed script + SQLite DB
│   └── crm_globe/            Globe CRM seed script + SQLite DB
├── ingestion/                Python scripts to load sources → DuckDB raw layer
│   └── load_raw.py
├── dbt_project/              dbt Core project
│   ├── models/
│   │   ├── raw/              Source definitions (sources.yml)
│   │   └── curated/          Unified customer + product models
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── packages.yml
├── warehouse/                DuckDB lakehouse (generated, gitignored)
├── run_pipeline.py           End-to-end pipeline orchestrator
└── requirements.txt
```

## Schema Differences (Why Unification Matters)

| Concept | Acme CRM | Globe CRM |
|---------|----------|-----------|
| **Customer table** | `contacts` | `customers` |
| **Name fields** | `first_name` + `last_name` | `full_name` |
| **Email** | `email_address` | `email` |
| **Phone** | `phone` | `mobile_phone` |
| **Company** | `company_name` | `organization` |
| **Product table** | `inventory` | `products` |
| **Product name** | `item_name` | `product_title` |
| **Price** | `price` | `retail_price` + `unit_cost` |
| **Availability** | `stock_qty` (integer) | `available` (0/1 flag) |

The curated dbt models normalize all of this into a single consistent schema.
