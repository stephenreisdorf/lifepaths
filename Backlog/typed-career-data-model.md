# Refactor: Typed Career Data Model (YAML → Domain Pipeline)

The career data pipeline passes raw dicts from YAML through `career_loader.py` and splats 13+ kwargs into `CareerTerm.__init__()`. No validated intermediate type exists — schema mismatches surface as runtime errors deep in the career flow rather than at load time.

## Problem

- `career_to_term_kwargs()` returns a flat dict that is splatted into `CareerTerm.__init__()`. A YAML schema change requires updating the loader, then the Term constructor, then any code reading those fields.
- There is no way to validate career data at load time. A typo in a YAML key or a missing field won't surface until that code path is hit during gameplay.
- Testing the loader and the Term constructor independently is difficult because the contract between them is implicit.

## Opportunity

Introduce a Pydantic `CareerData` model (or similar typed intermediate) between the loader and the Term:

- The loader validates YAML against the model at load time, catching schema errors early.
- `CareerTerm.__init__()` accepts a `CareerData` instance instead of kwargs, making the interface explicit.
- The model serves as living documentation of the YAML schema.
- Loader and Term can be tested independently against the typed contract.

## Scope

- `src/career_loader.py`: `load_career()`, `career_to_term_kwargs()`
- `src/terms/careers.py`: `CareerTerm.__init__()`
- `data/careers/*.yaml` (schema reference, no changes needed)
