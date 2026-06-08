---
id: TASK-004
title: Add Dockerfile, docker-compose, Makefile, bootstrap script, and local dev docs
status: todo
created: 2026-06-08
updated: 2026-06-08
branch: feature/containerization
---

## Objective

The project has no containerization or single-command local dev setup. Add a `Dockerfile` with a pinned Python base image, a `docker-compose.yml` that runs the pipeline container, a `Makefile` with `run`, `test`, `test-unit`, and `test-e2e` targets, a `scripts/bootstrap.sh` for one-time setup, a `.env.example` documenting environment variables, and update the README to document the single-command startup and rebuild sequence.

The goal is that an engineer can clone the repo and run `make run` (or `docker compose up`) to execute the full pipeline without any host-level setup beyond Docker.

## Acceptance Criteria

- [ ] `Dockerfile` committed with pinned Python base image (not `latest`), installs `requirements.txt`, entrypoint is `python run_pipeline.py`
- [ ] `docker-compose.yml` at project root defines the pipeline service with a volume for the warehouse output
- [ ] `.env.example` checked in with comments for any environment variables (even if currently none required)
- [ ] `scripts/bootstrap.sh` exists, is idempotent, and handles any one-time setup steps
- [ ] `Makefile` has at minimum: `run`, `test`, `test-unit`, `test-e2e`, `build`, `clean` targets
- [ ] README updated with single-command startup (`make run` or `docker compose up`) and destroy-and-rebuild sequence
- [ ] Critical path test passes locally after these changes

## Implementation Notes

*Fill in during development.*

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
