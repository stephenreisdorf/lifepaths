# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lifepaths is a TTRPG life path character creation system (inspired by Traveller-style character generation). Characters progress through "terms" composed of "steps" that resolve via dice rolls or player choices and apply effects to a character sheet.

## Rules source of truth

The rules being implemented are **Mongoose Traveller 2022 Core Rulebook**. The repo does not check in the PDF (copyright). The rulebook is available in the **"Bowman Arm" NotebookLM notebook** — query it (via the `notebooklm` skill) to transcribe exact tables/mechanics when working a fidelity item. Backlog fidelity items that cite "Core Rulebook.pdf" or a "NotebookLM audit" refer to this source.

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

Three layers: **Domain** (`src/terms/`, `src/character.py`) → **Engine** (`src/engine.py`, `src/connections.py`) → **API** (`src/api.py`). Career data is loaded from YAML (`data/careers/*.yaml`) by `src/career_loader.py`.

### Domain layer

- **`src/character.py`** — `Character` with `Characteristic`s (value + `modifier()` computed as `value // 3 - 2`, Traveller-style DM), `Skill`s (with specialties), `Associate`s (`AssociateType`: contact/ally/rival/enemy), `CareerRecord`s, plus `cash`, `possessions`, `age`, `pending_career_entry` (forced next-term career), and `anagathics` (an optional `AnagathicsCourse` of anti-aging drugs). All Pydantic `BaseModel`s; dicts keyed by name. Skill methods: `has_skill` (query), `grant_skill(name, level, specialty)` (the general skill-mutation primitive), and `grant_connection_skill(name)` (the Connections Rule wrapper that excludes Jack-of-all-Trades and caps the result at level 3); `_ensure_skill` is a private helper. Other state: `add_characteristic`, `add_associate`, `ensure_career`, `promote`, `record_career_term`, `mark_career_ejected`, plus the anagathics mutators (`start_anagathics_course`, `maintain_anagathics_course`, `stop_anagathics_course`, `anagathics_aging_dm`). Skill growth is capped by a budget (`total_skill_levels` vs `total_skill_level_cap`, enforced in `_budget_allows_increment`).
- **`src/terms/base.py`** — `StepType` enum (`AUTOMATIC` / `CHOICE`), `StepStatus` enum (the machine-readable outcome tag on `StepOutcome.status`; a `str, Enum` so it serializes to its string value unchanged while an unknown status fails loudly at construction), `StepPrompt` (self-describing step metadata for the frontend), `SubmitResult` (uniform API response). Abstract `Step` (`step_id`, `step_type`, `prompt()`, `resolve(player_input)`, `apply()`) and `Term` (sequences steps, owns the `resolve → apply → advance` lifecycle via `submit()`), plus `DispatchTerm(Term)` — a Template-Method base whose single `advance()` dispatches each resolved step through a subclass-declared `_STEP_HANDLERS` table (shared by `CareerTerm`, `AssignmentChangeTerm`, and both education terms).
- **`src/terms/childhood.py`** — `RollCharacteristicsStep` (2d6 per stat), `ChooseBackgroundSkillsStep` (pick N based on EDU DM); `ChildhoodTerm`. Its `next_term()` routes into the pre-career education phase when the character is eligible for any institution, otherwise straight to Career Selection.
- **`src/terms/education/`** — The optional pre-career education phase between Childhood and Career Selection, a package that re-exports its surface (`from src.terms.education import <name>`):
  - **`config.py`** — `UNIVERSITY` / `MILITARY_ACADEMIES` institution data (eligibility, qualification, graduation targets) plus `eligible_options()` and `academy_by_career()`. Academies map onto a commissioned service career (army/marine).
  - **`steps.py`** — `ChoosePreCareerStep` (University / academy / skip), `EducationQualificationStep` (a `PassFailRollStep` entry roll), `ChooseUniversitySkillsStep` (major at level 1 / minor at level 0), and the graduation steps `UniversityGraduationStep` (bumps major/minor + EDU, sets a graduate qualification DM) and `AcademyGraduationStep`.
  - **`terms.py`** — `PreCareerChoiceTerm` (dispatches the choice to University / academy / career selection), `UniversityTerm`, and `MilitaryAcademyTerm` (graduating enters the service commissioned at officer rank 1 and auto-qualified; merely attending enters enlisted). Both education terms subclass `DispatchTerm`, declaring only a step-keyed `_STEP_HANDLERS` table (the same mechanism as `CareerTerm` / `AssignmentChangeTerm`).
