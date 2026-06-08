---
id: TASK-005
title: Add GitHub Actions CI pipeline
status: completed
created: 2026-06-08
updated: 2026-06-08
branch: chore/ci-setup
---

## Objective

Add a GitHub Actions workflow that runs the full test suite on every push and on PRs targeting `dev`. CI must run unit tests and the critical path end-to-end test. This requires a remote to be configured — the workflow file is committed now so it is ready when the repo is pushed to GitHub.

Note: this task cannot be fully verified until a remote is configured. The workflow file should be authored to match the Makefile targets from TASK-004.

## Acceptance Criteria

- [x] `.github/workflows/ci.yml` committed
- [x] Workflow triggers on `push` to any branch and on `pull_request` targeting `dev`
- [x] Workflow installs Python dependencies from `requirements.txt` and `requirements-dev.txt`
- [x] Workflow runs `pytest tests/unit/ -v` and `pytest tests/e2e/ -v -s`
- [x] Workflow fails if any test fails (pytest exits non-zero on failure)
- [x] YAML structure verified locally (well-formed, all required fields present)

## Implementation Notes

Authored `.github/workflows/ci.yml` with:
- Triggers: `push` on all branches (`"**"`), `pull_request` targeting `dev`
- Single job `test` on `ubuntu-latest` with Python 3.11
- pip cache keyed on `hashFiles('requirements.txt', 'requirements-dev.txt')` using `actions/cache@v4`
- Separate install steps for production and dev dependencies
- `dbt deps --profiles-dir .` run from `dbt_project/` before tests so dbt packages are available when the e2e test calls `dbt build` via subprocess
- Unit tests: `pytest tests/unit/ -v`
- E2e tests: `pytest tests/e2e/ -v -s` (stdout visible for debugging seed/DuckDB/dbt output)

Decision: invoked pytest directly rather than via `make test` to avoid a Makefile dependency in CI; the Makefile targets authored in TASK-004 are a convenience wrapper around the same commands.

## Testing Notes

Full end-to-end verification requires pushing the repository to GitHub and observing a workflow run. Local verification performed:
- YAML parses cleanly (well-formed structure, no tab characters, correct indentation)
- All referenced actions use pinned major versions (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/cache@v4`)
- Step ordering is correct: checkout → setup-python → cache → install prod → install dev → dbt deps → unit tests → e2e tests
- `dbt deps --profiles-dir .` step ensures packages are present before the e2e test invokes `dbt build` via subprocess, matching the gap identified in the task spec

## Completion Notes

*Fill in on merge.*
