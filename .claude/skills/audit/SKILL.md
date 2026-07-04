---
name: audit
description: Coordinate a full codebase audit — `/audit ultimate` fans out five parallel focus subagents (rules-fidelity, architecture, UX, test-coverage, performance/dead-code), dedupes and impact-ranks their findings, files them all as backlog items, and ships the batch to main. `/audit <focus>` runs one focus standalone. Ordering/execution stay with the `backlog`/`iterate` skills. Args: "ultimate" | "rules|architecture|ux|tests|perf".
---

# Audit — coordinate a full codebase audit

Discovers backlog items systematically. Five focus audits each sweep the codebase from one angle;
this coordinator runs them together, merges the results, and ships a deduped, impact-ranked batch of
new backlog items to `main`. It **discovers and files** — it does not implement (that stays
[`iterate`](../iterate/SKILL.md)) or re-prioritize the whole queue (that stays
[`backlog`](../backlog/SKILL.md)).

The five focus skills live beside this one and are independently invokable:
`audit-rules`, `audit-architecture`, `audit-ux`, `audit-tests`, `audit-perf`.

Dispatch on the argument:

- **`ultimate`** → the full parallel run (below).
- **`rules` | `architecture` | `ux` | `tests` | `perf`** → passthrough: invoke the matching
  `audit-<focus>` skill standalone (it files directly to `Backlog/`, no commit). Nothing else.
- **no arg / anything else** → print usage: list the five focuses and `ultimate`, and stop. Do **not**
  spawn agents or commit.

---

## `ultimate` — the parallel run

The user invoked this, which is the explicit request to spawn subagents.

### 1. Prep

- Read `Backlog/README.md` (and note what's in `Backlog/done/`) so you can sanity-check the merged
  output against what's already tracked.
- Create a run directory in the session scratchpad and one empty target file per focus:
  `<scratchpad>/audit-run/{rules,architecture,ux,tests,perf}.md`. Use the **absolute** scratchpad
  path.

### 2. Fan out — five subagents in parallel

In a **single message**, spawn **five `general-purpose` subagents** (one Agent call each, so they run
in parallel). Each prompt, substituting `<focus>` and the absolute output path:

> Use the Skill tool to invoke the `audit-<focus>` skill with the argument
> `--candidates <scratchpad>/audit-run/<focus>.md`. Do the full sweep the skill describes and append
> every finding to that exact file using its candidate template. Do not touch `Backlog/` and do not
> commit. Return a one-paragraph summary and your finding count as your final message.
> If you cannot resolve the skill by name, read
> `/Users/stephenreisdorf/projects/lifepaths/.claude/skills/audit-<focus>/SKILL.md` and follow it.

Wait for all five to complete.

### 3. Collect

`Read` all five `<scratchpad>/audit-run/*.md` files. Parse the candidate blocks (fields defined in
`candidate-template.md`).

### 4. Dedupe

Merge findings that name the same file/concern across focuses into one item: union their `Files`
refs, keep the sharpest Problem/Opportunity framing, take the **highest** severity raised, and record
in Notes which focuses surfaced it (cross-focus agreement is a strong impact signal). Also drop any
finding that merely restates an item already open in `Backlog/` or shipped in `Backlog/done/`.

### 5. Rank

Order survivors by impact using the same priorities `/backlog sort` uses: Bugs/fidelity > enabling
Architecture > UX > Deferred; higher severity first; small items that unblock others win ties; respect
any stated dependency (never rank an item ahead of its open prerequisite).

### 6. File all

For **every** surviving finding, in ranked order:

- Create `Backlog/<slug>.md` from `../backlog/item-template.md`, filled from the candidate block
  (`# Title`, intro, `## Problem` with `path:line` refs, `## Opportunity`/`## Scope` per its category,
  `## Done when` checklist, `## Notes` incl. which focuses raised it).
- Add its bullet to the correct category section of `Backlog/README.md`
  (`- [Title](slug.md) — hook.`). Introduce a `## Fidelity` and/or `## Performance` section (mirroring
  the existing category sections) only if you have findings for it; otherwise map to the closest
  existing category (Bugs / UX / Architecture).
- Append it to the `## Order` queue **in ranked sequence**, after the existing entries. (Precise
  global re-prioritization is left to the next `/backlog sort`.)

Keep `Backlog/README.md` internally consistent: every filed item appears exactly once in `## Order`
and exactly once under a category.

### 7. Ship to main

Mirror `iterate`'s discipline. Run these as **separate** commands — combined merge+push is blocked:

```
git checkout -b audit/run-<YYYY-MM-DD>
git add Backlog/
git commit -m "Audit run: file <N> discovered backlog items"   # + the trailer below
git checkout main
git merge --ff-only audit/run-<YYYY-MM-DD>
git push
```

End the commit message with:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

Only the new `Backlog/*.md` files and `Backlog/README.md` are in this commit — the audit suite
touches no source. If the working tree has unrelated pending changes, branch off the current `HEAD`
and commit **only** the `Backlog/` paths (`git add Backlog/`) so nothing unrelated is swept in; report
that you did so.

### 8. Report

A table of filed items (title · category · severity · focuses that raised it), the totals (raw
findings → deduped count → filed count), and confirmation that `main` was fast-forwarded and pushed.
Suggest `/backlog sort` to fold the new items into the global order, then `/iterate` to start working
them.
