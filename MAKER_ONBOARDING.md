# Maker Onboarding

This document instructs an agent how to audit an existing project against the maker principles and produce a conformance plan for human review. The agent performs a read-only survey and writes a plan document — it makes no changes to the project.

Two integration modes are possible. The audit must assess which mode is appropriate and recommend one. See `MAKER_LITE.md` for the full description of each mode.

| Mode | When to use |
|---|---|
| **Full** | You own the project or have authority to change its conventions; maker artifacts belong in the remote |
| **Lite** | Shared or third-party project; you cannot impose structure on other contributors; maker files stay local only |

---

## Prerequisites

The following files must be present in the project before beginning:

```
.project/PRINCIPLES.md
.project/WORKFLOW.md
.project/TESTING.md
.project/INFRASTRUCTURE.md
.project/ORCHESTRATION.md
tasks/TASKS.md
tasks/templates/task.md
CLAUDE.md
```

If any are missing, stop and notify the human before proceeding.

---

## Process Overview

```
1. Read the maker principles and MAKER_LITE.md
2. Survey the project (read-only)
3. Assess mode fit (full vs. lite)
4. Assess each principle against findings
5. Write the onboarding plan to MAKER_ONBOARDING_PLAN.md
6. Present the plan to the human for review
```

The agent must not modify any project files, create branches, run tests, or execute build commands during this process. All operations are read-only.

---

## Step 1: Read the Principles

Before surveying the project, read all five principle documents and the lite mode reference in full:

- `.project/PRINCIPLES.md`
- `.project/WORKFLOW.md`
- `.project/TESTING.md`
- `.project/INFRASTRUCTURE.md`
- `tasks/TASKS.md`
- `MAKER_LITE.md`

Do not begin the survey until these are read. The audit questions below reference specific requirements from these documents.

---

## Step 2: Survey the Project

Use the Explore subagent to gather facts in parallel. Spawn independent research streams simultaneously rather than sequentially. Each stream should return specific facts, not summaries.

### Recommended parallel research streams

**Stream A — Repository structure**
- List all files in the repository root
- List all files in any `scripts/`, `infra/`, `deploy/`, `terraform/`, `cdk/`, or `pulumi/` directories if present
- Check for `Makefile`, `docker-compose.yml`, `docker-compose.yaml`, `.env.example`, `.env.sample`
- Check for `Dockerfile` files anywhere in the tree

**Stream B — Git state**
- List all local and remote branches: `git branch -a`
- Check for `dev` and `main` (or `master`) branches
- Inspect the last 20 commits on the default branch: `git log --oneline -20`
- Check whether recent commits come from feature branches or direct pushes: `git log --oneline --merges -10`

**Stream C — Test suite**
- Find all test files (look for patterns: `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, files in `__tests__/`, `tests/`, `test/`, `spec/`)
- Read `package.json` scripts section, `Makefile` test targets, `pyproject.toml`, `Cargo.toml`, or equivalent for test commands
- Check CI configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`) for test steps

**Stream D — Infrastructure and local dev**
- Read `docker-compose.yml` if present: list services, volumes, healthchecks, and exposed ports
- Read any `Dockerfile` files: note base image versions and multi-stage build usage
- Read the project README for local setup instructions
- Look for a bootstrap or setup script in `scripts/`

**Stream E — Existing task/ticket system**
- Check for `tasks/` directory and its contents
- Look for references to external trackers in README or docs (Jira, Linear, GitHub Issues, etc.)
- Check for any existing planning documents (`.md` files in root or `docs/`)

Synthesize all stream results before moving to Step 3.

---

## Step 3: Assess Mode Fit

Before evaluating individual principles, determine which integration mode is appropriate for this project. This shapes what the onboarding plan recommends and what the human needs to decide.

**Signals that favor Full integration:**
- You are the sole owner or have authority to change project conventions
- The project has no other contributors, or other contributors would accept maker conventions
- The project is greenfield or early enough that structural changes are low-friction
- There is no existing CI/CD or branch protection that would conflict with maker's git strategy

