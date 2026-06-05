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

## Quick Start

```bash
# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (seed → ingest → dbt build)
python run_pipeline.py
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
