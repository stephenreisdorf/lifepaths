from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "careers"


def get_available_careers() -> list[dict]:
    """Return a list of {name, description} dicts for every career YAML on disk."""
    careers: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        careers.append({"name": data["name"], "description": data.get("description", "")})
    return careers


def load_career(career_name: str) -> dict:
    """Load and return the full parsed YAML for a career by name."""
    path = DATA_DIR / f"{career_name.lower()}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def career_to_term_kwargs(career_data: dict, is_first_term: bool) -> dict:
    """Transform parsed career YAML into kwargs for CareerTerm.__init__."""
    # Extract flat assignment name list from rich assignment objects
    assignments = [a["name"] for a in career_data["assignments"]]

    # Normalize skill tables: gated tables have a {requirement, skills} structure,
    # while normal tables are flat lists. Extract just the skill lists.
    skill_tables: dict[str, list[str]] = {}
    for table_name, table_value in career_data["skill_tables"].items():
        if isinstance(table_value, dict) and "skills" in table_value:
            skill_tables[table_name] = table_value["skills"]
        else:
            skill_tables[table_name] = table_value

    return {
        "career_name": career_data["name"],
        "qualification_characteristic": career_data["qualification"]["characteristic"],
        "qualification_target": career_data["qualification"]["target"],
        "service_skills": career_data["service_skills"],
        "assignments": assignments,
        "skill_tables": skill_tables,
        "is_first_term": is_first_term,
    }
