# Maker Onboarding Plan — DE Agent

**Date:** 2026-06-08  
**Audited against:** maker principles (.project/)

---

## Mode Recommendation

**Recommended mode:** Full Integration

**Rationale:**
The project has a single contributor (git user `jaco129`, jacob.seiler@wwt.com), only two commits, and no branch protection rules, CI pipeline, or external contributors. The maker framework files (`.project/`, `CLAUDE.md`, `tasks/`) are already present on disk as untracked files — they were never committed, not intentionally excluded. There are no signals that would make full integration disruptive: no other contributors to consult, no existing conventions that conflict, and the project is early enough that structural changes are zero-friction.

**What changes based on this choice:**
- If Full: all maker files will be committed in a single `chore` commit; the action list below applies in full
- If Lite: run `.project/scripts/setup-maker-lite.sh`; actions marked [LITE: SKIP] below are not applicable; actions marked [LITE: PERSONAL] apply as personal discipline only

**Human decision required:** confirm the mode before any implementation begins.

---

## Executive Summary

The project is a solo-owned, early-stage DE skill demo with four principles in Gap status and one in Partial. The most urgent gap is the Git trunk strategy — there is no `dev` branch and both commits were pushed directly to `main`. The second-most urgent is the absence of any automated tests, including dbt singular tests and Python unit coverage for the ingestion layer. Infrastructure-as-Code and Local-First gaps are real but lower severity because the stack is file-based (SQLite + DuckDB), making containerization a lower-friction addition rather than a blocking requirement.

---

## Findings by Principle

### 1. Local-First Development — Gap

**Findings:**
- No `docker-compose.yml` exists at the project root (only one is present inside `dbt_project/dbt_packages/dbt_utils/`, a third-party dependency)
- No `Dockerfile` exists anywhere in the project
- No `.env.example` or `.env.sample` is checked in
- The README documents a 3-step manual host-level setup: `python -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`
- The pipeline does not use network-boundary services (no external database server, no queue, no cache) — all dependencies are file-based (SQLite source DBs, DuckDB lakehouse)
- The README documents a single run command (`python run_pipeline.py`) but not as a containerized startup

**Gaps:**
- No `docker compose up` equivalent that encapsulates all dependencies
- No `.env.example` (though the project currently has no secrets)
- README requires manual Python venv setup rather than a single command
- No documented destroy-and-rebuild sequence

**Recommended actions:**
- [BOTH] Add a `docker-compose.yml` that runs the pipeline as a service with the DuckDB warehouse mounted as a named volume. For this file-based stack, a single-container compose that installs deps and runs `python run_pipeline.py` satisfies the spirit of the principle without over-engineering.
- [BOTH] Add `.env.example` with a comment block documenting what variables are used (even if currently none are required — establishes the pattern for when credentials are added)
- [BOTH] Add a `Makefile` with a `run` target that wraps the compose command, so the single-command test is met
- [BOTH] Document destroy-and-rebuild sequence in README

---

### 2. Lightweight Automated Testing — Gap

**Findings:**
- No test files exist anywhere in the project (the `dbt_project/tests/` directory contains only `.gitkeep`)
- No test commands are documented in the README
- No `Makefile`, `pyproject.toml`, or CI configuration defines test targets
- No CI configuration exists (no `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`)
- The `ingestion/load_raw.py` script contains transformation logic (column mapping, schema normalization) with no test coverage
- dbt has native test support (`dbt test`) with generic tests (not_null, unique, relationships) and singular SQL tests — none are configured

**Gaps:**
- No unit tests for Python ingestion logic
- No dbt schema tests on source or curated models
- No critical path test that exercises the full pipeline from seed to curated output
- No test commands documented
- No CI to run tests on push

**Recommended actions:**
- [BOTH] Add unit tests for `ingestion/load_raw.py` covering the column-mapping and type-coercion logic; use `pytest` with in-memory DuckDB fixtures
- [BOTH] Add dbt generic tests (not_null, unique) to `_acme__models.yml`, `_globe__models.yml`, and the intermediate/curated model YAML files
- [BOTH] Add a critical path test: a Python test that seeds both CRMs, runs ingestion, runs `dbt build`, and asserts that `curated_customers` and `curated_products` contain the expected row counts and unified column schema
- [BOTH] Document `pytest` and `dbt test` commands in the README
- [BOTH] Add a `Makefile` with `test`, `test-unit`, and `test-e2e` targets
- [BOTH] Add a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs all tests on push to any branch and on PRs targeting `dev`

---

### 3. Git Trunk Strategy — Gap

**Findings:**
- Only one branch exists locally and remotely: `main`
- Both commits (`bcdd850 Initial commit`, `3b0bd87 dbt-ify`) were pushed directly to `main`
- No `dev` branch exists
- No feature branches exist or have existed
- No merge commits in history — all work has been direct pushes
- No branch naming convention has been applied
- No branch protection rules are visible from a static read (cannot assess from git alone)

**Gaps:**
- No `dev` integration branch
- No enforcement of the feature-branch PR workflow
- No branch protection preventing direct pushes to `main`

**Recommended actions:**
- [FULL ONLY] Create `dev` branch off current `main` tip; configure branch protection on `main` and `dev` to require PRs
- [LITE: PERSONAL] All future work branches off `dev`; apply rebase discipline; never push directly to `main`
- [BOTH] Apply `feature/`, `fix/`, `chore/` naming convention to all new branches

---

### 4. Infrastructure as Code — Gap