- **`src/terms/careers/`** — The career flow, split into focused sub-modules under a package whose `__init__.py` re-exports the full public surface (so `from src.terms.careers import <name>` still works):
  - **`parsers.py`** — `parse_skill_entry()`, `try_apply_characteristic_bonus()` (skill-entry / characteristic-bonus text parsers), and `apply_rank_bonus(character, ranks, rank)` — the single helper that grants a typed `Rank` model's `bonus_skill` (skill at level 0, or a `<Char> +N` bump), shared by career entry (rank 0, applied in `CareerTerm._after_qualification`), promotions (`AdvancementRollStep`), commission (`CommissionStep`), and academy graduation. A career's `rank: 0` bonus_skill is granted the moment the career is entered (Army → Gun Combat, Marine → Gun Combat, Prisoner → Melee (unarmed)). `Rank.bonus_skill` is a single string, so the two RAW *choice* cases are simplified with a documented fallback (Marine rank-0 "Gun Combat (any)/Melee (blade)" → fixed Gun Combat; "SOC 10 or +1" top officer ranks → Social Standing +1); see `career_data.py`.
  - **`steps.py`** — the interactive/automatic Step subclasses: `RollQualificationStep` / `AutoQualifyStep`, `BasicTrainingStep`, `PickServiceSkillStep`, `ChooseAssignmentStep`, `ChooseCareerSkillsTable`, `RollForSkillStep`, `SurvivalCheckStep`, `EventsRollStep`, `MishapRollStep`, `AdvancementRollStep`, `CommissionStep`, the anagathics start-of-term steps `ChooseAnagathicsStep` / `AnagathicsUpkeepStep`, plus the transition/branching steps `ChooseCareerStep`, `ContinueOrMusterOutStep`, `MusterOutOrNewCareerStep`, and `ChooseDraftOrDrifterStep` (failed-qualification fallback: Draft once-per-life or Drifter).
  - **`aging.py`** — the official MgT 2022 `AGING_TABLE` (graded result rows) and `AgingStep`: a single 2D roll with a DM of −(total terms served) plus any positive DM from an active anagathics course (`character.anagathics_aging_dm()`), reductions applied to the physical characteristics (and Intelligence on the worst row).
  - **`muster_out.py`** — `MusterOutStep`, `MusterOutTerm`, and the `_muster_out_term_for()` benefit-roll wiring.
  - **`terms.py`** — `CareerTerm`, `TransitionTerm`, `AssignmentChangeTerm`. `CareerTerm` (like `AssignmentChangeTerm` and the education terms) subclasses `DispatchTerm`, whose `advance()` dispatches the just-resolved step through the term's declarative table (`_STEP_HANDLERS`: step type → a small `_after_<step>` handler) that appends the next step(s) or synthesizes a terminal status (`FAILED_QUAL` / `MISHAP` / `EVENT` / `FORCED_EXIT` / `COMPLETED`); adding a step type means adding a handler + one table row, not editing a central chain, and each handler is testable in isolation (see `tests/test_career_transitions.py`). `TransitionTerm` is a one-step term used for career selection and continue/muster choices; its `next_term()` uses the same pattern (`_NEXT_TERM_HANDLERS`: inner step id → handler). `AssignmentChangeTerm` handles mid-career assignment switches.
