---
id: TASK-002
title: Add maker project conventions and onboarding scaffolding
status: completed
created: 2026-06-08
updated: 2026-06-08
branch: chore/add-maker-conventions
---

## Objective

Commit the maker framework files that were present on disk as untracked artifacts. Run the full maker onboarding audit (`MAKER_ONBOARDING.md`) to produce a conformance plan, then commit all scaffolding and the resulting plan. This establishes the maker task tracking system, principle documents, Claude Code entry point, and onboarding record for the project.

## Acceptance Criteria

- [x] `.project/` directory with all five principle documents committed
- [x] `CLAUDE.md` committed and correctly referencing `.project/` docs and `tasks/`
- [x] `tasks/` directory structure committed with template and subdirectories
- [x] `MAKER_ONBOARDING.md` and `MAKER_LITE.md` committed
- [x] `MAKER_ONBOARDING_PLAN.md` produced and committed
- [x] TASK-001 backfill task committed in `tasks/completed/`
- [x] Task files for follow-on onboarding work in `tasks/todo/`
- [x] PR references this task

## Implementation Notes

Mode selected: Full Integration. Project is solo-owned, two commits old, no remote configured, no other contributors. All maker files were already present on disk as untracked files — this commit formalizes them.

Onboarding audit identified four Gap-status principles and one Partial (Task-as-Documentation). Follow-on tasks TASK-003 through TASK-005 cover the remaining gaps.

## Testing Notes

No runtime tests for scaffolding files. Verified that `git status` after commit shows a clean working tree (all maker files tracked).

## Completion Notes

All maker scaffolding is now committed. The project has a functioning task system, principle docs, and Claude Code entry point. Follow-on gaps (testing, containerization, CI) are tracked as tasks in `tasks/todo/`.
