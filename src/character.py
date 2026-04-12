from enum import Enum

from pydantic import BaseModel


class Characteristic(BaseModel):
    """A character attribute (e.g. Strength, Dexterity) with a numeric value."""

    name: str
    value: int

    def modifier(self) -> int:
        """Calculate the Traveller-style dice modifier (value // 3 - 2)."""
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


class Character(BaseModel):
    """A player character with characteristics and skills."""

    name: str
    characteristics: dict[str, Characteristic]
    skills: dict[str, Skill]
    careers: dict[str, CareerRecord] = {}
    associates: list[Associate] = []

    def add_characteristic(self, characteristic: str, value: int) -> None:
        """Add or replace a characteristic with the given value."""
        self.characteristics[characteristic] = Characteristic(
            name=characteristic,
            value=value,
        )

    def has_skill(self, name: str) -> bool:
        """Return whether the character has the named skill."""
        return name in self.skills

    def add_skill(self, name: str) -> None:
        """Add a skill at base rank 0. No-op if the skill already exists."""
        if self.has_skill(name):
            return
        new_skill = Skill(name=name, specialties={}, base_rank=0)
        self.skills[name] = new_skill

    def increment_skill(self, name: str, specialty: str, increment: int = 1) -> None:
        """Increment a skill specialty's rank, creating the skill/specialty if needed."""
        if not self.has_skill(name):
            self.add_skill(name)
        skill = self.skills[name]
        if not skill.has_specialty(specialty):
            skill.add_specialty(specialty, increment)
        else:
            skill.specialties[specialty].rank += increment

    def grant_skill(
        self,
        name: str,
        level: int | None = None,
        specialty: str | None = None,
    ) -> None:
        """Grant a skill (or specialty) per Traveller notation.

        - `level=0` : ensure the skill / specialty exists at rank 0 (no-op if
          already present).
        - `level=None` (bare): if absent, grant at rank 1; if present, raise
          rank by 1.
        - `level=N` (explicit): if current rank < N, raise to N; otherwise
          no-op (no reduction).

        `specialty` targets the named specialty on the parent skill; when
        None the rank applies to the skill's `base_rank`.
        """
        if not self.has_skill(name):
            self.add_skill(name)
        skill = self.skills[name]

        if specialty is not None:
            if not skill.has_specialty(specialty):
                start = 0 if level == 0 else max(level or 1, 1)
                skill.add_specialty(specialty, start)
                return
            current = skill.specialties[specialty].rank
            if level is None:
                skill.specialties[specialty].rank = current + 1
            elif level > current:
                skill.specialties[specialty].rank = level
            return

        current = skill.base_rank
        if level is None:
            skill.base_rank = current + 1
        elif level == 0:
            # No-op: skill already exists at base_rank >= 0.
            return
        elif level > current:
            skill.base_rank = level

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
