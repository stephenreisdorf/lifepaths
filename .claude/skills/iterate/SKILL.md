---
name: iterate
description: Execute the backlog — work the top item in Backlog/README.md's `## Order` queue end-to-end (implement, verify, then FF-merge to main and push), filing new backlog items for issues found along the way. Use when asked to iterate on / work / ship the next backlog item. Ordering is owned by the separate `backlog` skill (run `/backlog sort` first). Args: none (optionally a "<item-slug>" to jump a specific item).
---

# Iterate — execute the top backlog item to main

This skill is about **execution**: taking one already-prioritized item from open to shipped. It does
**not** decide priority — that concern belongs to the [`backlog`](../backlog/SKILL.md) skill, which
persists the execution sequence as the `## Order` queue in `Backlog/README.md`. `/iterate` always
works the **first** entry in that queue.

Unlike backlog management, this ships: it branches, implements, verifies, commits, and **FF-merges
to `main` and pushes**. It does **one item per invocation**, then stops; wrap it in `/loop` to drain
the queue continuously.

**Argument:** none → the top item in `## Order`. An optional `<item-slug>` (filename without `.md`)
jumps a specific item instead.

Run the pipeline below in order. The verify gate in step 3 is the safety net: a red suite or a
failed `## Done when` check blocks archive, commit, **and** push.

---

## 1. Pick the item

- If an `<item-slug>` was given, use it.
- Otherwise read `Backlog/README.md` and take the **first** entry in the `## Order` queue.
  - If there is no `## Order` section, or it's empty, **stop** and tell the user to run
    `/backlog sort` first — `iterate` does not rank the backlog itself.

State the chosen item (title + file path), then proceed — this skill is non-interactive.

## 2. Execute

- **Branch off `main` first** — never edit on `main`.
- Read `Backlog/<slug>.md`. Restate its goal, scope, and `## Done when` criteria. If it has no
  `## Done when`, derive concrete acceptance criteria from its body and state them.
- Implement per repo conventions: imports use the `src.` prefix; if architecture notes change, keep
  `CLAUDE.md` and `AGENTS.md` in sync (they are near-duplicates by design).

## 3. Verify honestly

Run `uv run pytest`, then each `## Done when` check, reporting real output.

**If anything fails: stop.** Do not archive, do not commit, do not push. Report the branch name and
the failure so it can be picked up manually.

## 4. Capture discovered issues

For any unrelated bug or opportunity you notice while working (not part of this item's scope), file
it exactly as the `backlog` skill's **Mode 2 (add)** does: create `Backlog/<kebab-slug>.md` from
`../backlog/item-template.md`, add its bullet to the correct category section of
`Backlog/README.md`, and append it to the end of the `## Order` queue. Leave precise
re-prioritization to the next `/backlog sort`.

## 5. Commit atomically (only on all-green)

- Move the worked item to `Backlog/done/<slug>.md`; remove its bullet from its category section **and**
  its entry from the `## Order` queue in `Backlog/README.md`.
- **Commit 1** — the code changes **and** this item's backlog archival (queue + category removal),
  together.
- **Commit 2** — only if step 4 filed anything: the newly-created backlog item files and their
  README additions (kept separate from the feature commit so each commit is atomic).
- End every commit message with the trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  ```

## 6. Ship to main

Fast-forward `main` and push, as **two separate git commands** — combined push commands are blocked
in this environment, so never chain merge and push:

```
git checkout main
git merge --ff-only <branch>
git push
```

Report the merged commit(s) and confirm the push succeeded.

## 7. Report

Summarize: the item shipped, `pytest` / `## Done when` results, any new backlog items filed, and the
final state of `main`.
