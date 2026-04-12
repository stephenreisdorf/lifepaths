# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lifepaths is a TTRPG life path character creation system (inspired by Traveller-style character generation). Characters progress through "terms" composed of "steps" that resolve via dice rolls or player choices and apply effects to a character sheet.

## Development Commands

```bash
# Backend — install deps and run the API (FastAPI on http://127.0.0.1:8000, reload enabled)
uv sync
uv run python main.py

# Run a specific module directly
uv run python -m src.terms.childhood

# Frontend (Vue 3 + Vite)
cd frontend
npm install
npm run dev           # dev server
npm run build         # production build into frontend/dist
```

No tests or linter are configured yet.

## Tech Stack

- **Python 3.12**, managed with `uv`
- **FastAPI** + **Pydantic v2**
- **PyYAML** for career data files
- **Vue 3 + Vite** frontend in `frontend/`

## Architecture

Three layers: **Domain** (`src/terms/`, `src/character.py`) → **Engine** (`src/engine.py`) → **API** (`src/api.py`). Career data is loaded from YAML (`data/careers/*.yaml`) by `src/career_loader.py`.

### Domain layer

- **`src/character.py`** — `Character` with `Characteristic`s (value + `modifier()` computed as `value // 3 - 2`, Traveller-style DM) and `Skill`s (with specialties). All Pydantic `BaseModel`s. Dicts keyed by name; methods `add_skill`, `increment_skill`, `has_skill`, `promote`, `record_career_term`.
- **`src/terms/base.py`** — `StepType` enum (`AUTOMATIC` / `CHOICE`), `StepPrompt` (self-describing step metadata for the frontend), `SubmitResult` (uniform API response). Abstract `Step` (`step_id`, `step_type`, `prompt()`, `resolve(player_input)`, `apply()`) and `Term` (sequences steps, owns the `resolve → apply → advance` lifecycle via `submit()`).
- **`src/terms/childhood.py`** — `RollCharacteristicsStep` (2d6 per stat), `ChooseBackgroundSkillsStep` (pick N based on EDU DM); `ChildhoodTerm`.
- **`src/terms/careers.py`** — The largest domain file. Contains the full career flow: `RollQualificationStep`, `BasicTrainingStep`, `ChooseAssignmentStep`, `ChooseCareerSkillsTable`, `RollForSkillStep`, `SurvivalCheckStep`, `EventsRollStep`, `MishapRollStep`, `AdvancementRollStep`, plus `ChooseCareerStep` / `ContinueOrMusterOutStep`. `CareerTerm.advance()` dynamically appends the next steps based on prior outcomes. `TransitionTerm` is a one-step term used for career selection and continue/muster choices.
- **`src/utilities.py`** — `roll(d)` rolls `d` six-sided dice and sums (uses global `random`).

### Engine layer

- **`src/engine.py`** — `GameSession` owns a character and current term. `start()` and `submit()` drive the lifecycle, auto-advancing through consecutive automatic steps. `_next_term()` decides the next term after one finishes, chaining Childhood → Career Selection → Career Term → Continue/Muster → repeat (or back to Career Selection on qualification failure or mishap).

### API layer

- **`src/api.py`** — Two generic endpoints (`POST /api/start`, `POST /api/submit`) that delegate entirely to `GameSession`. No knowledge of specific step types. Session IDs for multi-user support.

### Career data

- **`data/careers/<name>.yaml`** — one YAML per career (qualification, service skills, assignments, skill tables, events, mishaps, ranks).
- **`src/career_loader.py`** — `get_available_careers()`, `load_career(name)`, `career_to_term_kwargs(data, is_first_term)`. Normalizes gated skill tables (those with `{requirement, skills}` shape) to flat `dict[str, list[str]]` for `CareerTerm`.

## Key patterns

- **Self-describing steps**: every step declares its `step_type` and `prompt()` so the API and frontend handle any step generically. Adding a new term/step requires only new domain code — no API or frontend changes.
- **Uniform resolve interface**: all steps accept `resolve(player_input: dict | None = None)`. Automatic steps ignore input; interactive steps read `player_input["selections"]`.
- **Auto-advancement**: the engine resolves consecutive automatic steps silently, collecting their prompts in `SubmitResult.resolved_steps`.
- **Prompts are re-rendered post-resolve**: step `apply()` populates `self.outcome: StepOutcome | None` with a status tag and a human-readable description; `prompt()` reads `self.outcome.description` when present and otherwise renders a "before" description. The frontend displays both.
- **Pass/fail roll steps**: `RollQualificationStep`, `SurvivalCheckStep`, and `AdvancementRollStep` all inherit from `PassFailRollStep` in `src/terms/base.py`, which handles the 2d6 + DM vs target boilerplate. Subclasses declare `step_id`, `check_label`, `status_pass`, `status_fail`.
- **Term-owned routing**: each `Term` implements `next_term(session) -> Term | None`. The engine's transition logic is just `self.term.next_term(self)`. `CareerTerm` synthesizes its own terminal outcome (`FAILED_QUAL` / `MISHAP` / `COMPLETED`) at the end of its step machine so `next_term` can branch on status strings rather than `isinstance` checks.
- **Imports use `src.` prefix** (e.g., `from src.character import Character`).

## Known rough edges

- `utilities.roll()` uses the global `random` module directly, so step logic is untestable without monkeypatching or seeding.

## Backlog

Open issues live as one file per issue under `Backlog/`, indexed by `Backlog/README.md`. Check there for the current list of known bugs, missing mechanics, and architectural RFCs before adding new features or refactors.
