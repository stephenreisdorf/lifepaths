"""Pre-Career Education (University / Military Academy) flow.

Mirrors ``test_career_transitions``: transitions are exercised in isolation by
driving individual handlers / steps, so the deterministic behaviour is tested
without stepping a whole randomised run.
"""

from src.career_loader import load_career
from src.career_repository import FilesystemCareerRepository
from src.character import Character
from src.terms.base import PassFailRollStep, StepOutcome
from src.terms.careers import CareerTerm, ChooseCareerStep, TransitionTerm
from src.terms.context import CareerContext
from src.terms.education import (
    MILITARY_ACADEMIES,
    UNIVERSITY,
    ChoosePreCareerStep,
    MilitaryAcademyTerm,
    PreCareerChoiceTerm,
    UniversityTerm,
    eligible_options,
)
from src.terms.education.steps import (
    AcademyGraduationStep,
    ChooseUniversitySkillsStep,
    EducationQualificationStep,
    UniversityGraduationStep,
)


class _FakeStep:
    """Stand-in resolved step: an outcome plus any attributes a handler reads."""

    def __init__(self, status: str = "done", data: dict | None = None, **attrs):
        self.outcome = StepOutcome(status=status, data=data or {})
        for key, value in attrs.items():
            setattr(self, key, value)


def _character(**overrides: int) -> Character:
    char = Character(name="Test", characteristics={}, skills={})
    values = {
        "Strength": 7,
        "Dexterity": 7,
        "Endurance": 7,
        "Intelligence": 7,
        "Education": 7,
        "Social Standing": 7,
    }
    values.update(overrides)
    for name, value in values.items():
        char.add_characteristic(characteristic=name, value=value)
    char.age = 18
    return char


# Shared filesystem repository for constructing academy terms in tests.
_REPO = FilesystemCareerRepository()


def _academy(career: str, character: Character | None = None) -> MilitaryAcademyTerm:
    return MilitaryAcademyTerm(character or _character(), career, _REPO)


# --- Eligibility ----------------------------------------------------------


def test_eligible_options_gated_by_characteristics():
    # EDU 7, INT 7, END 7 → University + all three academies.
    keys = {o["key"] for o in eligible_options(_character())}
    assert keys == {"university", "academy:navy", "academy:army", "academy:marine"}

    # Everything below the floor → nothing qualifies.
    assert eligible_options(
        _character(Education=5, Endurance=5, Intelligence=5)
    ) == []

    # EDU 6 only (INT/END below floor) → University only.
    keys = {
        o["key"]
        for o in eligible_options(
            _character(Education=6, Endurance=5, Intelligence=5)
        )
    }
    assert keys == {"university"}

    # INT 6 (EDU/END below floor) → Naval Academy only.
    keys = {
        o["key"]
        for o in eligible_options(
            _character(Education=5, Endurance=5, Intelligence=6)
        )
    }
    assert keys == {"academy:navy"}


def test_choose_pre_career_step_offers_institutions_plus_skip():
    char = _character()
    step = ChoosePreCareerStep(char, eligible_options(char))
    labels = step.prompt().options
    assert "University" in labels
    assert "Military Academy (Army)" in labels
    assert ChoosePreCareerStep.SKIP_LABEL in labels


# --- PreCareerChoiceTerm dispatch -----------------------------------------


def _choice_term(choice: str) -> PreCareerChoiceTerm:
    char = _character()
    term = PreCareerChoiceTerm(char, eligible_options(char))
    term.steps[0].outcome = StepOutcome(status="CHOSEN", data={"choice": choice})
    return term


def test_choice_skip_routes_to_career_selection():
    term = _choice_term(ChoosePreCareerStep.SKIP_KEY)
    nxt = term.next_term(CareerContext(character=term.character))
    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ChooseCareerStep.step_id


def test_choice_university_routes_to_university_term():
    term = _choice_term("university")
    nxt = term.next_term(CareerContext(character=term.character))
    assert isinstance(nxt, UniversityTerm)


def test_choice_academy_routes_to_military_academy_term():
    term = _choice_term("academy:army")
    nxt = term.next_term(CareerContext(character=term.character))
    assert isinstance(nxt, MilitaryAcademyTerm)
    assert nxt.career_key == "army"


# --- UniversityTerm transitions -------------------------------------------


def test_university_qualification_failure_ends_not_admitted():
    term = UniversityTerm(_character())
    term._after_qualification(_FakeStep(status="FAILED"))
    assert term.outcome is not None
    assert term.outcome.status == "NOT_ADMITTED"


