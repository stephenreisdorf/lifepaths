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
        """Describe the qualification check, reflecting the outcome once resolved."""
        if hasattr(self, "qualification_status"):
            description = (
                f"Qualification check on {self.qualification_characteristic}: "
                f"rolled {self.qualification_roll} vs target "
                f"{self.qualification_target} — {self.qualification_status}."
            )
        else:
            description = (
                f"Qualification check: 2d6 + {self.qualification_modifier} DM "
                f"on {self.qualification_characteristic} vs "
                f"{self.qualification_target}."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
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
            description=(
                f"Gained basic training skills: {', '.join(self.service_skills)}."
            ),
        )

    def apply(self) -> None:
        for skill in self.service_skills:
            self.character.add_skill(skill)


class ChooseAssignmentStep(Step):
    """Choose an assignment under the given career."""

    step_id = "choose_assignment"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, assignments: list[dict]):
        super().__init__(character=character)
        self.assignments = assignments

    def prompt(self) -> StepPrompt:
        """Return the available assignment options."""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Choose your assignment.",
            options=[a["name"] for a in self.assignments],
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Validate and store the player's assignment selection."""
        if player_input is None:
            raise ValueError("Assignment selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single assignment")
        selected_name = selections[0]
        matching = [a for a in self.assignments if a["name"] == selected_name]
        if not matching:
            raise ValueError(f"Unknown assignment: {selected_name}")
        self.selected_assignment: dict = matching[0]


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
        """Describe the skill roll, reflecting the outcome once resolved."""
        if hasattr(self, "skill"):
            description = (
                f"Rolled a {self.skill_roll} on the skill table — "
                f"gained {self.skill}."
            )
        else:
            description = "Roll d6 for a skill on the selected skill table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class SurvivalCheckStep(Step):
    """Roll 2d6 + DM vs the assignment's survival target."""

    step_id = "survival_check"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, assignment: dict) -> None:
        super().__init__(character=character)
        self.assignment = assignment
        survival = assignment["survival"]
        self.survival_characteristic: str = survival["characteristic"]
        self.survival_target: int = survival["target"]
        self.survival_modifier: int = character.characteristics[
            self.survival_characteristic
        ].modifier()

    def resolve(self, player_input: dict | None = None) -> None:
        self.survival_roll: int = roll(2) + self.survival_modifier

    def apply(self) -> None:
        if self.survival_roll >= self.survival_target:
            self.survival_status = "SURVIVED"
        else:
            self.survival_status = "FAILED"

    def prompt(self) -> StepPrompt:
        if hasattr(self, "survival_status"):
            description = (
                f"Survival check on {self.survival_characteristic}: "
                f"rolled {self.survival_roll} vs target "
                f"{self.survival_target} — {self.survival_status}."
            )
        else:
            description = (
                f"Survival check: 2d6 + {self.survival_modifier} DM on "
                f"{self.survival_characteristic} vs {self.survival_target}."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class MishapRollStep(Step):
    """Roll d6 on the career's mishap table. Flavor text only — no mechanical effects applied."""

    step_id = "mishap_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, mishaps: dict) -> None:
        super().__init__(character=character)
        self.mishaps = mishaps

    def resolve(self, player_input: dict | None = None) -> None:
        self.mishap_roll: int = roll(1)
        self.mishap_text: str = str(self.mishaps.get(self.mishap_roll, "")).strip()

    def apply(self) -> None:
        # Flavor-only for now; effects are not auto-applied.
        pass

    def prompt(self) -> StepPrompt:
        if hasattr(self, "mishap_text"):
            description = (
                f"Mishap! Rolled {self.mishap_roll}: {self.mishap_text} "
                "Your career ends."
            )
        else:
            description = "Roll d6 on the mishap table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class EventsRollStep(Step):
    """Roll 2d6 on the career's events table. Flavor text only — no mechanical effects applied."""

    step_id = "events_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, events: dict) -> None:
        super().__init__(character=character)
        self.events = events

    def resolve(self, player_input: dict | None = None) -> None:
        self.event_roll: int = roll(2)
        self.event_text: str = str(self.events.get(self.event_roll, "")).strip()

    def apply(self) -> None:
        # Flavor-only for now; effects are not auto-applied.
        pass

    def prompt(self) -> StepPrompt:
        if hasattr(self, "event_text"):
            description = f"Event (2d6 = {self.event_roll}): {self.event_text}"
        else:
            description = "Roll 2d6 on the events table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class AdvancementRollStep(Step):
    """Roll 2d6 + DM vs the assignment's advancement target. On success, promote and apply rank bonus."""

    step_id = "advancement_roll"
    step_type = StepType.AUTOMATIC

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment: dict,
        ranks: list[dict],
    ) -> None:
        super().__init__(character=character)
        self.career_name = career_name
        self.assignment = assignment
        self.ranks = ranks
        advancement = assignment["advancement"]
        self.advancement_characteristic: str = advancement["characteristic"]
        self.advancement_target: int = advancement["target"]
        self.advancement_modifier: int = character.characteristics[
            self.advancement_characteristic
        ].modifier()

    def resolve(self, player_input: dict | None = None) -> None:
        self.advancement_roll: int = roll(2) + self.advancement_modifier

    def apply(self) -> None:
        # Always tick terms_served at the end of a successful term.
        self.character.record_career_term(self.career_name)

        if self.advancement_roll >= self.advancement_target:
            record = self.character.promote(self.career_name)
            self.advancement_status = "PROMOTED"
            self.new_rank_title: str | None = self._apply_rank_bonus(record.rank)
        else:
            self.advancement_status = "NOT_PROMOTED"
            self.new_rank_title = None

    def _apply_rank_bonus(self, new_rank: int) -> str | None:
        """Find the rank entry for new_rank, apply any bonus skill/characteristic, return the title."""
        entry = next((r for r in self.ranks if r.get("rank") == new_rank), None)
        if entry is None:
            return None
        bonus = entry.get("bonus_skill")
        if bonus:
            self._apply_bonus(bonus)
        return entry.get("title")

    def _apply_bonus(self, bonus: str) -> None:
        """Apply a rank bonus. '<Name> +<N>' against a known characteristic bumps it; otherwise add as a skill."""
        parts = bonus.rsplit(" +", 1)
        if len(parts) == 2 and parts[1].isdigit():
            name, delta = parts[0], int(parts[1])
            if name in self.character.characteristics:
                current = self.character.characteristics[name].value
                self.character.add_characteristic(name, current + delta)
                return
        self.character.add_skill(bonus)

    def prompt(self) -> StepPrompt:
        if hasattr(self, "advancement_status"):
            outcome = (
                f"PROMOTED to {self.new_rank_title}"
                if self.advancement_status == "PROMOTED" and self.new_rank_title
                else self.advancement_status
            )
            description = (
                f"Advancement check on {self.advancement_characteristic}: "
                f"rolled {self.advancement_roll} vs target "
                f"{self.advancement_target} — {outcome}."
            )
        else:
            description = (
                f"Advancement check: 2d6 + {self.advancement_modifier} DM on "
                f"{self.advancement_characteristic} vs {self.advancement_target}."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
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

    def label(self) -> str:
        inner = self.steps[0]
        if isinstance(inner, ChooseCareerStep):
            return "Career Selection"
        if isinstance(inner, ContinueOrMusterOutStep):
            return f"{inner.career_name} — Term End"
        return "Transition"


class CareerTerm(Term):
    """Live through a full career term.

    The progression is dynamic based on results and choices:
    1. First term: Qualify → Basic Training → Choose Assignment
       (If qualification fails, the term ends immediately. No skill roll on
       the first term — basic training is the only skill grant.)
    2. Subsequent terms: Choose Assignment → Choose Skill Table → Roll for Skill
    """

    def __init__(
        self,
        character: Character,
        career_name: str,
        qualification_characteristic: str,
        qualification_target: int,
        service_skills: list[str],
        assignments: list[dict],
        skill_tables: dict[str, list[str]],
        events: dict | None = None,
        mishaps: dict | None = None,
        ranks: list[dict] | None = None,
        is_first_term: bool = True,
        term_number: int = 1,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.service_skills = service_skills
        self.assignments = assignments
        self.skill_tables = skill_tables
        self.events = events or {}
        self.mishaps = mishaps or {}
        self.ranks = ranks or []
        self.is_first_term = is_first_term
        self.term_number = term_number
        self._selected_assignment: dict | None = None

        if is_first_term:
            self.steps = [
                RollQualificationStep(
                    character, qualification_characteristic, qualification_target
                )
            ]
        else:
            self.steps = [ChooseAssignmentStep(character, assignments)]

    def label(self) -> str:
        return f"{self.career_name} — Term {self.term_number}"

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
            self._selected_assignment = step.selected_assignment
            if self.is_first_term:
                self.steps.append(
                    SurvivalCheckStep(self.character, self._selected_assignment)
                )
            else:
                self.steps.append(
                    ChooseCareerSkillsTable(self.character, list(self.skill_tables.keys()))
                )

        elif isinstance(step, ChooseCareerSkillsTable):
            skill_options = self.skill_tables[step.selected_skill_table]
            self.steps.append(RollForSkillStep(self.character, skill_options))

        elif isinstance(step, RollForSkillStep):
            self.steps.append(
                SurvivalCheckStep(self.character, self._selected_assignment)
            )

        elif isinstance(step, SurvivalCheckStep):
            if step.survival_status == "SURVIVED":
                self.steps.append(EventsRollStep(self.character, self.events))
                self.steps.append(
                    AdvancementRollStep(
                        self.character,
                        self.career_name,
                        self._selected_assignment,
                        self.ranks,
                    )
                )
            else:
                self.steps.append(MishapRollStep(self.character, self.mishaps))
