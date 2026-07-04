# Audit output modes (shared by the five focus skills)

Every focus audit (`audit-rules`, `audit-architecture`, `audit-ux`, `audit-tests`, `audit-perf`)
does the same thing with its findings. Only the *sweep* differs; the output dispatch is identical and
lives here so the focus skills stay about their subject matter.

Dispatch on the argument the skill was invoked with:

## Standalone mode (no arg, or a plain focus arg)

File each finding directly into the backlog, exactly as the `backlog` skill's **Mode 2 (add)** does —
**but do not commit** (the user reviews and commits, or `iterate` ships later):

1. For each finding, create `Backlog/<slug>.md` from `../backlog/item-template.md`. Fill:
   - `# Title` (the finding's full-sentence title) + a 1–2 sentence intro of the result and why it matters.
   - `## Problem` — what's wrong today, citing `path:line` refs.
   - `## Opportunity` **or** `## Scope` — match the home category's convention (Opportunity for
     refactor/UX/perf; Scope for fidelity/feature).
   - `## Done when` — a checkable `- [ ]` list. Backend items end with `- [ ] uv run pytest passes.`
   - `## Notes` — dependencies, ordering, `[links](other.md)`.
2. Add one bullet to the correct category section of `Backlog/README.md`
   (`- [Title](slug.md) — one-line hook.`).
3. Append the item to the end of the `## Order` queue (true position isn't authoritative until the
   next `/backlog sort`; appending keeps it tracked).
4. **Do not commit.** Report each filed file path, its category, and that it was queued.

If a finding belongs in a `## Fidelity` or `## Performance` category that doesn't exist yet in
`Backlog/README.md`, create that section (mirroring the existing category sections) only if you have
findings for it; otherwise map to the closest existing category (Bugs / UX / Architecture).

## Coordinated mode (`--candidates <output-file>`)

Do **not** touch `Backlog/` and do **not** commit. Instead, for each finding, append one block to
`<output-file>` using `../audit/candidate-template.md` (keep its field names and order intact — the
`audit` coordinator parses them to dedupe and rank). Create `<output-file>` if it doesn't exist.
Finish by returning a one-paragraph summary and the finding count as your final message.

## Quality bar (both modes)

- Every finding names concrete `path:line` (or `path` + symbol) references — a finding with no anchor
  is not actionable, so don't file it.
- Severity is your honest impact estimate: **high** = correctness/rules/data-loss or blocks other
  work; **medium** = real but bounded; **low** = polish. The coordinator ranks on this.
- Prefer fewer, sharp findings over many vague ones. Don't restate items already open in
  `Backlog/` (read `Backlog/README.md` first) or already shipped in `Backlog/done/`.