def test_university_qualified_appends_skill_choice():
    term = UniversityTerm(_character())
    term._after_qualification(_FakeStep(status="QUALIFIED"))
    assert term.steps[-1].step_id == ChooseUniversitySkillsStep.step_id


def test_university_skills_appends_graduation():
    term = UniversityTerm(_character())
    term._after_skills(_FakeStep(data={"major": "Science", "minor": "Admin"}))
    grad = term.steps[-1]
    assert isinstance(grad, UniversityGraduationStep)
    assert grad.major == "Science" and grad.minor == "Admin"


def test_university_entry_target_and_soc_bonus():
    # RAW: entry target 6, +1 DM if SOC >= 9 (not INT).
    plain = UniversityTerm(_character())
    assert plain.steps[0].target == 6
    assert plain.steps[0].extra_dm == 0  # SOC 7 → no bonus

    high_int = UniversityTerm(_character(Intelligence=9))
    assert high_int.steps[0].extra_dm == 0  # INT no longer grants the bonus

    high_soc = UniversityTerm(_character(**{"Social Standing": 9}))
    assert high_soc.steps[0].extra_dm == 1  # SOC 9+ → +1 DM


def test_university_next_term_sets_graduate_dm_on_context():
    term = UniversityTerm(_character())
    term.outcome = StepOutcome(status="EDUCATED", description="graduated")
    term._graduated_qualification_dm = 2
    context = CareerContext(character=term.character)

    nxt = term.next_term(context)

    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ChooseCareerStep.step_id
    assert context.pre_career_qualification_dm == 2


# --- University graduation side effects ------------------------------------


def _graduation_step(char: Character, total_roll: int) -> UniversityGraduationStep:
    grad = UniversityGraduationStep(
        char,
        major="Science",
        minor="Admin",
        characteristic="Intelligence",
        target=6,
        honours_target=10,
        graduate_qualification_dm=2,
    )
    grad.raw_roll = total_roll
    grad.total_roll = total_roll
    return grad


def test_university_graduation_bumps_skills_and_edu():
    char = _character()
    # Simulate entry: major at 1, minor at 0.
    char.grant_skill("Science", level=1)
    char.grant_skill("Admin", level=0)

    grad = _graduation_step(char, total_roll=8)  # pass, no honours
    grad.apply()

    assert grad.outcome.status == "GRADUATED"
    assert not grad.honours
    assert char.skills["Science"].base_rank == 2
    assert char.skills["Admin"].base_rank == 1
    assert char.characteristics["Education"].value == 8  # +1
    assert grad.qualification_dm == 2


def test_university_graduation_with_honours_grants_edu_plus_one():
    char = _character()
    char.grant_skill("Science", level=1)
    char.grant_skill("Admin", level=0)

    grad = _graduation_step(char, total_roll=11)  # honours
    grad.apply()

    assert grad.honours
    # RAW: honours grants EDU +1 (same as a plain graduation); the honours
    # distinction is a Commission roll, not extra EDU.
    assert char.characteristics["Education"].value == 8  # +1


def test_university_failed_graduation_keeps_entry_skills_only():
    char = _character()
    char.grant_skill("Science", level=1)
    char.grant_skill("Admin", level=0)

    grad = _graduation_step(char, total_roll=4)  # fail
    grad.apply()

    assert grad.outcome.status == "NOT_GRADUATED"
    assert char.skills["Science"].base_rank == 1  # unchanged
    assert char.skills["Admin"].base_rank == 0
    assert char.characteristics["Education"].value == 7  # unchanged
    assert grad.qualification_dm == 0


# --- Graduate DM feeds the first career qualification ----------------------


def test_choose_career_consumes_graduate_qualification_dm():
    char = _character()
    step = ChooseCareerStep(char, [])
    step.outcome = StepOutcome(status="CHOSEN", data={"career": "scout"})
    transition = TransitionTerm(char, step)
    context = CareerContext(character=char, pre_career_qualification_dm=2)

    nxt = transition.next_term(context)

    assert isinstance(nxt, CareerTerm)
    assert nxt.qualification_dm == 2
    # One-shot: cleared so later careers don't inherit it.
    assert context.pre_career_qualification_dm == 0


def test_pass_fail_step_folds_extra_dm_into_modifier():
    char = _character(Education=9)  # EDU 9 → +1 DM
    step = PassFailRollStep(char, "Education", target=7, extra_dm=2)
    assert step.modifier == 3  # +1 characteristic DM, +2 extra


# --- MilitaryAcademyTerm transitions --------------------------------------


