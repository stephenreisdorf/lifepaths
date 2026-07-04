---
name: loop-iterate
description: >-
  Repeatedly execute the Lifepaths $iterate backlog-shipping workflow while
  controlling context growth. Use when the user asks to run /iterate, $iterate,
  or backlog iteration in a loop; continue through multiple prioritized backlog
  items; work until tokens run low; or avoid context blow-up between Lifepaths
  backlog items.
---

# Loop Iterate

Run the project-local `$iterate` workflow repeatedly without carrying detailed
context from one backlog item into the next. Treat each item as a complete
transaction whose durable memory is the repository state, commits, and a compact
checkpoint.

## Required Skill

Before starting work, read `.codex/skills/iterate/SKILL.md` completely and obey
it for every individual backlog item. This skill only orchestrates repeated
invocations; it does not replace `$iterate`'s implementation, verification,
archival, commit, merge, or push rules.

## Loop Contract

Run one backlog item at a time:

1. Start the cycle from the current `main` state.
2. Execute exactly one `$iterate` item to a terminal result.
3. If the item ships, checkpoint the result and intentionally discard detailed
   item context before selecting the next item.
4. If the item blocks or fails verification, stop the loop and report the
   branch, status, and blocker.

Never begin a second item while the previous item has uncommitted implementation
work, failing required checks, an unresolved merge/push problem, or incomplete
backlog archival.

## Cycle Start

At the start of each cycle, gather only fresh, minimal context:

- `git status --short`
- `git branch --show-current`
- `Backlog/README.md`, only enough to identify the first item in `## Order`
- the selected `Backlog/<slug>.md`
- relevant source files found with targeted `rg` searches

Do not preload previous item diffs, logs, or implementation details unless they
directly affect the new item's acceptance criteria.

## Checkpoint

After each shipped item, write a short progress update with only:

- shipped backlog title and path
- branch name and commit hash or subject
- verification commands and pass/fail status
- files changed at a high level
- new backlog items filed, if any
- current `main`/push status

Use this checkpoint as the handoff surface if context compacts. Keep it brief;
the repo and git history are the source of truth.

## Context Hygiene

After a successful checkpoint:

- treat prior item details as stale unless the next backlog item explicitly
  references them
- re-read the next backlog file instead of relying on memory of the queue
- inspect source from scratch with focused searches
- summarize rather than paste large outputs
- prefer commit hashes, file paths, and acceptance checks over prose history

If context budget becomes tight before starting a new item, stop after the last
completed checkpoint. If it becomes tight mid-item, finish the current safe
stopping point: either complete and ship the item, or leave the branch in a clear
blocked state with verification details.

## Stop Conditions

Stop immediately when any of these occur:

- `$iterate` would stop under its own rules
- `Backlog/README.md` has no usable `## Order` item
- required tests or acceptance checks fail
- branch creation, merge, or push cannot complete cleanly
- unrelated user changes make safe continuation ambiguous
- external approval is required and not already granted
- context budget is too low to start another item responsibly

Final reporting should list the number of items shipped, the final branch or
`main` state, the last checkpoint, and any blocker.
