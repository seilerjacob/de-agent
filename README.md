# DE Agent — Claude Skill for Data Engineering

A **Claude skill demo** focused on **Data Engineering (DE)** within a
data lakehouse using a **medallion architecture** and **dbt Core** for
transformation between layers.

## Architecture

Two mock CRM systems with deliberately different schemas feed into a DuckDB
lakehouse via a medallion pattern:

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
     ┌──────────────────────────┐
     │ Intermediate Layer (dbt)  │
     │  int_unified_customers    │  ← unified schema
     │  int_unified_products     │  ← unified schema
     └──────────────────────────┘
```

---

## Snowflake reference implementation

The `reference/snowflake` branch ports this entire pipeline to Snowflake as a
long-lived reference implementation. It swaps the DuckDB raw layer for the
Snowflake connector, reconfigures dbt with `dbt-snowflake`, and materializes
the intermediate layer as **Snowflake Dynamic Tables** (auto-refreshing,
no scheduler).

That branch is intentionally **not merged into `dev`** — it exists as a
canonical example alongside the DuckDB baseline. See
[`docs/reference-snowflake.md`](docs/reference-snowflake.md) (on the
`reference/snowflake` branch) for setup and a full mapping of medallion layers
to Snowflake primitives.

---

## Prerequisites

- **Docker** (for `make run` / `docker compose up`), or
- **Python 3.11+** and `pip` (for local venv setup)

---

## Quick Start

**Option A — Docker:**

```bash
make run
# or equivalently: docker compose up
```

**Option B — Local venv:**

```bash
bash scripts/bootstrap.sh    # creates .venv and installs dependencies
source .venv/bin/activate
python run_pipeline.py
```

---

## Testing

Tests require the local venv (`bash scripts/bootstrap.sh` if not already done).

| Command | What it runs |
|---|---|
| `make test` | Full suite — unit + e2e |
| `make test-unit` | Unit tests for ingestion logic (fast, no I/O) |
| `make test-e2e` | Critical path: seed → ingest → dbt build → assert curated output |

The e2e test exercises the full pipeline against real local files and asserts
that `int_unified_customers` (22 rows) and `int_unified_products` (21 rows)
are produced with the expected schema.

---

## Rebuild from Scratch

```bash
make clean    # destroy containers and volumes
make build    # rebuild image without cache
make run      # start fresh
```

---

## Project Structure

```
├── .project/                 Development principles and conventions
│   ├── PRINCIPLES.md         The five core principles (start here)
│   ├── WORKFLOW.md           Git branching strategy
│   ├── TESTING.md            Testing philosophy and requirements
│   ├── INFRASTRUCTURE.md     Infrastructure conventions
│   └── ORCHESTRATION.md      Subagent patterns (Claude Code)
├── tasks/                    Task tracking — the filesystem is the board
│   ├── todo/                 Defined, not yet started
│   ├── development/          Actively being implemented
│   ├── testing/              Implementation complete, under verification
│   └── completed/            Merged and done
├── sources/                  Mock upstream CRM databases
│   ├── crm_acme/             Acme CRM seed script + SQLite DB
│   └── crm_globe/            Globe CRM seed script + SQLite DB
├── ingestion/                Python: load SQLite sources → DuckDB raw layer
├── dbt_project/              dbt Core project (staging + intermediate models)
├── tests/
│   ├── unit/                 Isolated unit tests (tmp_path fixtures)
│   └── e2e/                  Critical path end-to-end test
├── scripts/
│   └── bootstrap.sh          Idempotent local environment setup
├── warehouse/                DuckDB lakehouse (generated, gitignored)
├── Dockerfile                Pipeline container (python:3.11-slim)
├── docker-compose.yml        Local orchestration
├── Makefile                  Convenience targets: run, test, build, clean
├── run_pipeline.py           End-to-end pipeline orchestrator
├── requirements.txt          Runtime dependencies
├── requirements-dev.txt      Dev dependencies (pytest)
└── CLAUDE.md                 Claude Code entry point
```

---

## Contributing

### Conventions

All development conventions live in `.project/`. Read `.project/PRINCIPLES.md`
before making your first change — it covers local dev, testing, git strategy,
infrastructure, and task tracking in one place.

### Git workflow

Two permanent branches: `dev` (integration) and `main` (production).

```bash
# Start work
git fetch origin
git checkout dev && git pull --ff-only origin dev
git checkout -b feature/my-thing

# Stay current
git fetch origin && git rebase origin/dev

# Finish — open a PR targeting dev
```

Never push directly to `dev` or `main`. Full details: `.project/WORKFLOW.md`.

### Task tracking

Every non-trivial piece of work has a task file in `tasks/`. Before starting:

1. Create `tasks/todo/TASK-XXX-short-title.md` from `tasks/templates/task.md`
2. Move it to `tasks/development/` when you begin; add the branch name
3. Move it to `tasks/testing/` when implementation is complete
4. Move it to `tasks/completed/` when merged to `dev`

The task file is the record of *why* something was done the way it was. PR
descriptions and commit messages reference it but do not replace it.

### Claude Code

If you use Claude Code, `CLAUDE.md` at the repo root is the agent entry point.
It references `.project/` for principles and `tasks/` for in-flight work.
Subagent patterns for parallelising complex tasks are in `.project/ORCHESTRATION.md`.

---

## Schema Differences (Why Unification Matters)

| Concept | Acme CRM | Globe CRM |
|---|---|---|
| Customer table | `contacts` | `customers` |
| Name fields | `first_name` + `last_name` | `full_name` |
| Email | `email_address` | `email` |
| Phone | `phone` | `mobile_phone` |
| Company | `company_name` | `organization` |
| Product table | `inventory` | `products` |
| Product name | `item_name` | `product_title` |
| Price | `price` | `retail_price` + `unit_cost` |
| Availability | `stock_qty` (integer) | `available` (0/1 flag) |

The intermediate dbt models normalize all of this into a single consistent schema.