- **`src/terms/effects.py`** — structured effects for events/mishaps. A YAML events/mishaps entry is either flavor text or `{text, effects}`. `parse_entry` splits it; `apply_effects(character, effects)` applies each typed effect (`skill`, `characteristic`, `associate`, `forced_exit`, `enter_career`, `life_event`, `injury`, `betrayal`, plus flavor-only `advancement_dm` / `benefit_dm`) and returns human-readable descriptions. `enter_career` sets `character.pending_career_entry`; `forced_exit` is surfaced so `CareerTerm` ends with `FORCED_EXIT`. Characteristic reductions floor at 0. `life_event` / `injury` roll on the shared sub-tables in **`src/terms/life_events.py`** (the transcribed MgT 2022 Life Events 2D and Injury 1D tables) and apply the rolled row's own effects recursively; `injury` accepts `{rolls, take}` for the "roll twice, take the lower/higher result" entries.
- **`src/terms/anagathics.py`** — the optional anti-aging drugs rule (MgT 2022, Ageing). `attempt_start_anagathics(character)` performs the start-of-term SOC 10+ entry roll: a natural 2 routes the Traveller to the Prisoner career (no course started), otherwise 2D + SOC DM ≥ 10 starts a course and charges its 1D×Cr25000 cost (may drive `cash` into debt); `maintain_anagathics(character)` (via `roll_anagathics_cost`) charges each continuing term. The persistent `AnagathicsCourse` state and its positive Ageing DM live on `Character` (see the anagathics mutators). Dice live here, not on the pure `Character`. The rule is **wired into `CareerTerm`** as an opt-in (`CareerContext.anagathics_enabled`, set via `GameSession(anagathics_enabled=…)` / the `/api/start` body; off by default so baseline flows are unchanged): each career term opens with `ChooseAnagathicsStep` (the SOC 10+ offer — natural 2 → terminal `ANAGATHICS_PRISONER`, routed to the Prisoner career via `pending_career_entry`) or `AnagathicsUpkeepStep` (per-term upkeep charge on an active course), and while a course is active the Survival check is doubled (fail either → Mishap). Suppressed in the Prisoner career ("no anagathics in prison").
- **`src/utilities.py`** — `roll(d)` rolls `d` six-sided dice and sums, using a module-level `random.Random` instance (`rng`) that tests seed via `rng.seed(...)` for deterministic dice.

### Engine layer

- **`src/engine.py`** — `GameSession` owns a character and current term plus a typed `CareerContext` (`src/terms/context.py`) holding the cross-term state (`character`, `current_career_data`, `career_term_count`, `blocked_career`, `current_assignment`, `draft_used`, `pre_career_qualification_dm`, and `careers` — the injected `CareerRepository` terms read the catalogue through). The context is passed explicitly to each term's `next_term`; terms consume and mutate it rather than reaching into the session, which makes term transitions testable without a `GameSession`. `start()` and `submit()` drive the lifecycle. **Every step — automatic or choice — requires an explicit `submit()`** so the frontend can show each step's pre-resolve prompt and post-resolve outcome (resolved automatic steps return their post-resolve prompt in `SubmitResult.resolved_steps`). Only *term boundaries* are crossed automatically: `_advance_past_term_boundaries()` repeatedly calls the current term's `next_term(self.context)` until a step is available, chaining Childhood → (optional Pre-Career Education) → Career Selection → Career Term → Continue/Muster → repeat (or to the Draft/Drifter fallback on qualification failure). A university graduate's one-shot entry DM rides on `pre_career_qualification_dm` and is consumed by the first Career Selection. The API-facing character payload is built by the `CharacterSummary` read model (`src/character_summary.py`), not hand-serialized in the engine: `_character_summary()` just calls `CharacterSummary.from_character(self.character).model_dump()`, so the serialized shape is defined in one place and the engine no longer reaches into `Characteristic` / `Skill` / `Associate` internals.

- **`src/connections.py`** — `PartySession` composes two or more independent `GameSession`s without adding party state to career terms. It captures each member's resolved `events_roll` outcomes, exposes them as `ConnectionEvent`s, and owns the mutual proposal → acceptance transaction. An accepted connection grants both Travellers one validated skill, enforces the two-distinct-partner limit, and records the chosen Contact/Ally/Rival relationship on both characters. Proposals validate fully before either character mutates.

### API layer

- **`src/api.py`** — The single-character endpoints (`POST /api/start`, `POST /api/submit`) delegate entirely to `GameSession`. Party endpoints create/advance a `PartySession` and expose the Connections proposal/acceptance handshake. Both stores use opaque in-memory session IDs; the API has no career-step-specific routing.

### Career data