**Findings:**
- No `Dockerfile` committed to the repository
- No `infra/`, `deploy/`, `terraform/`, `cdk/`, or `pulumi/` directory
- No `scripts/bootstrap.sh` or `make bootstrap` target
- No production IaC of any kind
- The local environment requires host-level Python 3.8 (inferred from `.venv/lib/python3.8/` path) and pip — not containerized
- The `.gitignore` correctly excludes generated artifacts (`warehouse/`, `*.duckdb`, `dbt_project/target/`) but does not document how to regenerate them

**Gaps:**
- No `Dockerfile` for the pipeline runner
- No bootstrap script for one-time setup
- No documented rebuild sequence
- No production IaC (though the project is currently a local demo with no cloud deployment target)

**Recommended actions:**
- [BOTH] Add `Dockerfile` with pinned Python base image (e.g., `python:3.11-slim`) that installs `requirements.txt` and sets the entrypoint to `python run_pipeline.py`
- [BOTH] Add `scripts/bootstrap.sh` that creates the virtual environment, installs dependencies, and seeds the source databases — idempotent
- [BOTH] Document the rebuild sequence in README (`docker compose down -v && docker compose build --no-cache && docker compose up`)
- [FULL ONLY] If/when this moves to production, add IaC in `infra/` — mark as a future task

---

### 5. Task-as-Documentation — Partial

**Findings:**
- The full task directory structure exists: `tasks/todo/`, `tasks/development/`, `tasks/testing/`, `tasks/completed/`
- `tasks/templates/task.md` is present
- `tasks/TASKS.md` is present with full documentation of the system
- All directories contain only `.gitkeep` — no actual task files have been created
- The maker files (`.project/`, `tasks/`, `CLAUDE.md`) are currently untracked — they appear in `git status` as `?? .project/`, `?? tasks/`, `?? CLAUDE.md` — meaning none of the maker scaffolding has been committed to the repo yet
- The `.git/info/exclude` file is at its default state — maker files have not been added there, confirming lite mode was not intentionally set up either
- No external tracker (Jira, Linear, GitHub Issues) is referenced in the README or docs

**Gaps:**
- Maker files have not been committed (no full integration) and have not been hidden from git (no lite mode) — currently in an ambiguous state
- No task files have been created to document the initial pipeline work already done

**Recommended actions:**
- [BOTH] Commit `.project/`, `tasks/`, `CLAUDE.md`, `MAKER_ONBOARDING.md`, `MAKER_LITE.md`, and `MAKER_ONBOARDING_PLAN.md` in a single `chore: add maker project conventions` commit on a feature branch targeting `dev`
- [BOTH] Create `tasks/completed/TASK-001-initial-pipeline.md` documenting the work already done (CRM sources, ingestion layer, dbt medallion models) — backfill the record

---

## Prioritized Action List

| Priority | Action | Effort | Principle | Mode |
|---|---|---|---|---|
| 1 | Create `dev` branch off `main`; configure branch protection on `main` and `dev` | Low | Git Trunk | Full only |
| 2 | Commit all maker scaffolding files in a `chore` commit on a feature branch | Low | Task-as-Doc | Both |
| 3 | Backfill `TASK-001-initial-pipeline.md` in `tasks/completed/` | Low | Task-as-Doc | Both |
| 4 | Add dbt generic tests (not_null, unique) to all model YAML files | Low | Testing | Both |
| 5 | Add `pytest` unit tests for `ingestion/load_raw.py` column-mapping logic | Medium | Testing | Both |
| 6 | Add critical path test: seed → ingest → dbt build → assert curated output | Medium | Testing | Both |
| 7 | Add `Makefile` with `run`, `test`, `test-unit`, `test-e2e` targets | Low | Testing + Local Dev | Both |
| 8 | Add `Dockerfile` with pinned Python base image | Low | IaC | Both |
| 9 | Add `docker-compose.yml` that runs the pipeline container | Low | Local-First + IaC | Both |
| 10 | Add `.env.example` documenting environment variables | Low | Local-First | Both |
| 11 | Add `scripts/bootstrap.sh` (idempotent setup script) | Low | IaC | Both |
| 12 | Update README with single-command startup and rebuild sequence | Low | Local-First | Both |
| 13 | Add GitHub Actions CI workflow (`.github/workflows/ci.yml`) | Medium | Testing | Full only |

Priority ordering rationale: git trunk gaps are highest because they affect all future work; maker scaffolding commit is next because it establishes the record; testing follows because it is the primary quality gate; infrastructure additions last because the project currently works locally without them.

---

## Open Questions

- **Deployment target:** Is there a planned production deployment for this pipeline (e.g., cloud scheduler, Airflow, Dagster)? If so, IaC priority rises significantly.
- **Python version:** The `.venv` is Python 3.8 (inferred from `.venv/lib/python3.8/`). This is EOL. Confirm intended Python version for the Dockerfile base image.
- **Branch protection:** Does the GitHub remote (`jaco129`'s account or a WWT org) support branch protection rules? If not, the `dev` branch strategy is enforced by convention only.
- **CI access:** Is GitHub Actions available for this repository, or is a different CI system in use at WWT?

---

## Cannot Assess

- **Test suite runtime:** Cannot determine whether tests pass or how long they take — no tests exist to run, and the test command was not established.
- **Branch protection configuration:** Requires access to the GitHub repository settings; not determinable from a static git read.
- **Production environment:** No IaC or deployment configuration exists; cannot assess what the production target looks like.
- **dbt test existing coverage:** `dbt test` requires a running dbt project with compiled models; cannot assess from static file read whether any implicit tests exist beyond the empty `tests/` directory.
