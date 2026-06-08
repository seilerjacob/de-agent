---
id: TASK-004
title: Add Dockerfile, docker-compose, Makefile, bootstrap script, and local dev docs
status: completed
created: 2026-06-08
updated: 2026-06-08
branch: feature/containerization
---

## Objective

The project has no containerization or single-command local dev setup. Add a `Dockerfile` with a pinned Python base image, a `docker-compose.yml` that runs the pipeline container, a `Makefile` with `run`, `test`, `test-unit`, and `test-e2e` targets, a `scripts/bootstrap.sh` for one-time setup, a `.env.example` documenting environment variables, and update the README to document the single-command startup and rebuild sequence.

The goal is that an engineer can clone the repo and run `make run` (or `docker compose up`) to execute the full pipeline without any host-level setup beyond Docker.

## Acceptance Criteria

- [x] `Dockerfile` committed with pinned Python base image (not `latest`), installs `requirements.txt`, entrypoint is `python run_pipeline.py`
- [x] `docker-compose.yml` at project root defines the pipeline service with a volume for the warehouse output
- [x] `.env.example` checked in with comments for any environment variables (even if currently none required)
- [x] `scripts/bootstrap.sh` exists, is idempotent, and handles any one-time setup steps
- [x] `Makefile` has at minimum: `run`, `test`, `test-unit`, `test-e2e`, `build`, `clean` targets
- [x] README updated with single-command startup (`make run` or `docker compose up`) and destroy-and-rebuild sequence
- [ ] Critical path test passes locally after these changes

## Implementation Notes

All six deliverables were implemented in a single commit on `feature/containerization`:

- `Dockerfile`: uses `python:3.11-slim` (pinned, not latest), copies `requirements.txt` first for layer caching, then copies the full project. Entrypoint is `python run_pipeline.py`.
- `docker-compose.yml`: single `pipeline` service, builds from local Dockerfile, mounts `./warehouse` as a bind volume so DuckDB output persists across container runs.
- `.env.example`: documents the pattern for future secrets/env vars; no values currently required.
- `scripts/bootstrap.sh`: idempotent — skips venv creation if `.venv` already exists, installs `requirements.txt` (and `requirements-dev.txt` if present). Made executable via `chmod +x`.
- `Makefile`: targets `run`, `build`, `clean`, `test`, `test-unit`, `test-e2e`, `bootstrap`. Uses tabs for indentation (required by make). Delegates test targets to `.venv/bin/pytest`.
- `README.md`: added Prerequisites, replaced Quick Start with Docker and local venv options, added Local Development table and Rebuild from Scratch sequence.

## Testing Notes

Verify the following against the committed files on `feature/containerization`:

- `Dockerfile` base image is `python:3.11-slim` (not `latest`)
- `docker-compose.yml` includes `./warehouse:/app/warehouse` volume mapping
- `scripts/bootstrap.sh` is executable (`ls -l scripts/bootstrap.sh` shows `-rwxr-xr-x`)
- `Makefile` indentation uses tabs (not spaces) — `cat -A Makefile` should show `^I` before recipe lines
- `README.md` contains Prerequisites, Option A (Docker), Option B (local venv), Local Development table, and Rebuild from Scratch section
- `.env.example` is present and contains comments

## Completion Notes

*Fill in on merge.*
