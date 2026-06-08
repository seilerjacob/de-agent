# Testing Philosophy

Tests are a precision instrument. Write them where they provide confidence that would otherwise require manual verification; skip them where they would only validate the compiler or the framework.

---

## The Three Categories

### Unit Tests

**Purpose:** verify that a discrete piece of logic produces correct output given known inputs.

**Scope:** one function, one class, one pure transformation. No network I/O, no database, no filesystem (except where the function's purpose is to interact with those things — test the contract, not the side effect).

**When to write them:**
- Non-trivial business logic with multiple code paths
- Parsing or transformation logic where edge cases matter
- Any function that has surprised you or could surprise someone else

**When to skip them:**
- Simple delegation or pass-through functions
- Logic already enforced by the type system
- Straightforward CRUD where the test would just restate the implementation

**Speed target:** the full unit suite should run in seconds locally.

---

### Integration Tests

**Purpose:** verify that two subsystems interact correctly at their boundary.

**Scope:** one interaction crossing a subsystem boundary — service writes to database, job enqueues a message, API validates a token. The test exercises real code against a real (containerized) dependency, not a mock.

**When to write them:**
- Any new integration point between services or a service and infrastructure (database, cache, queue, storage)
- Whenever a contract between subsystems changes
- When a bug was caused by a mismatch between what one side assumed and what the other side produced

**When to skip them:**
- Interactions already covered by the critical path test with sufficient specificity
- Pure infrastructure plumbing with no business logic (e.g., connection pooling configuration)

**Dependency requirement:** integration tests run against containerized dependencies defined in `docker-compose.yml`. A test that requires a deployed environment is not an integration test.

---

### Critical Path Test

**Purpose:** exercise one representative end-to-end use case through the full local stack to confirm the system works as a whole.

**Scope:** one test per meaningful use case type (not one per feature). The test drives the system from its public entry point (API call, UI action, CLI command) through to an observable outcome (database state, API response, file on disk).

**Characteristics:**
- Slow is acceptable; this runs less frequently than unit/integration tests
- It must pass locally before any merge to `dev`
- It is the primary regression signal — a failure here means something fundamental broke

**How many:** one per distinct use case type, not one per feature. If your system has three fundamentally different workflows, you have three critical path tests. If it has one workflow with many configuration variations, you have one critical path test parameterized appropriately.

---

## What Tests Are Not Required To Cover

- Code paths that the type system makes impossible
- Framework behavior (e.g., that your ORM correctly implements SQL)
- Configuration values (test that they're loaded, not their content)
- Logging and metrics emission (unless the emission is the feature)

---

## Running Tests Locally

Tests must run locally. The commands to do so should be documented in the project README and should work immediately after `docker compose up`.

Suggested targets (adapt to the project's tooling):

```bash
# unit tests only — fast feedback
make test-unit

# integration tests — requires local stack running
make test-integration

# critical path — full stack, slowest
make test-e2e

# all tests
make test
```

---

## CI Requirements

The CI pipeline runs all three test categories on every pull request targeting `dev`. A PR may not merge if any test fails. The critical path test is included in CI; its slowness is acceptable because merges to `dev` are a deliberate act.
