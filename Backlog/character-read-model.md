# Move character serialization out of the engine into a read model

`GameSession._character_summary` hand-serializes the internals of `Character`, `Characteristic`, `Skill`, and `Associate`. That API-shaping responsibility living in the engine couples it to every domain model's structure — a new field silently fails to surface until the engine is also edited.

## Problem

`src/engine.py:27-55` reaches through `Character.characteristics` (`c.value`, `c.modifier()`), `Character.skills` (`s.base_rank`, `s.specialties`), `Character.associates`, `cash`, `possessions` to build the API payload. Serialization is mixed into the engine/session layer rather than living with the model or at the API boundary, and drifts silently when the domain model grows.

## Opportunity

- Move the summary into a read model: either a `Character.summary()` method (Information Expert — the model owns its own serialization) or a dedicated Pydantic read model constructed at the API/engine boundary.
- Have `GameSession.start()` / `submit()` delegate to it rather than inlining field access.

## Done when

- [ ] `GameSession` no longer reaches into `Characteristic` / `Skill` / `Associate` internals to build the response payload.
- [ ] Character-summary shape is defined in one place (a model method or read model), covered by a test asserting the serialized shape.
- [ ] `uv run pytest` passes and the `/api/start` + `/api/submit` payload shape is unchanged.

## Notes

Cohesion / layer-separation fix. Independent of the other items. If a Pydantic read model is chosen, it complements the clean-architecture "separate read models" guidance. Keep the `SubmitResult.character: dict` contract (`src/terms/base.py`) or tighten it deliberately.
