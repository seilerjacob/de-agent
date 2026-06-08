# Task System

Tasks are markdown files that live in this directory and move through status subdirectories as work progresses. The filesystem is the task board.

---

## Directory Structure

```
tasks/
  TASKS.md          ← this file
  templates/
    task.md         ← copy this to create a new task
  todo/             ← defined, not yet started
  development/      ← actively being implemented
  testing/          ← implementation complete, under verification
  completed/        ← merged and done
```

---

## Creating a Task

1. Copy `tasks/templates/task.md` to `tasks/todo/TASK-XXX-short-title.md`
2. Assign the next available task number
3. Fill in the Objective and Acceptance Criteria sections
4. Leave Implementation Notes, Testing Notes, and Completion Notes empty

Task files are committed to the repository. Creating a task is the act of defining work clearly enough that someone else could pick it up.

---

## Moving a Task

| Transition | When | What to update |
|---|---|---|
| `todo/` → `development/` | Work begins | Add branch name, update `status` and `updated` fields |
| `development/` → `testing/` | Implementation complete | Fill in Implementation Notes |
| `testing/` → `completed/` | Merged to dev | Fill in Testing Notes and Completion Notes |

Move = `git mv tasks/todo/TASK-XXX.md tasks/development/TASK-XXX.md`. Commit the move with the task file update in the same commit.

---

## What Belongs in a Task

**Objective** — one paragraph: what needs to happen and why. Enough context that someone unfamiliar with the work can understand the motivation.

**Acceptance Criteria** — a checklist of verifiable outcomes. Each item should be answerable with yes/no. These become the merge checklist.

**Implementation Notes** — filled in during development. Key decisions, approaches considered and rejected, constraints discovered, external references consulted. This is the "why did we do it this way" record.

**Testing Notes** — filled in during testing. What was verified, how, and what edge cases were checked. If an acceptance criterion was modified during testing, note why.

**Completion Notes** — filled in on merge. Final state summary, any follow-on tasks identified, any technical debt incurred that should be tracked.

---

## What Does Not Belong in a Task

- Code snippets (those belong in the PR or commit)
- Status update logs ("updated 3pm, still working") — the git history is the log
- Links to ephemeral resources (Slack threads, shared screen recordings)
- Speculation about future work that has not been decided — create a new task if it's real

---

## Naming Convention

```
TASK-XXX-short-descriptive-title.md
```

- `XXX` is a zero-padded integer (001, 002, ...) — assign sequentially
- The short title uses kebab-case and describes the outcome, not the activity
  - Good: `TASK-012-add-rate-limiting-to-auth.md`
  - Avoid: `TASK-012-work-on-auth.md`

---

## Agents and Tasks

When an agent begins work on a task, the first action is to move the task file to `tasks/development/` and update its metadata. As the agent works, it adds to the Implementation Notes section incrementally — not in one batch at the end.

When implementation is complete, the agent moves the task to `tasks/testing/` before running any tests or verification. The Testing Notes are filled in as tests are executed.

The task file is committed with the same branch as the feature work and included in the pull request.
