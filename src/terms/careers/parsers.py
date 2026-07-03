from __future__ import annotations

from src.career_data import CharacteristicCheck
from src.character import Character


def parse_skill_entry(entry: str) -> tuple[str, str | None, int | None]:
    """Parse a skill-table entry into (name, specialty, level).

    Forms handled:
      - "Skill"                → (name, None, None)  bare: +1, or grant at 1
      - "Skill 0"              → (name, None, 0)     ensure exists at 0
      - "Skill N"              → (name, None, N)     raise to N
      - "Parent (Specialty)"   → (parent, specialty, None)
      - "Parent (Specialty) N" → (parent, specialty, N)
    """
    entry = entry.strip()
    level: int | None = None
    tokens = entry.rsplit(" ", 1)
    if len(tokens) == 2 and tokens[1].lstrip("-").isdigit():
        entry, level = tokens[0].rstrip(), int(tokens[1])

    specialty: str | None = None
    if entry.endswith(")") and "(" in entry:
        paren = entry.rfind("(")
        specialty = entry[paren + 1 : -1].strip()
        entry = entry[:paren].rstrip()

    return entry, specialty, level


def best_qualification_option(
    character: Character, options: list[CharacteristicCheck]
) -> tuple[str, int]:
    """Pick the qualification option giving `character` the highest DM.

    For OR-qualification (e.g. Entertainer's DEX or INT), a character makes a
    single roll at their best modifier. Each option is a ``CharacteristicCheck``
    (``characteristic``/``target``); a characteristic the character lacks ranks
    last. Returns the winning ``(characteristic, target)``.
    """
    best = max(
        options,
        key=lambda o: character.characteristics[o.characteristic].modifier()
        if o.characteristic in character.characteristics
        else -99,
    )
    return best.characteristic, best.target


def try_apply_characteristic_bonus(character: Character, entry: str) -> bool:
    """If `entry` is '<Characteristic> +<N>', bump that characteristic.

    Returns True if the entry was consumed as a characteristic bonus, False
    if the caller should fall back to treating it as a skill. Used by both
    rank bonuses and skill-table rolls (Personal Development et al.).
    """
    parts = entry.rsplit(" +", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return False
    name, delta = parts[0], int(parts[1])
    if name not in character.characteristics:
        return False
    current = character.characteristics[name].value
    character.add_characteristic(name, current + delta)
    return True
