"""Career life-path flow.

Split into focused sub-modules — this package re-exports the full public
surface so callers can continue to `from src.terms.careers import <name>`.

- ``parsers``    — skill-entry / characteristic-bonus text parsers.
- ``steps``      — the interactive/automatic Step subclasses.
- ``aging``      — the aging table and AgingStep.
- ``muster_out`` — MusterOutStep, MusterOutTerm, and benefit-roll wiring.
- ``terms``      — CareerTerm, TransitionTerm, AssignmentChangeTerm.
"""

from src.terms.careers.aging import AGING_TABLE, AgingStep
from src.terms.careers.muster_out import MusterOutStep, MusterOutTerm
from src.terms.careers.parsers import (
    parse_skill_entry,
    try_apply_characteristic_bonus,
)
from src.terms.careers.steps import (
    AdvancementRollStep,
    AutoQualifyStep,
    BasicTrainingStep,
    ChooseAssignmentStep,
    ChooseCareerSkillsTable,
    ChooseCareerStep,
    ChooseDraftOrDrifterStep,
    CommissionStep,
    ContinueOrMusterOutStep,
    EventsRollStep,
    MishapRollStep,
    MusterOutOrNewCareerStep,
    PickServiceSkillStep,
    RollForSkillStep,
    RollQualificationStep,
    SurvivalCheckStep,
)
from src.terms.careers.terms import (
    AssignmentChangeTerm,
    CareerTerm,
    TransitionTerm,
)

__all__ = [
    "AGING_TABLE",
    "AdvancementRollStep",
    "AgingStep",
    "AssignmentChangeTerm",
    "AutoQualifyStep",
    "BasicTrainingStep",
    "CareerTerm",
    "ChooseAssignmentStep",
    "ChooseCareerSkillsTable",
    "ChooseCareerStep",
    "ChooseDraftOrDrifterStep",
    "CommissionStep",
    "ContinueOrMusterOutStep",
    "EventsRollStep",
    "MishapRollStep",
    "MusterOutOrNewCareerStep",
    "MusterOutStep",
    "MusterOutTerm",
    "PickServiceSkillStep",
    "RollForSkillStep",
    "RollQualificationStep",
    "SurvivalCheckStep",
    "TransitionTerm",
    "parse_skill_entry",
    "try_apply_characteristic_bonus",
]
