from src.terms.base import Step, StepPrompt, StepType, Term
from src.character import Character
from src.utilities import roll


class RollCharacteristicsStep(Step):
    """Roll 2d6 for each of the six core characteristics."""

    step_id = "roll_characteristics"
    step_type = StepType.AUTOMATIC

    CHARACTERISTIC_NAMES = [
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    ]

    def resolve(self, player_input: dict | None = None) -> None:
        """Roll 2d6 for each characteristic and store the results."""
        self.characteristics: dict[str, int] = {
            name: roll(2) for name in self.CHARACTERISTIC_NAMES
        }

    def apply(self) -> None:
        """Add each rolled characteristic to the character."""
        for characteristic, value in self.characteristics.items():
            self.character.add_characteristic(characteristic=characteristic, value=value)

    def prompt(self) -> StepPrompt:
        """Return rolled characteristic data (called after resolve for auto steps)."""
        data = None
        if hasattr(self, "characteristics"):
            data = {
                "characteristics": {
                    name: {
                        "value": self.character.characteristics[name].value,
                        "modifier": self.character.characteristics[name].modifier(),
                    }
                    for name in self.characteristics
                }
            }
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Roll 2d6 for each of the six core characteristics.",
            data=data,
        )


class ChooseBackgroundSkillsStep(Step):
    """Choose background skills based on the character's Education modifier."""

    step_id = "choose_background_skills"
    step_type = StepType.CHOICE

    SKILL_OPTIONS: list[str] = [
        "Admin",
        "Animals",
        "Art",
        "Athletics",
        "Carouse",
        "Drive",
        "Electronics",
        "Flyer",
        "Language",
        "Mechanic",
        "Medic",
        "Profession",
        "Science",
        "Seafarer",
        "Streetwise",
        "Survival",
        "Vacc Suit",
    ]

    def required_skill_count(self) -> int:
        """Return the number of background skills the player must choose (3 + EDU DM)."""
        education = self.character.characteristics["Education"]
        return 3 + education.modifier()

    def prompt(self) -> StepPrompt:
        """Return the available skill options and required count."""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Choose your background skills.",
            options=self.SKILL_OPTIONS,
            required_count=self.required_skill_count(),
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Validate and store the player's skill selections."""
        if player_input is None:
            raise ValueError("Skill selections are required.")
        selections = player_input.get("selections", [])
        required_choices = self.required_skill_count()
        if len(selections) != required_choices:
            raise ValueError(f"You need to choose exactly {required_choices} skills (3 + EDU DM)!")
        self.selections: list[str] = selections

    def apply(self) -> None:
        """Add each selected skill to the character."""
        for skill in self.selections:
            self.character.add_skill(skill)


class ChildhoodTerm(Term):
    """The childhood term: roll characteristics, then choose background skills."""

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self.steps: list[Step] = [
            RollCharacteristicsStep(self.character),
            ChooseBackgroundSkillsStep(self.character),
        ]
