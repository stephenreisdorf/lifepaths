"""CareerRepository: caching and disk-free term transitions.

Exercises the repository abstraction on ``CareerContext`` — that the default
filesystem repository parses each career at most once per session, and that a
career-selection transition backed by an in-memory stub touches no disk.
"""

import src.career_repository as repo_mod
from src.career_loader import load_career
from src.career_repository import (
    FilesystemCareerRepository,
    InMemoryCareerRepository,
)
from src.character import Character
from src.terms.base import StepOutcome
from src.terms.careers import CareerTerm, ChooseCareerStep, TransitionTerm
from src.terms.context import CareerContext


def _character() -> Character:
    char = Character(name="Test", characteristics={}, skills={})
    for name in (
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    ):
        char.add_characteristic(characteristic=name, value=7)
    char.age = 18
    return char


def test_filesystem_repository_parses_each_career_once(monkeypatch):
    """A career YAML is parsed/validated at most once per repository instance,
    across both load() and get_available() and repeated calls."""
    real_load = repo_mod._load_file
    parsed: list[str] = []

    def counting(path):
        parsed.append(path.stem)
        return real_load(path)

    monkeypatch.setattr(repo_mod, "_load_file", counting)

    repo = FilesystemCareerRepository()
    repo.load("scout")
    repo.load("scout")  # served from cache
    repo.get_available()  # parses the rest once; scout reused from cache
    repo.get_available()  # served from the cached summary list

    assert parsed.count("scout") == 1
    assert parsed.count("army") == 1


def test_career_selection_transition_uses_injected_repository_without_disk(monkeypatch):
    """A career-selection → CareerTerm transition reads the career through an
    in-memory repository and never touches the filesystem loader."""
    scout = load_career("scout")  # one real load, before disk is sealed off
    repo = InMemoryCareerRepository({"scout": scout})

    # Any filesystem parse from here on blows up — proving the transition
    # never reaches disk.
    def _boom(path):
        raise AssertionError(f"unexpected filesystem read: {path}")

    monkeypatch.setattr(repo_mod, "_load_file", _boom)

    char = _character()
    step = ChooseCareerStep(char, [])
    step.outcome = StepOutcome(status="CHOSEN", data={"career": "scout"})
    transition = TransitionTerm(char, step)
    context = CareerContext(character=char, careers=repo)

    nxt = transition.next_term(context)

    assert isinstance(nxt, CareerTerm)
    # Identity: the career came from the injected stub, not a fresh parse.
    assert context.current_career_data is scout
