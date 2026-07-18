from types import SimpleNamespace

from src.engine import GameSession
from src.terms.base import LifepathPhase
from src.terms.careers.muster_out import MusterOutTerm
from src.terms.education import PreCareerChoiceTerm


def test_start_reports_childhood_progress() -> None:
    result = GameSession().start()

    assert result.progress.phase == LifepathPhase.CHILDHOOD
    assert result.progress.phase_index == 1
    assert result.progress.phase_count == 4
    assert result.progress.career_term_number is None


def test_progress_reports_education_phase() -> None:
    session = GameSession()
    session.term = PreCareerChoiceTerm(session.character, options=[])

    progress = session._progress()

    assert progress.phase == LifepathPhase.EDUCATION
    assert progress.phase_index == 2


def test_progress_reports_in_progress_career_term_number() -> None:
    session = GameSession()
    session.term = SimpleNamespace(term_number=3)

    progress = session._progress()

    assert progress.phase == LifepathPhase.CAREER
    assert progress.phase_index == 3
    assert progress.career_term_number == 3


def test_progress_reports_completed_term_during_career_transition() -> None:
    session = GameSession()
    session.term = SimpleNamespace()
    session.context.career_term_count = 2

    progress = session._progress()

    assert progress.career_term_number == 2


def test_progress_reports_muster_out_phase() -> None:
    session = GameSession()
    session.term = MusterOutTerm(
        session.character,
        career_name="Scout",
        benefits={},
        terms_served=0,
        rank=0,
    )

    progress = session._progress()

    assert progress.phase == LifepathPhase.MUSTER_OUT
    assert progress.phase_index == 4
    assert progress.career_term_number is None
