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

Run the test suite with `uv run pytest`. No linter is configured yet.

### Process cleanup

When restarting dev servers, verify the port is actually free before starting a new one — leftover processes from prior sessions commonly linger:

- Backend (FastAPI): `lsof -i :8000`
- Frontend (Vite): `lsof -i :5173`

## Tech Stack

- **Python 3.12**, managed with `uv`
- **FastAPI** + **Pydantic v2**
- **PyYAML** for career data files
- **Vue 3 + Vite** frontend in `frontend/`

## Architecture

Three layers: **Domain** (`src/terms/`, `src/character.py`) → **Engine** (`src/engine.py`) → **API** (`src/api.py`). Career data is loaded from YAML (`data/careers/*.yaml`) by `src/career_loader.py`.

### Domain layer

- **`src/character.py`** — `Character` with `Characteristic`s (value + `modifier()` computed as `value // 3 - 2`, Traveller-style DM), `Skill`s (with specialties), `Associate`s (`AssociateType`: contact/ally/rival/enemy), `CareerRecord`s, plus `cash`, `possessions`, `age`, and `pending_career_entry` (forced next-term career). All Pydantic `BaseModel`s; dicts keyed by name. Skill methods: `add_skill`, `increment_skill`, `has_skill`, and the higher-level `grant_skill(name, level, specialty)` used by effects. Other state: `add_characteristic`, `add_associate`, `ensure_career`, `promote`, `record_career_term`, `mark_career_ejected`. Skill growth is capped by a budget (`total_skill_levels` vs `total_skill_level_cap`, enforced in `_budget_allows_increment`).
- **`src/terms/base.py`** — `StepType` enum (`AUTOMATIC` / `CHOICE`), `StepPrompt` (self-describing step metadata for the frontend), `SubmitResult` (uniform API response). Abstract `Step` (`step_id`, `step_type`, `prompt()`, `resolve(player_input)`, `apply()`) and `Term` (sequences steps, owns the `resolve → apply → advance` lifecycle via `submit()`).
- **`src/terms/childhood.py`** — `RollCharacteristicsStep` (2d6 per stat), `ChooseBackgroundSkillsStep` (pick N based on EDU DM); `ChildhoodTerm`.
- **`src/terms/careers.py`** — The largest domain file (~2000 lines). Contains the full career flow: `RollQualificationStep` / `AutoQualifyStep`, `BasicTrainingStep`, `PickServiceSkillStep`, `ChooseAssignmentStep`, `ChooseCareerSkillsTable`, `RollForSkillStep`, `SurvivalCheckStep`, `EventsRollStep`, `MishapRollStep`, `AdvancementRollStep`, `CommissionStep`, plus the transition/branching steps `ChooseCareerStep`, `ContinueOrMusterOutStep`, `MusterOutOrNewCareerStep`, and `ChooseDraftOrDrifterStep` (failed-qualification fallback: Draft once-per-life or Drifter). `MusterOutStep` / `AgingStep` live in `MusterOutTerm`. `CareerTerm.advance()` dynamically appends the next steps based on prior outcomes and synthesizes a terminal status (`FAILED_QUAL` / `MISHAP` / `EVENT` / `FORCED_EXIT` / `COMPLETED`). `TransitionTerm` is a one-step term used for career selection and continue/muster choices; `AssignmentChangeTerm` handles mid-career assignment switches.
- **`src/terms/effects.py`** — structured effects for events/mishaps. A YAML events/mishaps entry is either flavor text or `{text, effects}`. `parse_entry` splits it; `apply_effects(character, effects)` applies each typed effect (`skill`, `characteristic`, `associate`, `forced_exit`, `enter_career`, plus flavor-only `advancement_dm` / `benefit_dm`) and returns human-readable descriptions. `enter_career` sets `character.pending_career_entry`; `forced_exit` is surfaced so `CareerTerm` ends with `FORCED_EXIT`.
- **`src/utilities.py`** — `roll(d)` rolls `d` six-sided dice and sums, using a module-level `random.Random` instance (`rng`) that tests seed via `rng.seed(...)` for deterministic dice.

