from enum import Enum

from pydantic import BaseModel


class Characteristic(BaseModel):
    """A character attribute (e.g. Strength, Dexterity) with a numeric value."""

    name: str
    value: int

    def modifier(self) -> int:
        """Calculate the Traveller-style dice modifier.

        The formula ``value // 3 - 2`` reproduces the Core Rulebook DM table for
        all scores except 0, which the table assigns -3 (the formula yields -2).
        """
        if self.value == 0:
            return -3
        return self.value // 3 - 2


class SkillSpecialty(BaseModel):
    """A named specialty within a skill, tracked by rank."""

    name: str
    rank: int


class Skill(BaseModel):
    """A skill with a base rank and optional specialties."""

    name: str
    specialties: dict[str, SkillSpecialty]
    base_rank: int

    def has_specialty(self, name: str) -> bool:
        """Return whether this skill has the given specialty."""
        return name in self.specialties

    def add_specialty(self, name: str, rank: int) -> None:
        """Add a new specialty with the given rank."""
        self.specialties[name] = SkillSpecialty(name=name, rank=rank)


class CareerRecord(BaseModel):
    """A character's standing within a specific career."""

    name: str
    rank: int = 0
    terms_served: int = 0
    ejected: bool = False
    commissioned: bool = False


class AnagathicsCourse(BaseModel):
    """An active course of anti-aging drugs (Core Rulebook, Ageing).

    A character of sufficient Social Standing may take anagathics to hold off
    ageing. While the course is `active`, `terms_used` (the number of terms it
    has been maintained) is added as a *positive* DM to the Ageing roll,
    offsetting the -(terms served) penalty so the Traveller "effectively does
    not age". Each term costs 1D×Cr25000 (accumulated in `total_cost`); the
    charge is deducted from cash, which may go into debt.
    """

    terms_used: int = 1
    total_cost: int = 0
    active: bool = True


class AssociateType(str, Enum):
    """Kinds of associates a character can accumulate."""

    CONTACT = "contact"
    ALLY = "ally"
    RIVAL = "rival"
    ENEMY = "enemy"


class Associate(BaseModel):
    """A named associate (Contact / Ally / Rival / Enemy)."""

    name: str
    type: AssociateType
    description: str = ""
    source_event: str | None = None


SKILL_MAX_LEVEL = 4  # RAW: no single skill may exceed level 4 during creation.


