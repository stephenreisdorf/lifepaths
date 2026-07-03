# Hoist in-function career_loader imports to module scope

Seven `from src.career_loader import ...` statements sit inside function bodies. No import cycle through `career_loader`/`career_data` justifies them, so they can move to module scope for clarity — pending a check of the package `__init__` re-exports.

## Problem

- Deferred imports appear in `src/terms/careers/terms.py:39,52,95,117`, `src/terms/education/terms.py:37,164`, and `src/terms/childhood.py:140`.
- Neither `src/career_loader.py` nor `src/career_data.py` imports anything under `src/terms/`, so there is no cycle through those modules — the in-function placement reads as a leftover guard, not a necessity.
- Function-local imports obscure a module's real dependencies and re-run the import machinery on every call.

## Scope

Move the `career_loader` imports to the top of each of the three files. Touches only `src/terms/careers/terms.py`, `src/terms/education/terms.py`, `src/terms/childhood.py`.

## Done when

- [ ] The three files import `career_loader` at module scope; no `from src.career_loader import` remains inside a function body.
- [ ] `uv run pytest` passes and `uv run python main.py` imports cleanly.
- [ ] `grep -rn "from src.career_loader import" src/terms/` shows only module-level (top-of-file) hits.

## Notes

**Verify before bulk-editing:** `src/terms/careers/__init__.py` re-exports the full package surface. Hoist one file first, run `uv run pytest`, and confirm no cycle surfaces through the package `__init__` re-exports before converting the other two. Lowest-risk / lowest-leverage of the five; do it opportunistically alongside other work in these files.
