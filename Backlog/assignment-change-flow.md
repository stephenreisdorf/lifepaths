# Support changing assignments within a career

Per the rules, a Traveller may change assignment within the same career instead of starting a new career:

- **Army, Marine, Navy, Nobility, Rogue, Scholar, Scout:** qualification roll required. Fail → stay in previous assignment, no penalty. Succeed → new assignment, retain rank.
- **Agent, Citizen, Entertainer, Merchant:** treated as entering a new career. New benefit rolls, new qualification roll.
- Cannot change assignment if ejected from the career.
- On successful change, career begins afresh at rank 0 (contradicts "retain rank" above for the first group — reconcile with source).

The engine only offers `ChooseCareer` ↔ `ContinueOrMusterOut`; there is no intra-career assignment-change option.

## Scope

- Add an assignment-change branch to `ContinueOrMusterOutStep` (or a new choice step).
- Classify careers into the two groups in the YAML.
- For group 1: qualification roll, retain/reset rank per reconciled RAW.
- For group 2: route through normal benefit rolls + new qualification flow.
- Block assignment change when flagged as ejected (see `track-career-ejection.md`).