### Engine layer

- **`src/engine.py`** — `GameSession` owns a character and current term plus cross-term state (`current_career_data`, `career_term_count`, `blocked_career`, `current_assignment`, `draft_used`). `start()` and `submit()` drive the lifecycle. **Every step — automatic or choice — requires an explicit `submit()`** so the frontend can show each step's pre-resolve prompt and post-resolve outcome (resolved automatic steps return their post-resolve prompt in `SubmitResult.resolved_steps`). Only *term boundaries* are crossed automatically: `_advance_past_term_boundaries()` repeatedly calls the current term's `next_term(self)` until a step is available, chaining Childhood → Career Selection → Career Term → Continue/Muster → repeat (or to the Draft/Drifter fallback on qualification failure).

### API layer

- **`src/api.py`** — Two generic endpoints (`POST /api/start`, `POST /api/submit`) that delegate entirely to `GameSession`. No knowledge of specific step types. Session IDs for multi-user support.

### Career data

- **`data/careers/<name>.yaml`** — one YAML per career (qualification, service skills, assignments, skill tables, events, mishaps, ranks).
- **`src/career_data.py`** — `CareerData`, the Pydantic model that validates a career YAML at load time (`extra="forbid"` catches key typos) and serves as living documentation of the schema. Normalizes the two qualification shapes (`{characteristic, target}` and `{options: [...]}`) and the two skill-table shapes (flat list vs `{requirement, skills}`). Exposes plain-dict views (`assignments_as_dicts()`, `ranks_as_dicts()`, `normalized_skill_tables()`, `skill_table_requirements()`, `qualification_summary()`, …) consumed by the domain layer.
- **`src/career_loader.py`** — `get_available_careers()` (returns lightweight `qualification_summary()` dicts), `load_career(name)` (returns a validated `CareerData`), `filter_eligible_careers()`. `CareerTerm.__init__(character, career: CareerData, *, is_first_term, term_number, assignment_override, force_auto_qualify)` takes the typed model directly — no kwargs splat.

## Key patterns

- **Self-describing steps**: every step declares its `step_type` and `prompt()` so the API and frontend handle any step generically. Adding a new term/step requires only new domain code — no API or frontend changes.
- **Uniform resolve interface**: all steps accept `resolve(player_input: dict | None = None)`. Automatic steps ignore input; interactive steps read `player_input["selections"]`.
- **Explicit submit per step, auto-advance across terms**: every step (automatic *or* choice) needs its own `submit()` so each outcome is visible; the engine never silently chains steps. It *does* silently cross exhausted term boundaries. A just-resolved automatic step's post-resolve prompt rides back in `SubmitResult.resolved_steps`.
- **Prompts are re-rendered post-resolve**: step `apply()` populates `self.outcome: StepOutcome | None` with a status tag and a human-readable description; `prompt()` reads `self.outcome.description` when present and otherwise renders a "before" description. The frontend displays both.
- **Pass/fail roll steps**: `RollQualificationStep`, `SurvivalCheckStep`, and `AdvancementRollStep` all inherit from `PassFailRollStep` in `src/terms/base.py`, which handles the 2d6 + DM vs target boilerplate. Subclasses declare `step_id`, `check_label`, `status_pass`, `status_fail`.
- **Term-owned routing**: each `Term` implements `next_term(session) -> Term | None`. The engine's transition logic is just `self.term.next_term(self)`. `CareerTerm` synthesizes its own terminal outcome (`FAILED_QUAL` / `MISHAP` / `EVENT` / `FORCED_EXIT` / `COMPLETED`) at the end of its step machine so `next_term` can branch on status strings rather than `isinstance` checks.
- **Imports use `src.` prefix** (e.g., `from src.character import Character`).

## Agent guidance files

`AGENTS.md` (for Codex) is a near-duplicate of this file. Keep the two in sync when editing architectural notes.

## Backlog

Open issues live as one file per issue under `Backlog/`, indexed by `Backlog/README.md`. Check there for the current list of known bugs, missing mechanics, and architectural RFCs before adding new features or refactors.
