# Inject a CareerRepository instead of calling the loader from terms

The term layer reaches directly into the filesystem-backed `career_loader` module on every transition, re-reading and re-validating YAML each time. Introducing a `CareerRepository` abstraction on `CareerContext` decouples the domain layer, makes term transitions testable without touching disk, and gives a natural cache point.

## Problem

`src/terms/careers/terms.py` calls `load_career(name)` in three places (`_after_choose_career`, `_after_draft_or_drifter`, `_forced_entry_career_term`) and `get_available_careers()` via `_available_careers_for`. `get_available_careers()` (`src/career_loader.py:17`) globs `data/careers/*.yaml`, opens, parses, and re-validates **every** file on **every** career-selection prompt. Two consequences:

- **Efficiency**: repeated disk I/O + Pydantic validation per transition, redone from scratch each time.
- **Coupling / testability**: the domain layer depends on a concrete disk-backed module function, so terms cannot be exercised against an in-memory career set. This is the one place the repository/DI pattern used elsewhere is not applied.

## Scope

- Define a `CareerRepository` Protocol (e.g. `get_available() -> list[...]`, `load(name) -> CareerData`) — likely in a new module or alongside `career_loader.py`.
- Provide a default filesystem implementation wrapping the existing loader functions, caching parsed `CareerData`.
- Carry the repository on `CareerContext` (`src/terms/context.py`), constructed by `GameSession` (`src/engine.py`), and have `terms.py` consume it instead of importing `load_career` / `get_available_careers` directly.
- Provide an in-memory stub for tests.

## Done when

- [ ] `src/terms/careers/terms.py` no longer imports `load_career` / `get_available_careers`; it reads careers through a repository on `CareerContext`.
- [ ] A `CareerRepository` Protocol exists with a filesystem implementation and a test stub.
- [ ] A test exercises a career transition (e.g. career selection → first `CareerTerm`) using an in-memory repository, with no filesystem access.
- [ ] Career YAML for a given name is parsed/validated at most once per session (cached).
- [ ] `uv run pytest` passes.

## Notes

Highest-leverage architectural item of the review set. Naturally subsumes the loosely-typed career-summary dict cleanup ([typed-career-summary](typed-career-summary.md)) if the repository returns a typed summary. Update `CLAUDE.md` / `AGENTS.md` engine + career-data sections to describe the repository.
