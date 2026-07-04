"""Typed career data model — the validated intermediate between career YAML
and the domain layer.

`career_loader.load_career()` parses a YAML file into a `CareerData` instance,
validating it against this schema at load time so a typo in a key or a missing
field surfaces immediately rather than deep in the career flow. `CareerTerm`
accepts a `CareerData` instance, making the loader → Term contract explicit.

This model is the living documentation of the career YAML schema. See
`data/careers/*.yaml` for examples of every shape described here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class CharacteristicCheck(BaseModel):
    """A `{characteristic, target}` roll target (qualification / survival /
    advancement / commission)."""

    model_config = ConfigDict(extra="forbid")

    characteristic: str
    target: int


class Qualification(BaseModel):
    """Career entry requirement.

    Accepts two YAML shapes, normalized to `options` (an OR-list) here:
      - single: `{characteristic: X, target: N}`
      - multi:  `{options: [{characteristic, target}, ...]}`
    Either may set `auto: true` — the character auto-qualifies if they meet
    *any* option's threshold; otherwise the career is filtered out of
    selection.
    """

    model_config = ConfigDict(extra="forbid")

    options: list[CharacteristicCheck]
    auto: bool = False

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if isinstance(data, dict) and "options" not in data:
            return {
                "options": [
                    {"characteristic": data["characteristic"], "target": data["target"]}
                ],
                "auto": data.get("auto", False),
            }
        return data


class QualificationSummary(BaseModel):
    """Lightweight qualification data used by career selection."""

    model_config = ConfigDict(extra="forbid")

    options: list[CharacteristicCheck]
    auto: bool = False


class CareerSummary(BaseModel):
    """Lightweight career data used by eligibility and selection prompts."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    qualification: QualificationSummary
    entry_only: bool = False


class Assignment(BaseModel):
    """One assignment within a career, with its own survival / advancement
    checks."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    survival: CharacteristicCheck
    advancement: CharacteristicCheck


class SkillTableRequirement(BaseModel):
    """Per-table access gate. Either a characteristic minimum
    (`{characteristic, minimum}`) or a commission gate (`{commissioned: true}`)."""

    model_config = ConfigDict(extra="forbid")

    characteristic: str | None = None
    minimum: int | None = None
    commissioned: bool | None = None


class SkillTable(BaseModel):
    """A skill table: a flat list of entries, optionally gated by a
    requirement. A bare YAML list is normalized to `{skills: [...]}`."""

    model_config = ConfigDict(extra="forbid")

    skills: list[str]
    requirement: SkillTableRequirement | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"skills": data}
        return data


class Rank(BaseModel):
    """A rank rung, with an optional bonus skill/characteristic granted on
    reaching it.

    ``bonus_skill`` is a single string: a bare skill name (granted at level 0
    via ``apply_rank_bonus``) or a "<Characteristic> +<N>" bump. The rank-0
    entry (``rank: 0``) is granted the moment the career is entered, before any
    advancement roll (see ``CareerTerm._after_qualification``).

    The single-string shape cannot express the two RAW cases where a rank grants
    a *choice*; both are simplified with a documented fallback rather than a
    schema extension:
      - Marine rank 0 ("Gun Combat (any) 1 or Melee (blade) 1") → a fixed
        ``Gun Combat`` grant (matching Marine rank 1, and consistent with the
        loader collapsing the "(any)" specialty choice to base Gun Combat).
      - Army General / Marine Colonel ("SOC 10 or SOC +1, whichever is higher")
        → ``Social Standing +1`` (the common case; the floor-to-10 is dropped).
    """

    model_config = ConfigDict(extra="forbid")

    rank: int
    title: str
    bonus_skill: str | None = None


class Benefits(BaseModel):
    """Muster-out benefit tables — a cash column and a material column,
    indexed by benefit roll."""

    model_config = ConfigDict(extra="forbid")

    cash: list[int] = []
    material: list[str] = []


class CareerData(BaseModel):
    """The full, validated contents of one `data/careers/<name>.yaml` file.

    Events / mishaps stay loosely typed (`dict[int, str | dict]`): each entry
    is either flavor text or a `{text, effects}` block consumed by
    `src.terms.effects.parse_entry`.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    qualification: Qualification
    service_skills: list[str]
    assignments: list[Assignment]
    skill_tables: dict[str, SkillTable]
    commission: CharacteristicCheck | None = None
    assignment_change_group: str | None = None
    ranks: list[Rank] = []
    officer_ranks: list[Rank] = []
    benefits: Benefits = Benefits()
    events: dict[int, str | dict[str, Any]] = {}
    mishaps: dict[int, str | dict[str, Any]] = {}
    entry_only: bool = False
    basic_training_from_assignment: bool = False

    # --- Views consumed by the domain layer (plain dicts/lists) ------------

    def qualification_options(self) -> list[dict]:
        """Qualification options as plain `{characteristic, target}` dicts."""
        return [o.model_dump() for o in self.qualification.options]

    def commission_as_dict(self) -> dict | None:
        return self.commission.model_dump() if self.commission else None

    def benefits_as_dict(self) -> dict:
        return self.benefits.model_dump()

    def normalized_skill_tables(self) -> dict[str, list[str]]:
        """Flat `name -> [skills]` mapping (drops requirement metadata)."""
        return {name: table.skills for name, table in self.skill_tables.items()}

    def skill_table_requirements(self) -> dict[str, dict]:
        """`name -> requirement` for gated tables only."""
        return {
            name: table.requirement.model_dump(exclude_none=True)
            for name, table in self.skill_tables.items()
            if table.requirement is not None
        }

    def qualification_summary(self) -> CareerSummary:
        """Lightweight summary for career-selection eligibility checks."""
        return CareerSummary(
            name=self.name,
            description=self.description,
            qualification=QualificationSummary(
                options=self.qualification.options,
                auto=self.qualification.auto,
            ),
            entry_only=self.entry_only,
        )
