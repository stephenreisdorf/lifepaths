---
name: backlog
description: Manage the lifepaths Backlog/ — recommend the next item to work, add a new backlog item with acceptance criteria, or execute an item end-to-end (implement, verify, commit). Use when asked to pick/suggest backlog work, file a backlog item, or work/close out a backlog item. Args: "suggest" | "add <topic>" | "execute <item-slug>".
---

# Backlog management

Manages `Backlog/` in this repo: one prose markdown file per issue, indexed by
`Backlog/README.md` under `## Bugs` / `## UX` / `## Architecture` / `## Deferred`, each a bullet
`- [Title](file.md) — one-line hook.`. Completed items are archived under `Backlog/done/`.

Dispatch on the argument. If none is given, run **suggest**.

- `suggest` (or no arg) → Mode 1
- `add <topic>` → Mode 2
- `execute <item-slug>` → Mode 3 (slug = the item filename without `.md`)

Always read the actual files before acting — the backlog changes between sessions.

---

## Mode 1 — Suggest the next item

Recommend the single best item to work next. **Read-only: make no file changes.**

1. Read `Backlog/README.md`, then read **every** linked item file (not just the index hooks —
   the ordering signal lives in the item bodies).
2. Rank candidates by, in order:
   - **Explicit dependencies / ordering notes.** Items often name a prerequisite (e.g. one is
     called out as "the unstated prerequisite" or links to another as a blocker). A prerequisite
     always outranks the items that depend on it. Never recommend an item whose stated
     dependency is still open.
   - **Category priority:** Bugs > enabling Architecture > UX > Deferred.
   - **Effort / leverage cues** in the file (small items that unblock many others win ties).
   - `## Deferred` items are recommended only when nothing else is actionable.
3. Output:
   - The one recommended item (title + file path).
   - A one-paragraph rationale grounded in the file contents.
   - Its blockers/prerequisites, if any.
   - 1–2 runners-up, one line each.

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
3. Add one bullet to the correct section of `Backlog/README.md` (Bugs / UX / Architecture /
   Deferred), matching the existing `- [Title](file.md) — hook.` style.
4. Report the new file path and the section it was indexed under.

---

## Mode 3 — Execute an item

Take an item from open to done: implement, verify, archive, commit.

1. Read `Backlog/<item-slug>.md`. Restate its goal, scope, and `## Done when` criteria back to
   the user before starting. If the item has no `## Done when` section, derive concrete
   acceptance criteria from its body and state them explicitly.
2. **Branch first.** If on `main` (the default branch), create a working branch before any edit,
   per the repo git rules. Never commit the work directly to `main`.
3. Implement the change following the item's scope and repo conventions:
   - Imports use the `src.` prefix.
   - If architecture notes change, keep `CLAUDE.md` and `AGENTS.md` in sync (they are
     near-duplicates by design).
4. **Verify honestly.** Run `uv run pytest`, then run each `## Done when` check. Report results
   with real output. If any check fails, **stop and report** — do not archive, do not commit, do
   not claim the item is done.
5. On all-green:
   - Move the item file to `Backlog/done/<slug>.md` (preserve the record).
   - Remove its bullet from `Backlog/README.md`.
   - Commit the code changes **and** the backlog changes together on the branch. End the commit
     message with the trailer:
     ```
     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
     ```
   - **Stop before push/PR** unless the user asks. Report the branch name and what was verified.
