# Step outcome protocol + term-owned routing

Two interlocking pieces of architectural friction in the step/term/engine layer:

1. **Implicit step state via `hasattr`.** Steps communicate their result by assigning ad-hoc attributes (`qualification_status`, `survival_status`, `selected_career`, `decision`, `mishap_text`, `advancement_status`, …). Callers probe with `hasattr`. Examples:
   - `src/engine.py:80` — `hasattr(qual_step, "qualification_status")`
   - `src/terms/careers.py:33` — `if hasattr(self, "qualification_status"):` inside `prompt()`
   - Repeated in `SurvivalCheckStep`, `AdvancementRollStep`, `MishapRollStep`, `EventsRollStep`, `RollForSkillStep`.
2. **Term-transition routing lives in the engine.** `GameSession._next_term` (`src/engine.py:48-103`) is a 55-line `isinstance` chain that peeks inside finished terms (`finished.steps[0]`, `any(isinstance(s, MishapRollStep) …)`). `CareerTerm.advance` (`src/terms/careers.py:484-530`) has its own `isinstance` chain for intra-term step sequencing. Routing decisions are split across both.

These are coupled: the engine's routing needs to know "what happened to the finished term", and the only way it can ask today is via `hasattr` / `isinstance` on the term's steps. Fixing the outcome protocol is what unlocks moving routing onto the term.

## Design

**`StepOutcome` model (new, in `src/terms/base.py`)**

```python
class StepOutcome(BaseModel):
    status: str = "done"           # "QUALIFIED" | "FAILED" | "SURVIVED" | "MISHAP" | "CONTINUE" | "MUSTER_OUT" | ...
    description: str = ""          # rendered into prompt post-resolve
    data: dict = Field(default_factory=dict)   # rolls, selections, career name, etc.
```

**Additions to `Step`:** `outcome: StepOutcome | None = None`. `resolve()` / `apply()` set it. `prompt()` reads `self.outcome.description` when present, eliminating the `hasattr` branches.

**Additions to `Term`:** `next_term(session) -> Term | None` (default returns `None`). Each term subclass owns its own transition logic. `_next_term` in the engine collapses to `return self.term.next_term(self)`. Session state (`current_career_data`, `career_term_count`) stays on `GameSession`; terms mutate it via the passed `session` handle — the one new coupling accepted to avoid inventing a separate router/context type.

**`PassFailRollStep` helper base class (new, in `src/terms/base.py`)**

The three pass/fail roll steps (`RollQualificationStep`, `SurvivalCheckStep`, `AdvancementRollStep`) share ~20 lines of near-identical boilerplate: roll 2d6 + characteristic DM, compare to target, set status string, render prompt two ways. Once outcomes are uniform, this is directly extractable. Subclasses declare `step_id`, `status_pass`, `status_fail`, and (where needed) override `apply()` for side-effects like promotion. `AdvancementRollStep` keeps a custom `apply()` for `character.promote()` / rank bonus.

## Scope

- Add `StepOutcome` to `src/terms/base.py`; add `Step.outcome` and `Term.next_term(session)`.
- Add `PassFailRollStep` base and migrate `RollQualificationStep`, `SurvivalCheckStep`, `AdvancementRollStep` to inherit from it.
- Migrate remaining steps (`ChooseCareerStep`, `ChooseAssignmentStep`, `ChooseCareerSkillsTable`, `RollForSkillStep`, `MishapRollStep`, `EventsRollStep`, `ContinueOrMusterOutStep`, `BasicTrainingStep`, and childhood steps) to set `self.outcome` instead of dynamic attrs.
- Compose the post-resolve description inside `apply()` (where the data is freshest) and let `prompt()` read `self.outcome.description`. Removes every `hasattr` branch inside `prompt()`.
- Implement `next_term(session)` on `ChildhoodTerm`, `TransitionTerm`, `CareerTerm`. Delete the `isinstance` chain in `GameSession._next_term`.
- Keep `CareerTerm.advance`'s branching (it is genuinely a small state machine) but key it on `step.outcome.status` instead of ad-hoc attrs.
- When the last step of a `CareerTerm` resolves, synthesize a terminal outcome on the term itself (`"FAILED_QUAL"` / `"MISHAP"` / `"COMPLETED"`) so `CareerTerm.next_term` can branch cleanly.
- `TransitionTerm.label()` reads `self.steps[0].outcome.data` instead of `isinstance`-ing the inner step.

## Non-goals

- Not introducing a typed-outcome discriminated union, registry, or state-machine DSL. Status strings already are the convention; promote them, don't replace them. Revisit if 3+ career types with divergent graphs or a serializable save/load mid-creation become requirements.
- Not centralizing `Character` mutations via returned `Effect` objects — orthogonal, larger surface, soft payoff. Separate issue if pursued.
- Not injecting a `Dice` dependency for randomness — orthogonal testability concern, tracked separately.

## Expected diff shape

- `src/engine.py`: `_next_term` drops from ~55 lines to 1; imports of concrete term/step classes shrink.
- `src/terms/careers.py`: three roll step classes each shrink from ~40 lines to ~5 (just class-level constants). `hasattr` branches in every `prompt()` removed.
- `src/terms/base.py`: +`StepOutcome` model, +2 attributes on `Step`/`Term`, +`PassFailRollStep` base class (~40 lines).
- No changes required to `src/api.py` or the frontend — `StepPrompt` / `SubmitResult` contract is preserved.
