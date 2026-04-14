"""Structured effects for events and mishaps.

Events / mishaps entries in career YAML may be:
- a plain string (flavor text only, no mechanical effect), or
- a dict with `{text, effects}` where `effects` is a list of effect dicts.

Each effect dict declares a `type` and type-specific fields. Supported:

- `skill`       — grant a skill.
    `{type: skill, name: <str>, level?: <int>, specialty?: <str>}`
    Matches `Character.grant_skill` semantics: omit `level` for the bare
    Traveller notation (+1 if present, else rank 1); `level: 0` ensures
    the skill exists at rank 0; explicit `level: N` raises to N.

- `characteristic` — bump a characteristic by a signed delta.
    `{type: characteristic, name: <str>, delta: <int>}`

- `associate`   — add a Contact / Ally / Rival / Enemy.
    `{type: associate, associate_type: <contact|ally|rival|enemy>,
      name?: <str>, description?: <str>}`

- `forced_exit` — the character is ejected from the career at term end.
    `{type: forced_exit}`
    The owning step exposes `forced_exit: bool` so CareerTerm can end
    the term with the FORCED_EXIT status rather than EVENT / COMPLETED.

- `advancement_dm` / `benefit_dm` — flavor-only for now; recorded in
    the effect description so the player sees it, but no mechanical
    DM stacking is tracked yet.
"""

from __future__ import annotations

from src.character import AssociateType, Character


def parse_entry(entry: object) -> tuple[str, list[dict]]:
    """Split a raw events/mishaps YAML entry into (text, effects).

    Plain strings are treated as flavor-only. Dict entries carry an
    optional `text` (rendered to the player) and an optional `effects`
    list (applied mechanically).
    """
    if isinstance(entry, str):
        return entry.strip(), []
    if isinstance(entry, dict):
        text = str(entry.get("text", "")).strip()
        effects = list(entry.get("effects") or [])
        return text, effects
    return "", []


def has_effect(effects: list[dict], effect_type: str) -> bool:
    """Return whether any effect in `effects` is of the given type."""
    return any(e.get("type") == effect_type for e in effects)


def apply_effects(character: Character, effects: list[dict]) -> list[str]:
    """Apply each effect to the character; return human-readable descriptions.

    Unknown / unsupported effect types are skipped silently but surfaced
    in the returned descriptions list so they're visible in the prompt.
    """
    descriptions: list[str] = []
    for effect in effects:
        etype = effect.get("type")
        if etype == "skill":
            descriptions.append(_apply_skill(character, effect))
        elif etype == "characteristic":
            desc = _apply_characteristic(character, effect)
            if desc:
                descriptions.append(desc)
        elif etype == "associate":
            descriptions.append(_apply_associate(character, effect))
        elif etype == "forced_exit":
            descriptions.append("Forced to leave the career at term end.")
        elif etype == "advancement_dm":
            descriptions.append(
                f"Advancement DM {_signed(effect.get('value', 0))} this term."
            )
        elif etype == "benefit_dm":
            descriptions.append(
                f"Benefit DM {_signed(effect.get('value', 0))}."
            )
        else:
            descriptions.append(f"(unhandled effect: {etype})")
    return descriptions


def _apply_skill(character: Character, effect: dict) -> str:
    name = effect["name"]
    level = effect.get("level")
    specialty = effect.get("specialty")
    character.grant_skill(name, level=level, specialty=specialty)
    label = name + (f" ({specialty})" if specialty else "")
    if level is None:
        return f"Gained {label}"
    if level == 0:
        return f"Gained {label} at level 0"
    return f"Gained {label} {level}"


def _apply_characteristic(character: Character, effect: dict) -> str | None:
    name = effect["name"]
    delta = int(effect["delta"])
    stat = character.characteristics.get(name)
    if stat is None:
        return None
    character.add_characteristic(name, stat.value + delta)
    return f"{name} {_signed(delta)}"


def _apply_associate(character: Character, effect: dict) -> str:
    assoc_type = AssociateType(effect["associate_type"])
    name = effect.get("name") or f"Unnamed {assoc_type.value}"
    character.add_associate(
        name=name,
        type=assoc_type,
        description=effect.get("description", ""),
    )
    return f"Gained {assoc_type.value}: {name}"


def _signed(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)
