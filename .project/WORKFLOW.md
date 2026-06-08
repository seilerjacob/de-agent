# Git Workflow

---

## Branch Structure

```
main        ← always matches production
├── hotfix/critical-bug   ← exception: branches from and merges back into main
└── dev     ← integration branch; accumulates completed features
    ├── feature/user-auth
    ├── fix/token-expiry
    └── chore/upgrade-postgres
```

`main` and `dev` are permanent and protected. All other branches are ephemeral.

`hotfix/` branches are the sole exception to the rule that all branches originate from `dev` — see [Production Hotfixes](#production-hotfixes) below.

---

## Starting Work

Always branch from the current tip of `dev`:

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git checkout -b feature/my-feature
```

If `git pull --ff-only` fails, investigate before proceeding — someone may have force-pushed dev.

---

## Staying Current

Rebase onto `dev` regularly, and always immediately before opening a pull request:

```bash
git fetch origin
git rebase origin/dev
```

If the rebase produces conflicts, resolve them commit by commit. Do not use `git merge dev` to update a feature branch — this pollutes history and makes the eventual merge harder to read.

---

## Committing

- Commits on feature branches should be logical units of work, not checkpoints
- Write commit messages in imperative mood: "Add rate limiting to auth endpoint" not "Added..." or "Adding..."
- Keep the subject line under 72 characters
- If a commit needs explanation, add a blank line after the subject and write the body

---

## Merging to Dev

When a feature is complete:

1. Rebase onto the current tip of `dev` (see above)
2. Open a pull request targeting `dev`
3. The PR description should reference the task file (`tasks/completed/TASK-XXX.md`) and summarize what changed and why
4. Squash or preserve commits based on whether the individual commits tell a meaningful story; single-commit features should not be squashed further
5. Delete the feature branch after merge

---

## Deploying (dev → main)

A deployment is a merge of `dev` into `main`. This should only happen when:

- All tests pass on `dev`
- The critical path test passes
- All tasks intended for this release are in `tasks/completed/`

```bash
git checkout main
git merge --no-ff dev -m "deploy: <brief description of release>"
git push origin main
git push origin dev
```

The `--no-ff` flag preserves the merge commit so the deployment boundary is visible in history.

---

## Production Hotfixes

`hotfix/` branches are the only branches that originate from `main`. Use them exclusively when a bug in production requires a fix that cannot wait for the next `dev` → `main` deployment cycle.

**Agent boundary:** agents must not create `hotfix/` branches, open PRs targeting `main` from a hotfix branch, or merge a hotfix branch into `main`. These actions require a human decision. Agents may commit fixes onto an existing `hotfix/` branch once a human has created it.

**Process (human-executed steps marked):**

```bash
# [HUMAN] 1. Decide a hotfix is warranted and create the branch
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -b hotfix/brief-description

# [AGENT OK] 2. Implement the fix; critical path test must pass locally

# [HUMAN] 3. Open a PR targeting main and review it
# PR description must explain why this could not go through dev

# [HUMAN] 4. Merge the PR into main

# 5. After merge to main, immediately bring dev current
git checkout dev
git rebase origin/main
git push origin dev
```

**Task requirement:** create a task file in `tasks/completed/` before or alongside the PR. The task must document what broke, why it could not wait, and what the fix does. This is the audit trail.

**What qualifies as a hotfix:**
- Data loss or corruption actively occurring in production
- Security vulnerability being actively exploited or imminently exploitable
- Total outage of a critical path

**What does not qualify:**
- A bug that is annoying but not blocking production use
- A fix that is already on a feature branch nearly ready to merge
- Anything that can ship in the next planned deployment

If in doubt, it is not a hotfix.

---

## Rules Summary

| Rule | Detail |
|---|---|
| Feature branches source | Always `dev` |
| Hotfix branches source | `main` only — **human creates the branch**; see Production Hotfixes |
| Staying current | Rebase onto `dev`, never merge |
| Merging feature → dev | Pull request only |
| Merging hotfix → main | **Human only** — agents may not open or merge this PR |
| Merging dev → main | `--no-ff` merge, signals a deployment |
| Direct push to `dev` or `main` | Never |
