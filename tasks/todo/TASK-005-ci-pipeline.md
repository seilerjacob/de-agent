---
id: TASK-005
title: Add GitHub Actions CI pipeline
status: todo
created: 2026-06-08
updated: 2026-06-08
branch: chore/ci-setup
---

## Objective

Add a GitHub Actions workflow that runs the full test suite on every push and on PRs targeting `dev`. CI must run unit tests and the critical path end-to-end test. This requires a remote to be configured — the workflow file is committed now so it is ready when the repo is pushed to GitHub.

Note: this task cannot be fully verified until a remote is configured. The workflow file should be authored to match the Makefile targets from TASK-004.

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` committed
- [ ] Workflow triggers on `push` to any branch and on `pull_request` targeting `dev`
- [ ] Workflow installs Python dependencies from `requirements.txt` (and `requirements-dev.txt` if present)
- [ ] Workflow runs `make test` (or equivalent pytest commands)
- [ ] Workflow fails if any test fails
- [ ] YAML is valid (verifiable with `yamllint` or similar)

## Implementation Notes

*Fill in during development.*

## Testing Notes

Cannot fully test until remote is configured. YAML validity should be checked locally.

## Completion Notes

*Fill in on merge.*
