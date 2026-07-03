"""Pre-Career Education (University / Military Academy).

The optional phase between Childhood and Career Selection. This package
re-exports its public surface so callers can
``from src.terms.education import <name>``.

- ``config`` — institution data and eligibility helpers.
- ``steps``  — the choice / roll / graduation Step subclasses.
- ``terms``  — PreCareerChoiceTerm, UniversityTerm, MilitaryAcademyTerm.
"""

from src.terms.education.config import (
    MILITARY_ACADEMIES,
    UNIVERSITY,
    academy_by_career,
    eligible_options,
)
from src.terms.education.steps import (
    AcademyGraduationStep,
    ChoosePreCareerStep,
    ChooseUniversitySkillsStep,
    EducationQualificationStep,
    UniversityGraduationStep,
)
from src.terms.education.terms import (
    MilitaryAcademyTerm,
    PreCareerChoiceTerm,
    UniversityTerm,
)

__all__ = [
    "MILITARY_ACADEMIES",
    "UNIVERSITY",
    "AcademyGraduationStep",
    "ChoosePreCareerStep",
    "ChooseUniversitySkillsStep",
    "EducationQualificationStep",
    "MilitaryAcademyTerm",
    "PreCareerChoiceTerm",
    "UniversityTerm",
    "academy_by_career",
    "eligible_options",
]
