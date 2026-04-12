# Apply mechanical effects for mishaps

`MishapRollStep.apply()` (`src/terms/careers.py:229-231`) is explicitly a no-op; the code comment reads "Flavor-only for now; effects are not auto-applied." Mishaps should have mechanical effects (injury, enemy, gear loss, characteristic damage, etc.).

## Scope

- Extend the YAML mishap schema to describe effects (e.g. characteristic damage, skill grant, enemy/rival, forced career change).
- Implement an effect applier (possibly shared with events — see `events-effects.md`).
- Some mishaps are choice-based (e.g. "pick an enemy"); these will need a follow-up `StepType.CHOICE` step.
- Also covers "lose the Benefit roll for this term" once benefits are implemented.
