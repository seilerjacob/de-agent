# Agent Instructions

This file is the Claude Code entry point for projects using the maker conventions.
Detailed principles live in `.project/`. The task tracking system lives in `tasks/`.

---

## Orientation

| Topic | File |
|---|---|
| Core development principles | `.project/PRINCIPLES.md` |
| Git branching and workflow | `.project/WORKFLOW.md` |
| Testing philosophy | `.project/TESTING.md` |
| Infrastructure conventions | `.project/INFRASTRUCTURE.md` |
| Subagent orchestration patterns | `.project/ORCHESTRATION.md` |
| Task system | `tasks/TASKS.md` |

---

## Task Lifecycle

Every non-trivial unit of work begins and ends as a task file.

1. Create or find the task in `tasks/todo/` using the template at `tasks/templates/task.md`
2. Move it to `tasks/development/` when work begins; update the file with the branch name
3. Move it to `tasks/testing/` when implementation is complete; fill in testing notes
4. Move it to `tasks/completed/` when merged to dev; add completion notes

Update the task file continuously as work progresses — it is the implementation record, not a status field.

---

## Git Rules (Summary)

- All work branches off `dev`
- Feature branches stay current with `dev` via **rebase** (never merge)
- `main` is production; it is only updated by merging `dev` into it
- Never push directly to `dev` or `main`

Full details: `.project/WORKFLOW.md`

---

## Subagent Orchestration

Claude Code agents should be spawned aggressively for parallelizable work. The default is to work sequentially; override that default whenever independent streams exist.

**Research before planning.** Use the `Explore` subagent to survey the codebase before designing a solution. Pass exact questions, not open-ended prompts.

**Plan before implementing multi-file changes.** Use the `Plan` subagent for any change touching more than two files or crossing subsystem boundaries.

**Parallelize independent implementation.** Spawn multiple `claude` agents when two or more files or subsystems can be modified without interdependency.

**Verify after implementing.** Use the `verify` skill or a dedicated agent to confirm the critical path works after any non-trivial change.

Full patterns with examples: `.project/ORCHESTRATION.md`

---

## Testing Requirements (Summary)

Every code change must include or update:
- Unit or integration tests covering the logic changed
- If the change touches a subsystem boundary, an integration test for that crossing

The critical path end-to-end test must remain passing at all times.

Full details: `.project/TESTING.md`

---

## Infrastructure

All environment dependencies are containerized. An engineer must be able to run the full local stack with a single command after cloning. Never introduce a dependency that requires manual host-level setup.

Full details: `.project/INFRASTRUCTURE.md`

---

## Adapting to Other Agent Tools

The `.project/` directory is tool-agnostic. When onboarding these conventions into a non-Claude Code environment:

- The content of `.project/PRINCIPLES.md` through `.project/INFRASTRUCTURE.md` maps directly to system prompt instructions or equivalent config in other tools
- `.project/ORCHESTRATION.md` describes patterns; translate the Claude Code-specific `Agent` tool usage to whatever parallel execution primitive the target tool provides
- The `tasks/` filesystem structure works in any environment that can read and write files
