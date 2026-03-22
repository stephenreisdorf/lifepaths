# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Backend**: FastAPI (Python 3.12), managed with `uv`
- **Frontend**: Vue 3 + Vite, managed with `npm`

## Commands

### Backend (run from `backend/`)

```bash
uv run uvicorn main:app --reload   # Start dev server at http://localhost:8000
```

### Frontend (run from `frontend/`)

```bash
npm run dev       # Start dev server at http://localhost:5173
npm run build     # Production build to dist/
```

No test framework is configured yet.

## Architecture

Monorepo with independent backend and frontend. Both must run simultaneously during development.

### Backend

Event-sourced TTRPG life path character creation engine.

**Module layout:**
```
backend/
  main.py              # FastAPI app; loads all configs at startup via lifespan
  models/
    shared.py          # AttributeModifier, Feature
    content.py         # LifePathConfig, StageDefinition, EventDefinition, OutcomeDefinition, EventType
    session.py         # Log entry union types, SessionState, CharacterSession.derive_state()
    character.py       # CharacterSheet, StageHistorySummary
    dice.py            # DiceExpression — parses and validates roll results
    api.py             # Thin request/response schemas
  content/
    loader.py          # load_all_configs(), get_config(), all_configs()
    stages/            # YAML/JSON lifepath config files (loaded at startup)
  routers/
    sessions.py        # All session endpoints + game engine helpers
    content.py         # GET /api/content/lifepaths[/{id}]
    characters.py      # Placeholder (no endpoints yet)
```

**Key design patterns:**

- `log` is append-only. All state is derived by replaying it: `CharacterSession.derive_state(stages=...)`.
- `EventResolvedEntry` snapshots resolved effects (attribute_modifiers, features_granted, context_updates, injected_event_ids) so the log is self-contained.
- `StageCompletedEntry` is auto-appended by the server after a non-repeatable stage finishes all events.
- `_try_auto_advance()` in `routers/sessions.py` loops to resolve `automatic` events and cascade `StageCompletedEntry` additions until player input is required.
- Repeatable stages: after all events complete, the player is prompted (via `RepeatPrompt`) to repeat or advance. Explicit `POST /api/sessions/{id}/advance` with `repeat_stage: bool` is required.
- Roll validation is server-authoritative via `DiceExpression.validate_roll()`.
- Sessions are stored in an in-memory dict in `routers/sessions.py` (replace with DB later).
- `LifePathConfig` has a model validator that checks all cross-references (stage IDs, event IDs, prerequisite references) at load time.
- `derive_state()` separates base attributes (from `LifePathConfig.base_attributes`) from skills (attributes not in that set).
- The context system: `EventResolvedEntry.context_updates` merges into `SessionState.resolved_context`. `OutcomeDefinition.requires_context` gates which outcomes are visible/selectable.

**API routes:**
- `POST /api/sessions` — create session
- `GET /api/sessions/{id}` — get current state
- `POST /api/sessions/{id}/events/{event_id}/roll` — resolve table_roll event
- `POST /api/sessions/{id}/events/{event_id}/choose` — resolve choice event
- `POST /api/sessions/{id}/events/{event_id}/skip` — skip optional event
- `POST /api/sessions/{id}/advance` — advance or repeat a repeatable stage
- `GET /api/content/lifepaths` — list all configs
- `GET /api/content/lifepaths/{id}` — get single config

### Frontend

Screen-based state machine in `App.vue` with no router or global state library.

**Screens:** `landing` → `session` → `complete`

**Component hierarchy:**
```
App.vue                        # Screen state, API calls, event wiring
  LandingScreen.vue            # Lifepath selector + name inputs
  SessionScreen.vue            # Stage/event progression + sidebar
    StageHeader.vue
    EventPanel.vue             # Dispatches to event type component
      TableRollEvent.vue       # Dice roll UI with outcomes preview table
      ChoiceEvent.vue          # Multi-select cards, filtered by resolved_context
      AutomaticEvent.vue       # Single "Continue" button
    StatsSidebar.vue           # Live attributes, skills, features, age
    OutcomePanel.vue           # Modal showing outcome effects after resolution
    RepeatPrompt.vue           # Repeat/advance UI for repeatable stages
  CompleteScreen.vue           # Final character sheet
    AttributeGrid.vue
    FeatureList.vue
    StageHistoryList.vue
```

**Key points:**
- `App.vue` owns all API calls and passes data down as props; child components emit events upward.
- `api/client.js` uses `fetch` (not axios, despite axios being in package.json).
- `handleResolutionResponse()` in `App.vue` handles the unified `EventResolutionResponse` — updates state, triggers outcome modal, or transitions to complete screen.
- `ChoiceEvent.vue` filters outcomes client-side by `requires_context` before displaying cards.
- `OutcomePanel.vue` shows a "View Character Sheet" button instead of "Continue" when `sessionComplete` is true.

### Lifepath Config Authoring

Configs are YAML or JSON files placed in `backend/content/stages/`. See `docs/lifepath-config.md` for the complete authoring reference including all fields, dice expression syntax, context system, outcome triggers, and a full annotated example.

**Dice expressions:** `[N]d<sides>[+/-bonus]` — e.g., `2d6`, `1d20+3`, `d8-2`

**Event types:** `table_roll` (range-based outcomes), `choice` (player picks), `automatic` (no input, first outcome auto-selected)

## Environment Variables

Add backend secrets to `backend/.env`. The file is gitignored and loaded automatically at startup.
