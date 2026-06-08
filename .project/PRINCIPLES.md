# Core Development Principles

These five principles govern how projects built under the maker conventions are structured and executed. They are tool-agnostic and apply regardless of the agent or IDE being used.

---

## 1. Local-First Development

An engineer should be able to clone a repository and run a meaningful portion of the component stack locally with no external dependencies.

**What this means in practice:**
- Services that cross logical network boundaries (databases, queues, external APIs, auth providers) are containerized and orchestrated locally via Docker Compose or equivalent
- Secrets needed for local development are checked in as `.env.example` files with non-sensitive defaults; the actual `.env` is gitignored
- Local networking replaces production hostnames — services discover each other via container names or localhost ports, not DNS
- Mock/stub external third-party services only when containerizing them is impractical; prefer actual containerized equivalents (e.g., LocalStack for AWS, Mailpit for SMTP)
- The README must document the single command to bring up the full local stack and confirm it works

**The test:** a new engineer on a fresh machine should be productive within one `git clone` + one `docker compose up` (plus any one-time credential setup for true external services).

---

## 2. Lightweight Automated Testing

Automated tests are a precision tool, not a coverage metric. The goal is confidence in key logic and integration points, not exhaustive coverage.

**Test categories:**
- **Unit tests** — cover non-trivial business logic and edge cases in isolation; fast, no I/O
- **Integration tests** — cover interactions at subsystem boundaries (e.g., service → database, service → queue); run locally against containerized dependencies
- **Critical path test** — one end-to-end test per meaningful use case type that exercises the full stack locally; this test is the primary regression signal

**What is not required:**
- Testing framework boilerplate, getters/setters, or trivial delegation
- Coverage percentage targets
- Tests that duplicate what the type system already guarantees

**Tests must run locally.** If a test requires a deployed environment, it is not an automated test — it is a manual verification step and should be documented as such.

Full guidance: `.project/TESTING.md`

---

## 3. Git Trunk Strategy

Two permanent branches: `dev` and `main`.

- `main` is always an accurate representation of what is in production
- `dev` is the integration branch where work accumulates before a release
- A **deployment** is the act of merging `dev` into `main`
- All feature work branches off `dev`
- Feature branches are kept current with `dev` via **rebase** — never merge `dev` into a feature branch
- Feature branches merge into `dev` upon completion via a pull request

**Branch naming:** `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`

Full guidance: `.project/WORKFLOW.md`

---

## 4. Infrastructure as Code

Every component of the stack — compute, storage, networking, configuration — must be expressible as code and reproducible from scratch with a single command or script.

**What this means in practice:**
- No manual cloud console steps; if it was clicked, it should be scripted
- Container images are built from committed Dockerfiles, not pulled from personal registries
- Local environment orchestration uses a checked-in `docker-compose.yml` (or equivalent)
- Production infrastructure is defined in IaC (Terraform, CDK, Pulumi, etc.) committed to the repo
- A `scripts/bootstrap.sh` (or equivalent) documents and executes any one-time setup steps
- The destroy-and-rebuild sequence must be documented and tested periodically

**The test:** delete everything except the git repo and credentials. The stack should be fully recoverable.

Full guidance: `.project/INFRASTRUCTURE.md`

---

## 5. Task-as-Documentation

High-level tasks begin and end as documentation artifacts. A task is not a ticket in an external system — it is a markdown file in the repository that accumulates context as work progresses.

**Task lifecycle:**
1. `tasks/todo/` — defined, not yet started
2. `tasks/development/` — actively being implemented
3. `tasks/testing/` — implementation complete, under verification
4. `tasks/completed/` — merged and done

**What a task file contains:**
- Objective: what needs to happen and why
- Acceptance criteria: the verifiable outcomes
- Implementation notes: decisions made, approaches tried, constraints discovered (filled in during development)
- Testing notes: what was verified and how (filled in during testing)
- Completion notes: final state, any follow-on work identified (filled in on completion)

The task file is the authoritative record of why a piece of work was done the way it was. PR descriptions and commit messages reference it but do not replace it.

Full guidance: `tasks/TASKS.md`
