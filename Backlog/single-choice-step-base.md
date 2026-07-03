# Extract a SingleChoiceStep base to dedup choice-step resolve boilerplate

Every `CHOICE` step repeats the same `resolve()` body: null-check input, read `selections`, assert exactly one, validate membership, stash a pending value. A `SingleChoiceStep` Template-Method base removes that duplication across ~8 step classes, mirroring how `PassFailRollStep` already factors the roll steps.

## Problem

The following steps in `src/terms/careers/steps.py` each hand-roll a near-identical `resolve()`: `PickServiceSkillStep`, `ChooseAssignmentStep`, `ChooseCareerSkillsTable`, `CommissionStep`, `ContinueOrMusterOutStep`, `MusterOutOrNewCareerStep`, `ChooseDraftOrDrifterStep`, `ChooseAnagathicsStep` (and `ChooseCareerStep`). Each: raises if `player_input is None`, reads `player_input.get("selections", [])`, raises unless `len == 1`, validates the choice against an options list, and stores a `_..._pending`. This is ~8x duplicated validation with subtly different error strings.

## Opportunity

- Add a `SingleChoiceStep(Step)` base in `src/terms/base.py` (the home of the analogous `PassFailRollStep`), declaring `step_type = CHOICE`, an `options() -> list[str]` hook and an `on_choice(selection)` hook, and owning the shared null/length/membership validation in `resolve()`.
- Migrate the choice steps to subclass it, keeping their specific prompt text and `apply()` behavior.

## Done when

- [ ] `SingleChoiceStep` exists in `src/terms/base.py` and owns the input/length/membership validation.
- [ ] The listed choice steps subclass it and no longer duplicate that `resolve()` boilerplate.
- [ ] Existing choice-step behavior (including specific `ValueError`s for bad input) is preserved or intentionally unified.
- [ ] `uv run pytest` passes.

## Notes

Low-risk, on-pattern win: directly parallels the existing `PassFailRollStep` Template Method. Good companion to [career-term-next-term-dispatch](career-term-next-term-dispatch.md) as a "consistency" pass. Note `PassFailRollStep` subclasses are AUTOMATIC roll steps, so this base is a sibling, not a shared parent.
