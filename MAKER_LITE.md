# Maker Lite

Maker lite is a personal workflow overlay for projects where full maker integration is not appropriate — projects with existing conventions you cannot unilaterally change, shared codebases with their own structure, or third-party repos where adding maker artifacts to the remote would be unwelcome noise.

In lite mode, your personal working discipline is governed by maker principles, but the project remote stays untouched. Maker files exist locally and are hidden from git entirely.

---

## What Changes Between Full and Lite

| Area | Full Integration | Maker Lite |
|---|---|---|
| `.project/` principle docs | Committed to repo | Local only, gitignored |
| `CLAUDE.md` | Committed to repo | Local only, gitignored |
| `tasks/` tracking | Committed to repo | Local only, gitignored |
| `MAKER_ONBOARDING*.md` | Committed to repo | Local only, gitignored |
| Tests you write | Committed | Committed — tests are code contributions |
| Git branching discipline | Enforced via repo config (branch protection, PR rules) | Personal discipline only; adapt to project's existing trunk strategy |
| Docker/local dev setup | Added to project if missing | Use project's existing local dev approach; note gaps privately in tasks |
| IaC | Added or conformed to project | Use project's existing infrastructure approach; note gaps privately |

The through-line: in lite mode, you still apply maker discipline to *your behavior* — how you branch, how you track work, how you structure tests — but you do not impose maker structure on the project itself.

---

## The Isolation Mechanism

Lite mode uses `.git/info/exclude` to hide maker files from git. This file is a per-repository local gitignore that:

- Is never committed or pushed
- Does not appear in `git status` for you or any other contributor
- Does not require modifying the project's `.gitignore`
- Persists across branch switches and stashes
- Is lost on a fresh `git clone` (re-run setup after cloning)

Do not add maker files to the project's `.gitignore`. That file is committed and would make your local setup visible to others.

---

## Setup

Run the setup script from the repository root after copying maker files into the project:

```bash
bash .project/scripts/setup-maker-lite.sh
```

The script adds all maker file paths to `.git/info/exclude`. After running it, verify with `git status` — maker files should not appear as untracked.

To confirm the exclusions are in place:

```bash
cat .git/info/exclude
```

---

## Re-setup After Cloning

`.git/info/exclude` does not survive a fresh clone. After cloning a repo where you use maker lite:

1. Copy the maker files in (or keep them in a separate location and copy them in)
2. Re-run `bash .project/scripts/setup-maker-lite.sh`

Consider keeping your maker files in a separate directory (e.g., `~/maker/`) and maintaining a per-project copy routine, or using a git template directory to automate the exclusion entries.

---

## Adapting Each Principle in Lite Mode

### 1. Local-First Development

You cannot add `docker-compose.yml` if the project doesn't have one and the change would be disruptive. Instead:

- Use the project's existing local dev setup
- Document gaps in a task file (`tasks/todo/`) for your own reference
- Where possible, run dependencies in containers locally even if the project doesn't formalize this — your local environment, not the repo

If the project has a `docker-compose.yml`, you may extend it locally via `docker-compose.override.yml` — this file can be added to `.git/info/exclude` if you don't want it committed.

### 2. Lightweight Automated Testing

Tests are code contributions and are committed regardless of mode. Apply the same testing philosophy:

- Unit tests for non-trivial logic you write
- Integration tests at subsystem boundaries your code touches
- If the project lacks a critical path test and adding one is reasonable, add it

The difference in lite mode is that test *structure* conforms to the project's existing patterns, not necessarily to maker's naming or organization conventions.

### 3. Git Trunk Strategy

The project may not have a `dev`/`main` structure. Adapt:

- Branch off whatever the project's integration branch is (`main`, `master`, `develop`, `trunk`)
- Apply the rebase discipline personally — keep your branches current via rebase regardless of what the project enforces
- Never push directly to the integration branch
- Do not create a `dev` branch if the project doesn't use one — this would be confusing to other contributors

The spirit of the principle (clean history, intentional integration, no direct pushes to the trunk) applies even when the specific branch names don't.

### 4. Infrastructure as Code

Do not add IaC to a project that doesn't have it unless that work is sanctioned. In lite mode:

- Use the project's existing infrastructure tooling
- Note gaps in your local task files
- If you are asked to make infrastructure changes, apply IaC principles to those changes even if the project doesn't fully codify this

### 5. Task-as-Documentation

The task system is entirely local in lite mode. The `tasks/` directory lives in your working tree but is invisible to git. This means:

- You still maintain task files and move them through the lifecycle
- The implementation record exists on your machine but does not accompany the PR
- PR descriptions carry more weight in lite mode — they are the externally visible record of why changes were made

If the project uses an external tracker (Jira, Linear, GitHub Issues), use it in parallel. Your local task file is your working notes; the external tracker is the shared record.

---

## Naming Conflicts

If the project already uses a `tasks/` directory for something else, rename the maker task directory to avoid collision. Update the paths in `CLAUDE.md` and add the new name to `.git/info/exclude`.

Suggested alternatives: `.maker-tasks/`, `.work/`, `.inbox/`

---

## Transitioning from Lite to Full

If the project context changes and full integration becomes appropriate:

1. Run `MAKER_ONBOARDING.md` in full mode to produce a fresh conformance plan
2. Remove the maker entries from `.git/info/exclude`
3. Commit `.project/`, `tasks/`, and `CLAUDE.md` in a single `chore: add maker project conventions` commit on a feature branch targeting `dev`
4. Complete the conformance plan action items as subsequent tasks
