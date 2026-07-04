---
name: backlog
description: Manage the lifepaths Backlog/ — sort the open items into an execution sequence persisted in Backlog/README.md, or add a new item with acceptance criteria. Use when asked to prioritize/order/sort the backlog or file a new backlog item. Execution (implement/verify/ship an item) lives in the separate `iterate` skill. Args: "sort" | "add <topic>".
---

# Backlog management

Manages `Backlog/` in this repo: one prose markdown file per issue, indexed by
`Backlog/README.md`. Completed items are archived under `Backlog/done/`.

This skill is about **backlog management only** — deciding *what's in the backlog* and *in what
order*. Actually working an item (implement / verify / commit / push) is the separate
[`iterate`](../iterate/SKILL.md) skill's job. Keep those concerns apart.

`Backlog/README.md` has two parts:

- A **`## Order`** section at the top: a numbered list of item links in execution sequence. This is
  the authoritative queue `iterate` consumes — it always works the first entry.
- The **category index** below it (`## Bugs` / `## UX` / `## Architecture` / `## Deferred`), each a
  bullet `- [Title](file.md) — one-line hook.` The categories describe *what kind* of work each item
  is; `## Order` decides *when* it runs.

Dispatch on the argument. If none is given, run **sort**.

- `sort` (or no arg) → Mode 1
- `add <topic>` → Mode 2

Always read the actual files before acting — the backlog changes between sessions.

---

## Mode 1 — Sort the backlog

Rank **every** open item into a single global execution sequence and persist it as the `## Order`
queue in `Backlog/README.md`. This is the only place the "what to work next" decision is made.

1. Read `Backlog/README.md`, then read **every** linked item file (not just the index hooks — the
   ordering signal lives in the item bodies).
2. Order all open items by, in priority:
   - **Explicit dependencies / ordering notes.** Items often name a prerequisite (e.g. one is
     called out as "the unstated prerequisite" or links to another as a blocker). A prerequisite
     always comes before the items that depend on it. Never place an item ahead of its own open
     dependency.
   - **Category priority:** Bugs > enabling Architecture > UX > Deferred.
   - **Effort / leverage cues** in the file (small items that unblock many others win ties).
   - `## Deferred` items sort to the end.
3. Write the result into `Backlog/README.md`:
   - Replace (or create) the `## Order` section at the top of the file with a numbered list, one
     entry per open item, in sequence: `1. [Title](file.md)` … Every open item appears exactly
     once. Do **not** touch the category sections below.
4. Report the resulting order (at least the top few) and a one-line rationale for the head of the
   queue and its prerequisites, if any.

**Edits `Backlog/README.md` only — no code changes, and do not commit.** This is a management
capture step; the user reviews it, and `iterate` commits the queue as part of shipping an item.

---

## Mode 2 — Add a backlog item

Capture new or completed work as a structured item. **Do not commit** — this is a lightweight
capture step; the user reviews and commits.

1. Gather context. Infer what you can from the repo (affected files, current behavior, related
   items); ask the user only for what you genuinely can't derive — the intended result, and why
   it matters.
2. Create `Backlog/<kebab-slug>.md` from `item-template.md` (in this skill directory). Fill:
   - `# Title` and a 1–2 sentence summary of the result/context and why it matters.
   - `## Problem` — what's wrong or missing today; cite `path:line` where useful.
   - `## Opportunity` or `## Scope` — the change and the files/modules it touches. Match the
     framing (`Opportunity` vs `Scope`) used by neighbouring items in the same category.
   - `## Done when` — an explicit, checkable acceptance list. This is the "how to assess it's
     done" and must be concrete: specific tests pass (`uv run pytest tests/...`), an endpoint or
     behavior is observable, or a structural condition exists (e.g. a file boundary). Avoid vague
     criteria like "works well".
   - `## Notes` — dependencies, ordering vs other items, and links like `[other](other.md)`.
3. Add one bullet to the correct category section of `Backlog/README.md` (Bugs / UX / Architecture /
   Deferred), matching the existing `- [Title](file.md) — hook.` style.
4. Append the item to the end of the `## Order` queue (its true position isn't authoritative until
   the next `sort`; appending just keeps it tracked). If no `## Order` section exists yet, leave it
   for a `sort` run to build.
5. Report the new file path, the category it was indexed under, and that it was queued.
