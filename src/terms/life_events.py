"""Life Events and Injury sub-tables (Mongoose Traveller 2022, pp. 48-49).

Career events / mishaps that instruct "Roll on the Life Events table" or
"Roll on the Injury table" resolve here. Both are driven by the seeded
`src.utilities.roll`, so tests can make them deterministic via `rng.seed(...)`.

Each table row is resolved into a `(summary, effects)` pair where `effects`
uses the existing effect vocabulary in `src.terms.effects` (skill /
characteristic / associate / ...). `apply_effects` applies those effects
recursively, so every skill / associate / characteristic mutation stays
funneled through the one appliers set rather than being re-implemented here.

The rulebook lets the player choose which characteristic an injury reduces;
the engine picks deterministically in `PHYSICAL_CHARACTERISTICS` order, the
same policy the ageing step uses.
"""

from __future__ import annotations

from src.utilities import roll

# Physical characteristics an injury may reduce, in the deterministic order the
# engine assigns "one" / "another" / "any physical" reductions.
PHYSICAL_CHARACTERISTICS = ("Strength", "Dexterity", "Endurance")


INJURY_LABELS: dict[int, str] = {
    1: "Nearly killed",
    2: "Severely injured",
    3: "Missing eye or limb",
    4: "Scarred",
    5: "Injured",
    6: "Lightly injured",
}


def _injury_effects(result: int) -> list[dict]:
    """Concrete characteristic reductions for a 1D Injury result.

    Row 1 and 2 include a 1D reduction, rolled here so it rides on the same
    seeded RNG. Physical characteristics are assigned in
    `PHYSICAL_CHARACTERISTICS` order.
    """
    strength, dexterity, endurance = PHYSICAL_CHARACTERISTICS
    if result == 1:  # Nearly killed: one physical -1D, two others -2 each.
        return [
            {"type": "characteristic", "name": strength, "delta": -roll(1)},
            {"type": "characteristic", "name": dexterity, "delta": -2},
            {"type": "characteristic", "name": endurance, "delta": -2},
        ]
    if result == 2:  # Severely injured: one physical -1D.
        return [{"type": "characteristic", "name": strength, "delta": -roll(1)}]
    if result == 3:  # Missing eye or limb: STR or DEX -2 (engine picks STR).
        return [{"type": "characteristic", "name": strength, "delta": -2}]
    if result == 4:  # Scarred: any physical -2.
        return [{"type": "characteristic", "name": strength, "delta": -2}]
    if result == 5:  # Injured: any physical -1.
        return [{"type": "characteristic", "name": strength, "delta": -1}]
    return []  # 6: Lightly injured — no permanent effect.


def resolve_injury(rolls: int = 1, take: str = "single") -> tuple[int, str, list[dict]]:
    """Roll on the Injury table and return (result, label, effects).

    `rolls` / `take` model the "roll twice and take the lower result" mishaps:
    a lower number on the Injury table is the *more* severe result, so
    `take="lower"` selects the minimum of the rolls.
    """
    results = [roll(1) for _ in range(max(1, rolls))]
    if take == "lower":
        result = min(results)
    elif take == "higher":
        result = max(results)
    else:
        result = results[0]
    return result, INJURY_LABELS[result], _injury_effects(result)


def _unusual_event(sub: int) -> tuple[str, list[dict]]:
    """Life Event 12 sub-table (roll 1D)."""
    if sub == 1:
        return (
            "Unusual Event — Psionics: you encounter a Psionic institute and "
            "may test your Psionic Strength to take the Psion career next term.",
            [],
        )
    if sub == 2:
        return (
            "Unusual Event — Aliens: you spend time among an alien species. "
            "Gain Science 1 and an alien Contact.",
            [
                {"type": "skill", "name": "Science"},
                {
                    "type": "associate",
                    "associate_type": "contact",
                    "name": "Alien contact",
                },
            ],
        )
    if sub == 3:
        return ("Unusual Event — Alien Artefact: you acquire a strange alien device.", [])
    if sub == 4:
        return ("Unusual Event — Amnesia: something happened to you, but you do not know what.", [])
    if sub == 5:
        return (
            "Unusual Event — Contact with Government: you briefly meet the highest "
            "echelons of the Imperium.",
            [],
        )
    return ("Unusual Event — Ancient Technology: you possess something older than the Imperium.", [])


def resolve_life_event() -> tuple[int, str, list[dict]]:
    """Roll 2D on the Life Events table and return (result, summary, effects).

    Rows whose consequence is a player choice or an untracked DM (Travel,
    Good Fortune, Crime, Birth/Death, most Unusual Events) resolve to a
    descriptive summary with no mechanical effects.
    """
    result = roll(2)
    if result == 2:
        return result, "Sickness or Injury", [{"type": "injury"}]
    if result == 3:
        return result, "Birth or Death: someone close to you is born or dies.", []
    if result == 4:
        return (
            result,
            "Ending of a relationship: it ends badly. Gain a Rival.",
            [{"type": "associate", "associate_type": "rival", "name": "Former partner"}],
        )
    if result == 5:
        return (
            result,
            "Improved relationship: it deepens. Gain an Ally.",
            [{"type": "associate", "associate_type": "ally", "name": "Romantic partner"}],
        )
    if result == 6:
        return (
            result,
            "New relationship: you become romantically involved. Gain an Ally.",
            [{"type": "associate", "associate_type": "ally", "name": "Romantic partner"}],
        )
    if result == 7:
        return (
            result,
            "New Contact: you gain a new Contact.",
            [{"type": "associate", "associate_type": "contact", "name": "New contact"}],
        )
    if result == 8:
        return (
            result,
            "Betrayal: a friend betrays you.",
            [{"type": "betrayal"}],
        )
    if result == 9:
        return (
            result,
            "Travel: you move to another world. Gain DM+2 to your next Qualification roll.",
            [],
        )
    if result == 10:
        return (
            result,
            "Good Fortune: gain DM+2 to any one Benefit roll.",
            [],
        )
    if result == 11:
        return (
            result,
            "Crime: lose one Benefit roll, or take the Prisoner career next term.",
            [],
        )
    # 12: Unusual Event — roll 1D on the sub-table.
    sub = roll(1)
    summary, effects = _unusual_event(sub)
    return result, summary, effects
