from pathlib import Path

import yaml

from src.character import Character

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "careers"


def _normalize_qualification(qual: dict) -> tuple[list[dict], bool]:
    """Return (options, auto) for a qualification YAML block.

    Supported shapes:
      - single: `{characteristic: X, target: N}`           -> 1 option
      - multi:  `{options: [{characteristic, target}, ...]}` -> N options (OR)
    Either shape may set `auto: true` — the character auto-qualifies if
    they meet *any* option's threshold; otherwise the career is
    unavailable (filtered out of career selection).
    """
    auto = bool(qual.get("auto", False))
    if "options" in qual:
        options = [dict(o) for o in qual["options"]]
    else:
        options = [{"characteristic": qual["characteristic"], "target": qual["target"]}]
    return options, auto


def _qualification_summary(qual: dict) -> dict:
    """Lightweight summary of a career's qualification for eligibility checks."""
    options, auto = _normalize_qualification(qual)
    return {"options": options, "auto": auto}


def get_available_careers() -> list[dict]:
    """Return a list of `{name, description, qualification, entry_only}` dicts for every career YAML."""
    careers: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        careers.append(
            {
                "name": data["name"],
                "description": data.get("description", ""),
                "qualification": _qualification_summary(data["qualification"]),
                "entry_only": bool(data.get("entry_only", False)),
            }
        )
    return careers


def filter_eligible_careers(
    character: Character, careers: list[dict]
) -> list[dict]:
    """Drop careers the character cannot enter.

    - Entry-only careers (e.g. Prisoner) never appear in normal selection;
      they are reached only via an `enter_career` effect.
    - Auto-qualification careers are dropped if none of their options meet
      the threshold.
    - Non-auto careers are always listed — the player is allowed to attempt
      a qualification roll regardless of DM.
    """
    eligible: list[dict] = []
    for career in careers:
        if career.get("entry_only"):
            continue
        qual = career.get("qualification") or {}
        if not qual.get("auto"):
            eligible.append(career)
            continue
        options = qual.get("options") or []
        if any(_meets_option(character, opt) for opt in options):
            eligible.append(career)
    return eligible


def _meets_option(character: Character, option: dict) -> bool:
    stat = character.characteristics.get(option["characteristic"])
    if stat is None:
        return False
    return stat.value >= option["target"]


def load_career(career_name: str) -> dict:
    """Load and return the full parsed YAML for a career by name."""
    path = DATA_DIR / f"{career_name.lower()}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def career_to_term_kwargs(career_data: dict, is_first_term: bool) -> dict:
    """Transform parsed career YAML into kwargs for CareerTerm.__init__."""
    # Normalize skill tables: gated tables have a {requirement, skills} structure,
    # while normal tables are flat lists. Extract skills and (separately) the
    # per-table requirement so CareerTerm can gate access at prompt time.
    skill_tables: dict[str, list[str]] = {}
    skill_table_requirements: dict[str, dict] = {}
    for table_name, table_value in career_data["skill_tables"].items():
        if isinstance(table_value, dict) and "skills" in table_value:
            skill_tables[table_name] = table_value["skills"]
            if "requirement" in table_value:
                skill_table_requirements[table_name] = table_value["requirement"]
        else:
            skill_tables[table_name] = table_value

    qual_options, qual_auto = _normalize_qualification(career_data["qualification"])

    return {
        "career_name": career_data["name"],
        "qualification_options": qual_options,
        "qualification_auto": qual_auto,
        "service_skills": career_data["service_skills"],
        "assignments": career_data["assignments"],
        "skill_tables": skill_tables,
        "skill_table_requirements": skill_table_requirements,
        "events": career_data.get("events", {}),
        "mishaps": career_data.get("mishaps", {}),
        "ranks": career_data.get("ranks", []),
        "officer_ranks": career_data.get("officer_ranks", []),
        "commission": career_data.get("commission"),
        "assignment_change_group": career_data.get("assignment_change_group"),
        "benefits": career_data.get("benefits") or {},
        "basic_training_from_assignment": bool(
            career_data.get("basic_training_from_assignment", False)
        ),
        "is_first_term": is_first_term,
    }
