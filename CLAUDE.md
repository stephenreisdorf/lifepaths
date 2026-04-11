# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lifepaths is a TTRPG life path character creation system (inspired by Traveller-style character generation). Characters progress through "terms" composed of "steps" that resolve via dice rolls or player choices and apply effects to a character sheet.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the entry point
uv run python main.py

# Run a specific module
uv run python -m src.terms.childhood
```

## Tech Stack

- **Python 3.12**, managed with `uv`
- **FastAPI** web framework with **Pydantic v2** for data models
- **Vue 3 + Vite** frontend in `frontend/`
- No tests or linter configured yet

## Architecture

Three layers: **Domain** (terms/steps/character) → **Engine** (game session orchestration) → **API** (thin HTTP).

### Domain layer

- **`src/character.py`** — `Character` model with `Characteristic`s (stat + modifier) and `Skill`s (with specialties). All Pydantic `BaseModel`s.
- **`src/terms/base.py`** — `StepType` enum (`AUTOMATIC`/`CHOICE`), `StepPrompt` model (self-describing step metadata), `SubmitResult` model (uniform response). Abstract `Step` (with `step_id`, `step_type`, `prompt()`, uniform `resolve(player_input)`, `apply()`) and `Term` (sequences steps, owns resolve/apply/advance lifecycle via `submit()`).
- **`src/terms/childhood.py`** — `RollCharacteristicsStep` (automatic, rolls 2d6 per stat), `ChooseBackgroundSkillsStep` (choice, pick N skills based on EDU DM). `ChildhoodTerm` sequences these.
- **`src/utilities.py`** — `roll(d)` helper that rolls `d` six-sided dice and sums.

### Engine layer

- **`src/engine.py`** — `GameSession` owns a character and current term. `start()` and `submit()` drive the step lifecycle, auto-advancing through automatic steps, and return uniform `SubmitResult` responses.

### API layer

- **`src/api.py`** — Two generic endpoints (`POST /api/start`, `POST /api/submit`) that delegate entirely to `GameSession`. No knowledge of specific step types. Session IDs for multi-user support.

### Key patterns

- **Self-describing steps**: Each step declares its `step_type` and `prompt()` so the API and frontend can handle any step generically without type-specific logic.
- **Uniform resolve interface**: All steps accept `resolve(player_input: dict | None = None)`. Automatic steps ignore input; interactive steps read from it.
- **Auto-advancement**: The engine automatically resolves consecutive automatic steps, collecting their results in `resolved_steps`.
- **Adding new terms/steps** requires only new domain code — no API or frontend changes.
- Character uses dicts keyed by name for both characteristics and skills, with methods like `add_skill`, `increment_skill`, `has_skill`.
- `Characteristic.modifier()` computes `value // 3 - 2` (Traveller-style DM).
- Imports use `src.` prefix (e.g., `from src.character import Character`).