**Signals that favor Lite mode:**
- The project has other active contributors who have not agreed to maker conventions
- The project is an upstream, vendor, or third-party repo you are working within
- Branch protection rules, CI configuration, or existing `CLAUDE.md` files constrain what can be changed
- Adding committed files to the repo requires review processes that are not worth the overhead for tooling/conventions

**Cannot Assess signals:**
- Contributor count and ownership are not determinable from the repo alone
- Access controls are unknown

Record the mode recommendation and its rationale. This becomes the first section of the onboarding plan and the most important human decision — everything else in the plan is conditional on it.

---

## Step 4: Assess Each Principle

For each principle, evaluate the findings against the specific requirements below. Assign a status:

| Status | Meaning |
|---|---|
| **Compliant** | Meets the requirement as defined in the principle docs |
| **Partial** | Some requirements met; specific gaps identified |
| **Gap** | Requirement not met; action needed |
| **Cannot Assess** | Insufficient information from a static read; human or runtime verification needed |

---

### Principle 1: Local-First Development

| Check | Look for |
|---|---|
| Docker Compose present | `docker-compose.yml` or `docker-compose.yaml` in repo root |
| All dependencies containerized | Each external dependency (DB, cache, queue, storage) has a service definition |
| Services have healthchecks | `healthcheck:` defined on stateful services; dependent services use `condition: service_healthy` |
| Environment template present | `.env.example` or `.env.sample` checked in; actual `.env` is gitignored |
| Single startup command documented | README contains a `docker compose up` (or equivalent) as the primary local dev instruction |
| No undocumented host-level prerequisites | README does not require manual installation of databases, runtimes, or system packages beyond Docker and the language runtime |

---

### Principle 2: Lightweight Automated Testing

| Check | Look for |
|---|---|
| Unit tests exist | Test files that import no I/O dependencies; fast, isolated |
| Integration tests exist | Tests that run against a real (containerized) dependency |
| Critical path test exists | At least one end-to-end test that exercises a full use case from entry point to observable outcome |
| Tests run locally | Test commands do not require a deployed environment or external credentials |
| Test commands are documented | `Makefile`, `package.json` scripts, or README documents how to run each category |
| CI runs all three categories | CI config includes unit, integration, and e2e steps |

Note: if the test suite cannot be classified into these categories from a static read, mark as Cannot Assess and flag for human input.

---

### Principle 3: Git Trunk Strategy

| Check | Look for |
|---|---|
| `dev` branch exists | Present in remote branches |
| `main` (or `master`) branch exists | Present in remote branches |
| Feature branches target `dev` | Recent merged PRs target `dev`, not `main` |
| No direct pushes to `main` | Commit history on `main` shows only merge commits from `dev` (and any prior hotfixes) |
| Branch naming follows convention | Recent branches use `feature/`, `fix/`, `chore/`, or `hotfix/` prefixes |
| `hotfix/` branches (if any) originated from `main` | Check branch points in git log |

---

### Principle 4: Infrastructure as Code

| Check | Look for |
|---|---|
| IaC directory present | `infra/`, `deploy/`, `terraform/`, `cdk/`, `pulumi/` or equivalent |
| Dockerfiles committed | Application services have committed Dockerfiles |
| Base images are pinned | Dockerfile `FROM` lines use specific version tags, not `latest` |
| Multi-stage builds used where appropriate | Production images use multi-stage Dockerfiles |
| Bootstrap script exists | `scripts/bootstrap.sh` or `make bootstrap` or equivalent |
| Rebuild sequence documented | README or a dedicated doc describes destroy-and-rebuild |

---

### Principle 5: Task-as-Documentation

