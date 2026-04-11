from src.terms.base import Step, StepPrompt, StepType, Term
from src.character import Character
from src.utilities import roll


class RollQualificationStep(Step):
    """Roll d6 to see if you qualify for the career."""

    step_id = "roll_qualification"
    step_type = StepType.AUTOMATIC

    def __init__(self, character, test_characteristic: str, target: int):
        super().__init__(character=character)
        self.qualification_characteristic = test_characteristic
        self.qualification_target = target
        self.qualification_modifier = self.character.characteristics[
            test_characteristic
        ].modifier()

    def resolve(self, player_input: dict | None = None) -> None:
        """Roll 2d6 for each characteristic and store the results."""
        self.qualification_roll: int = roll(2) + self.qualification_modifier

    def apply(self) -> None:
        """Determine whether the character qualifies based on the roll."""
        if self.qualification_roll >= self.qualification_target:
            self.qualification_status = "QUALIFIED"
        else:
            self.qualification_status = "FAILED"

    def prompt(self) -> StepPrompt:
        """Determine whether a character qualifies for a career"""
        data = {
            "qualification_characteristic": self.qualification_characteristic,
            "qualification_target": self.qualification_target,
            "qualification_modifier": self.qualification_modifier,
        }
        if hasattr(self, "qualification_roll"):
            data["qualification_roll"] = self.qualification_roll
        if hasattr(self, "qualification_status"):
            data["qualification_status"] = self.qualification_status
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Roll 2d6 for each of the six core characteristics.",
            data=data,
        )


class BasicTrainingStep(Step):
    step_id = "basic_training"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, service_skills: list[str]):
        super().__init__(character=character)
        self.service_skills = service_skills

    def prompt(self) -> StepPrompt:
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Gain basic training skills for the career.",
            data={
                "service_skills": self.service_skills,
            },
        )

    def apply(self) -> None:
        for skill in self.service_skills:
            self.character.add_skill(skill)


class ChooseAssignmentStep(Step):
    """Choose an assignment under the given career."""

    step_id = "choose_assignment"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, assignments: list[str]):
        super().__init__(character=character)
        self.assignments = assignments

    def prompt(self) -> StepPrompt:
        """Return the available assignment options."""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Choose your assignment.",
            options=self.assignments,
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Validate and store the player's assignment selection."""
        if player_input is None:
            raise ValueError("Assignment selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single assignment")
        selected_assignment = selections[0]
        self.selected_assignment: str = selected_assignment


class ChooseCareerSkillsTable(Step):
    """Choose background skills based on the character's Education modifier."""

    step_id = "choose_career_skills_table"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, skill_tables: list[str]):
        super().__init__(character=character)
        self.skill_tables = skill_tables

    def prompt(self) -> StepPrompt:
        """Return the available skill options and required count."""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Choose a skill table to roll on.",
            options=self.skill_tables,
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Validate and store the player's assignment selection."""
        if player_input is None:
            raise ValueError("Assignment selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single skill table.")
        selected_skill_table = selections[0]
        self.selected_skill_table: str = selected_skill_table


class RollForSkillStep(Step):
    step_id = "roll_for_skill"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, skill_options: list[str]):
        super().__init__(character=character)
        self.skill_options = skill_options

    def resolve(self, player_input: dict | None = None) -> None:
        """Roll 2d6 for each characteristic and store the results."""
        self.skill_roll: int = roll(1)
        self.skill: str = self.skill_options[self.skill_roll - 1]

    def apply(self):
        self.character.increment_skill(self.skill, specialty="TODO")

    def prompt(self) -> StepPrompt:
        """Determine whether a character qualifies for a career"""
        data: dict = {
            "skill_options": self.skill_options,
        }
        if hasattr(self, "skill_roll"):
            data["skill_roll"] = self.skill_roll
        if hasattr(self, "skill"):
            data["skill"] = self.skill
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Roll d6 for a skill on the selected skill table.",
            data=data,
        )


class ChooseCareerStep(Step):
    """Present available careers for the player to choose from."""

    step_id = "choose_career"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, careers: list[dict]) -> None:
        super().__init__(character)
        self.careers = careers

    def prompt(self) -> StepPrompt:
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Choose a career to pursue.",
            options=[c["name"] for c in self.careers],
            required_count=1,
            data={"careers": self.careers},
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Career selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single career.")
        self.selected_career: str = selections[0]


class ContinueOrMusterOutStep(Step):
    """Ask whether to continue serving or muster out."""

    step_id = "continue_or_muster_out"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, career_name: str) -> None:
        super().__init__(character)
        self.career_name = career_name

    def prompt(self) -> StepPrompt:
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=f"Your term in the {self.career_name} is complete. Continue serving or muster out?",
            options=["Continue", "Muster Out"],
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Decision is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose one option.")
        self.decision: str = selections[0]


class TransitionTerm(Term):
    """A term containing a single decision step (career choice or muster out)."""

    def __init__(self, character: Character, step: Step) -> None:
        super().__init__(character)
        self.steps = [step]


class CareerTerm(Term):
    """Live through a full career term.

    The progression is dynamic based on results and choices:
    1. First term: Qualify → Basic Training → Choose Assignment → Choose Skill Table → Roll for Skill
       (If qualification fails, the term ends immediately.)
    2. Subsequent terms: Choose Assignment → Choose Skill Table → Roll for Skill
    """

    def __init__(
        self,
        character: Character,
        career_name: str,
        qualification_characteristic: str,
        qualification_target: int,
        service_skills: list[str],
        assignments: list[str],
        skill_tables: dict[str, list[str]],
        is_first_term: bool = True,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.service_skills = service_skills
        self.assignments = assignments
        self.skill_tables = skill_tables

        if is_first_term:
            self.steps = [
                RollQualificationStep(
                    character, qualification_characteristic, qualification_target
                )
            ]
        else:
            self.steps = [ChooseAssignmentStep(character, assignments)]

    def advance(self) -> None:
        """Complete the current step and dynamically append the next steps based on results."""
        step = self.current_step
        super().advance()

        if isinstance(step, RollQualificationStep):
            if step.qualification_status == "QUALIFIED":
                self.steps.append(
                    BasicTrainingStep(self.character, self.service_skills)
                )
                self.steps.append(
                    ChooseAssignmentStep(self.character, self.assignments)
                )

        elif isinstance(step, ChooseAssignmentStep):
            self.steps.append(
                ChooseCareerSkillsTable(self.character, list(self.skill_tables.keys()))
            )

        elif isinstance(step, ChooseCareerSkillsTable):
            skill_options = self.skill_tables[step.selected_skill_table]
            self.steps.append(RollForSkillStep(self.character, skill_options))
