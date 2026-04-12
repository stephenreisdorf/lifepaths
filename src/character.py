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


class Character(BaseModel):
    """A player character with characteristics and skills."""

    name: str
    characteristics: dict[str, Characteristic]
    skills: dict[str, Skill]
    careers: dict[str, CareerRecord] = {}

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