| Check | Look for |
|---|---|
| Task directory structure exists | `tasks/todo/`, `tasks/development/`, `tasks/testing/`, `tasks/completed/` |
| Task template in place | `tasks/templates/task.md` |
| Existing work is tracked | Any in-flight work has corresponding task files, or is tracked elsewhere and needs migration |
| External tracker in use | References to Jira, Linear, GitHub Issues, etc. — flag for migration decision |

---

## Step 5: Write the Onboarding Plan

Write findings to `MAKER_ONBOARDING_PLAN.md` in the project root using the template below. Do not editorialize — report what was found and what the maker principles require. The human will decide what to act on and in what order.

```markdown
# Maker Onboarding Plan — [Project Name]

**Date:** YYYY-MM-DD  
**Audited against:** maker principles (.project/)

---

## Mode Recommendation

**Recommended mode:** Full Integration / Maker Lite *(choose one)*

**Rationale:**
[Explain what signals drove the recommendation. Reference specific findings — contributor 
count, existing branch protection, external tracker in use, ownership model, etc.]

**What changes based on this choice:**
- If Full: all maker files will be committed; the action list below applies in full
- If Lite: run `.project/scripts/setup-maker-lite.sh`; actions marked [LITE: SKIP] below 
  are not applicable; actions marked [LITE: PERSONAL] apply as personal discipline only

**Human decision required:** confirm the mode before any implementation begins.

---

## Executive Summary

[2–4 sentences: overall conformance posture, count of compliant / partial / gap areas, 
and the most important gap to address first. Note if the mode choice significantly 
changes the scope of work.]

---

## Findings by Principle

### 1. Local-First Development — [Status]

**Findings:**
- [Specific finding, referencing the file or absence of file]
- ...

**Gaps:**
- [What is missing or non-conformant]

**Recommended actions:**
- [LITE: SKIP / LITE: PERSONAL / BOTH] Action description

---

### 2. Lightweight Automated Testing — [Status]

[same structure — note: test actions are always BOTH since tests are committed in both modes]

---

### 3. Git Trunk Strategy — [Status]

[same structure — note: branch creation actions are LITE: PERSONAL; repo config changes are LITE: SKIP]

---

### 4. Infrastructure as Code — [Status]

[same structure]

---

### 5. Task-as-Documentation — [Status]

[same structure]

---

## Prioritized Action List

| Priority | Action | Effort | Principle | Mode |
|---|---|---|---|---|
| 1 | ... | Low / Medium / High | ... | Both / Full only / Personal |
| 2 | ... | ... | ... | ... |

Priority is ordered by: blocking severity first (gaps that prevent local development rank highest), 
then effort-to-value (low-effort, high-conformance items next), 
then foundational items that other changes depend on.

Effort estimates:
- **Low** — a single file change or addition, under an hour
- **Medium** — multiple files or requires understanding existing code, a few hours
- **High** — architectural change, new tooling, or migration of existing patterns

---

## Open Questions

[Items that cannot be assessed from a static read and require human input or runtime verification:]

- [Question 1]
- [Question 2]

---

## Cannot Assess

[Areas where a static audit was insufficient. Each entry should describe what would be needed 
to complete the assessment:]

- [Area]: requires [specific action, e.g., "running the test suite" or "access to CI logs"]
```

---

## Step 6: Present the Plan

After writing `MAKER_ONBOARDING_PLAN.md`, notify the human that the audit is complete and the plan is ready for review. Do not begin implementing any item from the plan. Implementation begins only after the human has reviewed the plan and explicitly authorized work to start, optionally as task files in `tasks/todo/`.

---

## Agent Constraints During Onboarding

- **No file modifications** — read only; do not alter any existing project file
- **No branch creation** — do not create `dev`, `main`, or any other branch
- **No commits** — do not stage or commit anything
- **No test execution** — do not run the test suite or build commands
- **No external calls** — do not fetch dependencies, pull images, or query external services
- **One output file only** — the only write operation permitted is creating `MAKER_ONBOARDING_PLAN.md`
