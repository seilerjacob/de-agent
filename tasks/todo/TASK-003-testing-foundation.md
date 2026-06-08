---
id: TASK-003
title: Add automated testing foundation — pytest unit, integration, and critical path
status: todo
created: 2026-06-08
updated: 2026-06-08
branch: feature/testing-foundation
---

## Objective

The project has no automated tests. Add a pytest-based test suite covering: unit tests for the ingestion column-mapping logic in `ingestion/load_raw.py`, and a critical path end-to-end test that runs the full pipeline (seed → ingest → dbt build) and asserts the expected shape of the curated output tables. The dbt model YAML files already declare generic tests (unique, not_null, accepted_values) — these are exercised by the critical path test via `dbt build`.

## Acceptance Criteria

- [ ] `tests/unit/test_load_raw.py` exists with unit tests for `extract_sqlite_tables` covering: happy path, missing DB file returns empty or raises, table naming
- [ ] `tests/e2e/test_pipeline.py` exists with a critical path test that seeds both CRMs, runs `load_to_raw`, runs `dbt build`, and asserts `int_unified_customers` and `int_unified_products` row counts and column presence
- [ ] All tests pass locally via `pytest tests/`
- [ ] `requirements-dev.txt` (or updated `requirements.txt`) includes `pytest`
- [ ] Makefile `test`, `test-unit`, `test-e2e` targets are present (Makefile may be authored in TASK-004 if that branch lands first — coordinate)
- [ ] Critical path test passes locally

## Implementation Notes

*Fill in during development.*

## Testing Notes

*Fill in during testing.*

## Completion Notes

*Fill in on merge.*
