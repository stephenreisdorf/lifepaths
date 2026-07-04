<!--
Candidate-finding block. Focus audits append one of these per finding to their
`--candidates <output-file>` in coordinated mode. The `audit` coordinator parses these
to dedupe + rank, so keep the field names and order exactly as below. One `---` rule
separates consecutive findings.
-->

### <Title — a full descriptive sentence, becomes the backlog item's `# Title`>

- **Focus:** <rules | architecture | ux | tests | perf>
- **Category:** <Bugs | Fidelity | UX | Architecture | Performance | Deferred>
- **Severity:** <high | medium | low>
- **Slug:** <lowercase-kebab-case-suggested-filename, no `.md`>
- **Files:** `path:line`, `path:line-range`, `bare/path.py` (comma-separated; the sharper the refs, the better the dedupe)

**Problem:** <what's wrong or missing today; cite the `Files` refs inline.>

**Opportunity / Scope:** <the change and the modules it touches. Use "Opportunity" for refactor/UX/perf, "Scope" for fidelity/feature work — match the home category's convention.>

**Done when:**
- [ ] <checkable acceptance criterion — a specific test, observable behavior, or structural condition>
- [ ] <backend items end with: uv run pytest passes.>

**Notes:** <dependencies, ordering vs other items, links like [other](other.md), and for fidelity findings the RAW-vs-code numbers in **bold**.>

---
