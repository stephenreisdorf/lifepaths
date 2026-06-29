from pathlib import Path

import yaml

from src.career_data import CareerData
from src.character import Character

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "careers"


def _load_file(path: Path) -> CareerData:
    """Parse and validate a single career YAML file into a CareerData."""
    with open(path) as f:
        return CareerData.model_validate(yaml.safe_load(f))


def get_available_careers() -> list[dict]:
    """Return a `{name, description, qualification, entry_only}` summary dict for
    every career YAML. Each file is validated against `CareerData` on the way."""
    careers: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.yaml")):
        careers.append(_load_file(path).qualification_summary())
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


def load_career(career_name: str) -> CareerData:
    """Load and validate the full career data for a career by name."""
    return _load_file(DATA_DIR / f"{career_name.lower()}.yaml")