class Character(BaseModel):
    """A player character with characteristics and skills."""

    name: str
    age: int = 18
    characteristics: dict[str, Characteristic]
    skills: dict[str, Skill]
    careers: dict[str, CareerRecord] = {}
    associates: list[Associate] = []
    # Credits accumulated from Cash benefit rolls during muster-out.
    cash: int = 0
    # Material muster-out benefits that don't fit into skills / characteristics /
    # associates (e.g. "Weapon", "Ship Share", "TAS Membership").
    possessions: list[str] = []
    # Set by an enter_career effect (typically from a mishap): the engine
    # forces entry into this career on the next term transition and clears
    # the flag. Does not bypass normal career selection when None.
    pending_career_entry: str | None = None
    # An active (or discontinued) course of anti-aging drugs; None until the
    # character starts one. See AnagathicsCourse and src/terms/anagathics.py.
    anagathics: AnagathicsCourse | None = None

    def total_skill_levels(self) -> int:
        """Return the sum of every skill's base_rank plus all specialty ranks."""
        total = 0
        for skill in self.skills.values():
            total += skill.base_rank
            total += sum(sp.rank for sp in skill.specialties.values())
        return total

    def total_skill_level_cap(self) -> int:
        """RAW cap: 3 × (INT + EDU). Returns a large fallback if stats absent."""
        int_stat = self.characteristics.get("Intelligence")
        edu_stat = self.characteristics.get("Education")
        if int_stat is None or edu_stat is None:
            return 10**9  # effectively uncapped pre-childhood
        return 3 * (int_stat.value + edu_stat.value)

    def _budget_allows_increment(self, amount: int = 1) -> bool:
        """Return True if raising total skill levels by `amount` stays within the 3×(INT+EDU) cap."""
        return self.total_skill_levels() + amount <= self.total_skill_level_cap()

    def add_characteristic(self, characteristic: str, value: int) -> None:
        """Add or replace a characteristic with the given value."""
        self.characteristics[characteristic] = Characteristic(
            name=characteristic,
            value=value,
        )

    def has_skill(self, name: str) -> bool:
        """Return whether the character has the named skill."""
        return name in self.skills

    def _ensure_skill(self, name: str) -> Skill:
        """Return the named skill, creating it at base rank 0 if absent.

        Internal primitive used by `grant_skill`; callers grant skills via
        `grant_skill`, the single public skill-mutation entry point.
        """
        if not self.has_skill(name):
            self.skills[name] = Skill(name=name, specialties={}, base_rank=0)
        return self.skills[name]

    def grant_skill(
        self,
        name: str,
        level: int | None = None,
        specialty: str | None = None,
    ) -> None:
        """Grant a skill (or specialty) per Traveller notation.

        This is the single entry point for all skill mutation; every caller
        (background/service skills, skill-table rolls, rank bonuses, event and
        mishap effects) routes through here.

        - `level=0` : ensure the skill / specialty exists at rank 0 (no-op if
          already present).
        - `level=None` (bare): if absent, grant at rank 1; if present, raise
          rank by 1.
        - `level=N` (explicit): if current rank < N, raise to N; otherwise
          no-op (no reduction).

        `specialty` targets the named specialty on the parent skill; when
        None the rank applies to the skill's `base_rank`.

        Respects the per-skill cap (SKILL_MAX_LEVEL) and the total-skill-
        levels cap (3 × (INT + EDU)) by silently clamping / refusing further
        increments — RAW treats over-cap grants as wasted.
        """
        skill = self._ensure_skill(name)

        if specialty is not None:
            current = (
                skill.specialties[specialty].rank
                if skill.has_specialty(specialty)
                else 0
            )
        else:
            current = skill.base_rank

        target = self._clamp_target(current, level)
        delta = target - current

        # A zero/negative delta means no growth (e.g. `level=0`, or an
        # explicit level at or below the current rank). Raise nothing, but
        # still materialize a missing specialty at rank 0 so `level=0` can
        # ensure a specialty exists — mirroring how `_ensure_skill` creates a
        # missing base skill above.
        if delta <= 0:
            if specialty is not None and not skill.has_specialty(specialty):
                skill.add_specialty(specialty, target)
            return

        if not self._budget_allows_increment(delta):
            return

        if specialty is not None:
            if skill.has_specialty(specialty):
                skill.specialties[specialty].rank = target
            else:
                skill.add_specialty(specialty, target)
        else:
            skill.base_rank = target

    @staticmethod
    def _clamp_target(current: int, level: int | None) -> int:
        """Resolve the skill-grant notation to a target rank, clamped to SKILL_MAX_LEVEL."""
        if level is None:
            target = current + 1
        elif level == 0:
            target = current  # no change; caller may have just added the skill
        else:
            target = max(current, level)
        return min(target, SKILL_MAX_LEVEL)

    def ensure_career(self, name: str) -> CareerRecord:
        """Return the CareerRecord for `name`, creating it at rank 0 if missing."""
        if name not in self.careers:
            self.careers[name] = CareerRecord(name=name)
        return self.careers[name]

    def promote(self, name: str) -> CareerRecord:
        """Increment the character's rank in the given career and return the record."""
        record = self.ensure_career(name)
        record.rank += 1
        return record

    def record_career_term(self, name: str) -> CareerRecord:
        """Increment terms_served for the given career and return the record."""
        record = self.ensure_career(name)
        record.terms_served += 1
        return record

    def mark_career_ejected(self, name: str) -> CareerRecord:
        """Mark the career as having ended in ejection (mishap). Returns the record."""
        record = self.ensure_career(name)
        record.ejected = True
        return record

    def add_associate(
        self,
        name: str,
        type: AssociateType,
        description: str = "",
        source_event: str | None = None,
    ) -> Associate:
        """Add a new associate to the character and return it."""
        associate = Associate(
            name=name,
            type=type,
            description=description,
            source_event=source_event,
        )
        self.associates.append(associate)
        return associate

    def start_anagathics_course(self, cost: int) -> AnagathicsCourse:
        """Begin an anti-aging course (Core Rulebook, Ageing).

        Records the course active with one term of use — a +1 DM to the next
        Ageing roll — and charges this term's cost against cash (which may go
        negative, i.e. start the game in debt). Replaces any prior course.
        """
        self.anagathics = AnagathicsCourse(terms_used=1, total_cost=cost)
        self.cash -= cost
        return self.anagathics

    def maintain_anagathics_course(self, cost: int) -> None:
        """Extend the active course by one term, raising the Ageing DM.

        No-op when there is no active course. Charges this term's cost against
        cash (which may go into debt).
        """
        if self.anagathics is None or not self.anagathics.active:
            return
        self.anagathics.terms_used += 1
        self.anagathics.total_cost += cost
        self.cash -= cost

    def stop_anagathics_course(self) -> None:
        """Discontinue the course (RAW: triggers an immediate Ageing roll).

        The record is kept but marked inactive, so it no longer contributes a
        DM to Ageing. No-op when there is no course.
        """
        if self.anagathics is not None:
            self.anagathics.active = False

    def anagathics_aging_dm(self) -> int:
        """Return the positive Ageing DM from an active anagathics course."""
        if self.anagathics is not None and self.anagathics.active:
            return self.anagathics.terms_used
        return 0