def test_academy_qualification_failure_ends_not_admitted():
    term = _academy("army")
    term._after_qualification(_FakeStep(status="FAILED"))
    assert term.outcome is not None
    assert term.outcome.status == "NOT_ADMITTED"


def test_academy_qualified_appends_basic_training_then_graduation():
    term = _academy("army")
    term._after_qualification(_FakeStep(status="QUALIFIED"))
    assert term.steps[-1].step_id == "basic_training"

    term._after_training(term.steps[-1])
    assert isinstance(term.steps[-1], AcademyGraduationStep)


def test_academy_graduate_enters_career_commissioned():
    term = _academy("army")
    term.outcome = StepOutcome(status="GRADUATED", description="graduated")
    term._graduated = True
    context = CareerContext(character=term.character)

    nxt = term.next_term(context)

    assert isinstance(nxt, CareerTerm)
    assert context.current_career_data.name == load_career("army").name
    record = term.character.careers["army"]
    assert record.commissioned
    assert record.rank == 1
    # Officer rank-1 bonus (Leadership) applied.
    assert term.character.has_skill("Leadership")


def test_naval_academy_graduate_enters_navy_commissioned():
    term = _academy("navy")
    term.outcome = StepOutcome(status="GRADUATED", description="graduated")
    term._graduated = True
    context = CareerContext(character=term.character)

    nxt = term.next_term(context)

    assert isinstance(nxt, CareerTerm)
    assert context.current_career_data.name == load_career("navy").name
    record = term.character.careers["navy"]
    assert record.commissioned and record.rank == 1
    # Navy officer rank-1 bonus (Ensign → Leadership) applied.
    assert term.character.has_skill("Leadership")


def test_academy_attended_enters_career_enlisted():
    term = _academy("army")
    term.outcome = StepOutcome(status="ATTENDED", description="did not graduate")
    term._graduated = False
    context = CareerContext(character=term.character)

    nxt = term.next_term(context)

    assert isinstance(nxt, CareerTerm)
    # No commission was granted.
    assert "army" not in term.character.careers or (
        not term.character.careers["army"].commissioned
    )


def test_academy_not_admitted_routes_to_career_selection():
    term = _academy("army")
    term.outcome = StepOutcome(status="NOT_ADMITTED", description="rejected")
    context = CareerContext(character=term.character)

    nxt = term.next_term(context)

    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ChooseCareerStep.step_id


def test_academy_ages_character_on_graduation():
    term = _academy("army")
    start_age = term.character.age
    grad = _FakeStep(status="GRADUATED", graduated=True)
    grad.outcome = StepOutcome(status="GRADUATED", description="graduated")
    term._after_graduation(grad)
    assert term.character.age == start_age + 4


# --- RAW config fidelity ---------------------------------------------------


def test_university_config_matches_raw():
    qual = UNIVERSITY["qualification"]
    assert qual["target"] == 6
    assert qual["soc_bonus_at"] == 9
    assert "int_bonus_at" not in qual  # bonus is keyed on SOC, not INT
    # Graduation is an Intelligence check.
    assert UNIVERSITY["graduation"]["characteristic"] == "Intelligence"


def test_academy_graduation_is_intelligence_seven_check():
    # RAW: every military academy graduates on an Intelligence 7+ check.
    for academy in MILITARY_ACADEMIES:
        graduation = academy["graduation"]
        assert graduation["characteristic"] == "Intelligence", academy["name"]
        assert graduation["target"] == 7, academy["name"]


# --- Academy graduation side effects ---------------------------------------


def _academy_graduation_step(
    char: Character, total_roll: int
) -> AcademyGraduationStep:
    grad = AcademyGraduationStep(
        char,
        academy_name="Military Academy (Army)",
        characteristic="Intelligence",
        target=7,
        honours_target=11,
    )
    grad.raw_roll = total_roll
    grad.total_roll = total_roll
    return grad


def test_academy_graduation_no_honours_leaves_edu_and_soc():
    char = _character()  # EDU 7, SOC 7
    grad = _academy_graduation_step(char, total_roll=9)  # graduate, no honours
    grad.apply()

    assert grad.outcome.status == "GRADUATED"
    assert not grad.honours
    assert char.characteristics["Education"].value == 7
    assert char.characteristics["Social Standing"].value == 7


def test_academy_graduation_with_honours_grants_edu_and_soc():
    char = _character()  # EDU 7, SOC 7
    grad = _academy_graduation_step(char, total_roll=11)  # honours
    grad.apply()

    assert grad.honours
    assert char.characteristics["Education"].value == 8  # EDU +1
    assert char.characteristics["Social Standing"].value == 8  # SOC +1
