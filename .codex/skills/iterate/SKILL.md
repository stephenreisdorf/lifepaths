---
name: iterate
description: >-
  Execute the Lifepaths backlog queue end-to-end: choose the top item from
  Backlog/README.md's ## Order queue or an explicitly named backlog slug, create
  a codex/ branch from main, implement the item, verify it, archive the completed
  backlog file, commit, fast-forward merge to main, and push. Use when asked to
  iterate, work, implement, ship, or complete the next prioritized backlog item.
  Backlog prioritization belongs to the backlog skill; run that first if the
  queue is missing or stale.
---

# Iterate - ship one backlog item

Execute one already-prioritized Lifepaths backlog item from open to shipped. This skill does not rank the backlog; the `backlog` skill owns ordering through the `## Order` queue in `Backlog/README.md`.

Accept either no argument, meaning the first item in `## Order`, or an explicit `<item-slug>` filename without `.md`. Run non-interactively unless blocked by missing information, failing checks, merge conflicts, or required external approval.

## Workflow

1. Pick exactly one item.
   - If a slug was provided, use `Backlog/<slug>.md`.
   - Otherwise read `Backlog/README.md` and select the first entry in `## Order`.
   - If `## Order` is missing or empty, stop and tell the user to run the backlog sorting workflow first.
   - State the chosen title and path in a short progress update.

2. Prepare a branch.
   - Inspect `git status --short` before changing files. Preserve unrelated user changes.
   - Branch from `main` before edits, using the Codex branch prefix: `codex/<slug>` or a similarly clear `codex/` branch name.
   - If local state prevents clean branching, stop and explain the blocker.

3. Understand the item.
   - Read `Backlog/<slug>.md`.
   - Restate the goal, scope, and `## Done when` checks.
   - If the file has no `## Done when`, derive concrete acceptance criteria from its body and state them before implementing.
   - Follow repo conventions from `AGENTS.md`: imports use the `src.` prefix; architecture notes in `AGENTS.md` and `CLAUDE.md` stay in sync when either is changed.

4. Implement the smallest complete change.
   - Edit only files required by the chosen item, plus focused tests and backlog bookkeeping.
   - Use existing domain, engine, API, and frontend patterns.
   - Do not fold unrelated bugs or refactors into the item. Capture them as new backlog items instead.

5. Verify honestly.
   - Run `uv run pytest`.
   - Run every command or manual check named in `## Done when`.
   - Report real pass/fail results. If any required check fails, stop without archiving, committing, merging, or pushing. Leave the branch in place and report the branch name plus failure details.

6. Capture discovered issues.
   - For unrelated bugs or opportunities found along the way, create `Backlog/<kebab-slug>.md` using the same structure as `.claude/skills/backlog/item-template.md`: title, summary, `## Problem`, `## Opportunity` or `## Scope`, `## Done when`, and `## Notes`.
   - Add one bullet to the correct category section of `Backlog/README.md` using the existing `- [Title](file.md) — hook.` style.
   - Append the item to the end of `## Order` when that section exists. Leave precise reprioritization to the next backlog sort.

7. Archive the completed item only after all checks pass.
   - Move `Backlog/<slug>.md` to `Backlog/done/<slug>.md`.
   - Remove the completed item from its category section in `Backlog/README.md`.
   - Remove the completed item from the `## Order` queue.

8. Commit atomically.
   - Commit the implementation, tests, and completed-item archival together.
   - If step 6 created new backlog items, make a second commit containing only those new backlog files and README additions.
   - Use concise project-style commit messages. Do not add Claude attribution trailers. Add Codex attribution only if the user or repo explicitly asks for it.
   - After successful staging and commits, emit the Codex git stage and commit directives in the final response.

9. Ship to `main`.
   - Fast-forward `main` and push with separate git commands:

   ```bash
   git checkout main
   git merge --ff-only <branch>
   git push
   ```

   - If the merge is not a fast-forward or push fails, stop and report the branch and error. Do not force push.
   - After successful branch creation, push, or other git actions, emit the matching Codex git directives in the final response.

10. Report the result.
   - Summarize the shipped item, tests and acceptance checks, commits merged, any new backlog items filed, and final `main` state.
