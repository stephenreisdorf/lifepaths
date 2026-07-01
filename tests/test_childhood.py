from src.character import Character
from src.terms.childhood import (
    ChildhoodTerm,
    ChooseBackgroundSkillsStep,
    RollCharacteristicsStep,
)


def test_full_childhood_run(seeded_rng):
    char = Character(name="Test", characteristics={}, skills={})
    term = ChildhoodTerm(char)

    # Step 1: roll characteristics.
    assert isinstance(term.current_step, RollCharacteristicsStep)
    term.submit()
    for name in RollCharacteristicsStep.CHARACTERISTIC_NAMES:
        assert name in char.characteristics
        assert 2 <= char.characteristics[name].value <= 12

    # Step 2: choose background skills (3 + EDU DM of them).
    step = term.current_step
    assert isinstance(step, ChooseBackgroundSkillsStep)
    count = step.required_skill_count()
    selections = ChooseBackgroundSkillsStep.SKILL_OPTIONS[:count]
    term.submit({"selections": selections})

    for skill in selections:
        assert char.has_skill(skill)
    assert term.current_step is None