- **`data/careers/<name>.yaml`** — one YAML per career (qualification, service skills, assignments, skill tables, events, mishaps, ranks).
- **`src/career_data.py`** — `CareerData`, the Pydantic model that validates a career YAML at load time (`extra="forbid"` catches key typos) and serves as living documentation of the schema. Normalizes the two qualification shapes (`{characteristic, target}` and `{options: [...]}`) and the two skill-table shapes (flat list vs `{requirement, skills}`). `CareerSummary` / `QualificationSummary` are the typed lightweight selection read models. The domain layer consumes the typed models directly where they never cross the generic API contract — `CareerTerm`/`AssignmentChangeTerm` hold `assignments: list[Assignment]`, `ranks: list[Rank]`, and qualification `options: list[CharacteristicCheck]`, converting to plain dicts only at the `StepPrompt`/`StepOutcome.data` boundary. Plain-dict views (`normalized_skill_tables()`, `skill_table_requirements()`, …) remain for the shapes still passed as dicts.
- **`src/career_loader.py`** — `get_available_careers()` (returns lightweight `CareerSummary` models), `load_career(name)` (returns a validated `CareerData`), `filter_eligible_careers()`. `CareerTerm.__init__(character, career: CareerData, *, is_first_term, term_number, assignment_override, force_auto_qualify)` takes the typed model directly — no kwargs splat.
- **`src/career_repository.py`** — the `CareerRepository` Protocol (`get_available() -> list[CareerSummary]`, `load(name) -> CareerData`) that terms read the career catalogue through, carried on `CareerContext.careers`. `FilesystemCareerRepository` (the default, constructed by `GameSession`) wraps `career_loader` and caches: each career YAML is parsed/validated at most once per instance (i.e. per session), so re-prompting Career Selection never re-globs or re-validates. `InMemoryCareerRepository` is the test stub — term transitions can be exercised against an in-memory career set with no filesystem access. Terms (`childhood`, `education/terms`, `careers/terms`) call `context.careers.load(...)` / `.get_available()` rather than importing the loader functions.

## Key patterns

- **Self-describing steps**: every step declares its `step_type` and `prompt()` so the API and frontend handle any step generically. Adding a new term/step requires only new domain code — no API or frontend changes.
- **Uniform resolve interface**: all steps accept `resolve(player_input: dict | None = None)`. Automatic steps ignore input; interactive steps read `player_input["selections"]`.
- **Explicit submit per step, auto-advance across terms**: every step (automatic *or* choice) needs its own `submit()` so each outcome is visible; the engine never silently chains steps. It *does* silently cross exhausted term boundaries. A just-resolved automatic step's post-resolve prompt rides back in `SubmitResult.resolved_steps`.
- **Prompts are re-rendered post-resolve**: step `apply()` populates `self.outcome: StepOutcome | None` with a status tag and a human-readable description; `prompt()` reads `self.outcome.description` when present and otherwise renders a "before" description. The frontend displays both.
- **Pass/fail roll steps**: `RollQualificationStep`, `SurvivalCheckStep`, and `AdvancementRollStep` all inherit from `PassFailRollStep` in `src/terms/base.py`, which handles the 2d6 + DM vs target boilerplate. Subclasses declare `step_id`, `check_label`, `status_pass`, `status_fail`.
- **Term-owned routing**: each `Term` implements `next_term(context: CareerContext) -> Term | None`. The engine's transition logic is just `self.term.next_term(self.context)`. `CareerTerm` synthesizes its own terminal outcome (`StepStatus.FAILED_QUAL` / `MISHAP` / `EVENT` / `FORCED_EXIT` / `COMPLETED`) at the end of its step machine so `next_term` can branch on `StepStatus` members rather than `isinstance` checks.
- **Imports use `src.` prefix** (e.g., `from src.character import Character`).

## Agent guidance files

`AGENTS.md` (for Codex) is a near-duplicate of this file. Keep the two in sync when editing architectural notes.

## Backlog

Open issues live as one file per issue under `Backlog/`, indexed by `Backlog/README.md`. Check there for the current list of known bugs, missing mechanics, and architectural RFCs before adding new features or refactors.

The backlog is fed by three skills: `backlog` (sort/add), `iterate` (execute/ship the top item), and the `audit` suite that *discovers* items. `/audit ultimate` fans out five focus audits in parallel — `audit-rules` (MgT 2022 fidelity via the "Bowman Arm" NotebookLM notebook), `audit-architecture`, `audit-ux`, `audit-tests`, `audit-perf` — then dedupes, impact-ranks, files them, and ships to `main`. Each focus audit is also runnable standalone (files directly to `Backlog/`, no commit).
