# Subagent Orchestration

Agents working on complex tasks should decompose work into parallel streams wherever possible. Sequential execution is the default; override it deliberately when independent work can proceed simultaneously.

This document describes patterns for orchestrating subagents. Examples use Claude Code's `Agent` tool; the patterns themselves translate to any agent platform that supports parallel execution.

---

## When to Use Subagents

| Situation | Action |
|---|---|
| Need to understand an unfamiliar area of the codebase before writing anything | Spawn `Explore` agent(s) |
| Change touches more than two files or crosses a subsystem boundary | Spawn `Plan` agent first |
| Two or more files/subsystems can be modified without interdependency | Spawn parallel `claude` agents |
| Implementation is complete and needs real-world verification | Use `verify` skill or dedicated agent |
| Research question spans multiple documentation sources | Spawn parallel research agents |

Do not spawn a subagent for a change that fits in your current context and has no parallelizable components. Overhead is real.

---

## Pattern: Research Before Planning

Use this before designing a solution in an unfamiliar area.

**When:** the change involves code you haven't read yet, or spans multiple subsystems.

**Structure:**
1. Identify the specific questions you need answered (file locations, existing patterns, current contracts)
2. Spawn one `Explore` agent per independent question — they run in parallel
3. Synthesize the results yourself before writing any code

**Claude Code example:**
```
// Spawn two research agents in parallel
Agent(Explore): "Find all places where user authentication tokens are validated. 
                 Report file paths and line numbers. Quick search."

Agent(Explore): "Find the database schema for the sessions table. 
                 Report the migration file and current column definitions. Quick search."

// After both return: synthesize findings, then plan or implement
```

**Key principle:** write the agent prompts as specific questions with expected answer formats, not open-ended explorations. "Find where X is defined and report the file and line number" is better than "explore the authentication system."

---

## Pattern: Plan Before Multi-File Implementation

Use this before any change that touches more than two files or crosses a subsystem boundary.

**When:** you know what needs to change but not exactly how to structure it across files.

**Structure:**
1. Provide the `Plan` agent with the goal, relevant file paths (from prior research), and constraints
2. Review the plan before writing any code — push back if it introduces unnecessary abstraction or misses a simpler approach
3. Implement following the plan, not improvising

**Claude Code example:**
```
Agent(Plan): "Design the implementation for adding rate limiting to the auth API.
              Context: auth routes are in src/routes/auth.ts, middleware lives in 
              src/middleware/, Redis is already configured in src/lib/redis.ts.
              Constraint: must work with the existing Express middleware pattern.
              Return a step-by-step plan identifying which files change and what each change does."
```

---

## Pattern: Parallel Implementation

Use this when two or more independent changes need to happen.

**When:** the changes do not share modified files and neither depends on the output of the other.

**Structure:**
1. Decompose the work into fully independent streams — if stream B reads a file that stream A writes, they are not independent
2. Brief each agent completely — it has no context from the current conversation
3. Send all agent spawns in one message so they execute concurrently
4. After all return: integrate and verify

**Claude Code example (two independent streams):**
```
// Both agents start simultaneously

Agent(claude): "Add a `last_seen_at` column to the users table. 
                Migration file goes in db/migrations/ following the existing pattern 
                in db/migrations/20240101_add_email_verified.sql.
                Also update the User type in src/types/user.ts to include the field.
                Do not touch any other files."

Agent(claude): "Add request logging middleware to the Express app in src/app.ts.
                Log method, path, status code, and duration using the existing logger 
                at src/lib/logger.ts. Insert it as the first middleware before routes.
                Do not touch any other files."
```

**The brief must be self-contained.** Each agent starts cold. Include file paths, existing patterns, and constraints explicitly. "Follow the existing pattern in X" is better than "follow our conventions."

---

## Pattern: Research + Implement (Combined)

For tasks where research and implementation are clearly sequenced but each phase has internal parallelism.

**Structure:**
```
Phase 1 (parallel): multiple Explore agents gather facts
Phase 2 (sequential): synthesize and plan
Phase 3 (parallel): multiple implementation agents execute independent changes  
Phase 4 (sequential): integrate, test, verify
```

Do not skip Phase 2. Jumping from research directly into parallel implementation without synthesis produces agents that make inconsistent decisions.

---

## Briefing Subagents Effectively

Subagents have no memory of the current conversation. Every prompt must be self-contained.

**Always include:**
- What to do and why (the goal, not just the task)
- Relevant file paths and line numbers from prior research
- The specific constraint or pattern to follow
- What NOT to touch (scope boundary)
- Expected output format (especially for research agents)

**Avoid:**
- "Follow our conventions" without specifying what they are
- "Based on your findings, fix it" — the main agent does synthesis, not the subagent
- Vague scope ("update the auth system") — be specific about files

---

## Integrating Subagent Results

When subagents return:

1. Read the actual changes they made — do not trust the summary alone
2. Check for conflicts if multiple agents touched related areas
3. Run the test suite before reporting work as done
4. If a subagent's output is wrong, correct it directly — do not re-spawn with the same prompt

---

## Worktree Lifecycle and Cleanup

When agents run with `isolation: "worktree"`, Claude Code creates a git worktree under `.claude/worktrees/` and a corresponding `worktree-agent-*` branch. These are scaffolding — they have no value once the work is merged.

**Clean up immediately after validating and merging each agent's work.** Do not wait until the end of a session or leave worktrees across sessions.

### What to remove

**1. The worktrees themselves** (use `-f -f` if they were locked by the agent process):
```bash
git worktree remove -f -f .claude/worktrees/<agent-id>
```

**2. The `worktree-agent-*` bookkeeping branches** — pure artifacts, no semantic meaning:
```bash
git branch -d worktree-agent-<id>
```

**3. Feature branches after merge** — content lives on `dev`; branches are ephemeral:
```bash
git branch -d feature/<name>
```

### Why prompt cleanup matters

- Worktrees consume disk space (each is a full working tree checkout)
- Branches marked `+` in `git branch -a` are checked out in a worktree and cannot be switched to in the main working tree until the worktree is removed
- Stale `worktree-agent-*` branches add noise to branch listings with no informational value
- `.claude/worktrees/` shows as untracked in `git status` until gitignored

### `.gitignore` requirement

`.claude/` must be gitignored. It is transient agent tooling state — equivalent to `.venv/` or `node_modules/`. Add it on project setup:

```
# Agent tooling — transient, never committed
.claude/
```

### The one exception

Keep a worktree alive only if the agent's work produced an unexpected result and you need to inspect the intermediate state. Remove it once the investigation is complete.

---

## Translating to Other Agent Platforms

| Claude Code concept | Generic equivalent |
|---|---|
| `Agent(Explore)` | Read-only context-gathering agent or retrieval tool |
| `Agent(Plan)` | Planning/design agent or structured thinking step |
| `Agent(claude)` (parallel) | Parallel tool calls or concurrent agent threads |
| `verify` skill | Execution agent that runs the app and observes behavior |

The core principle — research → plan → parallel implement → integrate — is platform-independent.
