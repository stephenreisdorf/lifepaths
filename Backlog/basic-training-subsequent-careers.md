# Basic Training on subsequent careers

Per the rules: "Subsequent careers: pick any one Service Skills table skill at level 0."

`CareerTerm.__init__` (`src/terms/careers.py:472-479`) goes straight to `ChooseAssignmentStep` on non-first terms, skipping Basic Training entirely for any career after the first.

Note: this hinges on "first career *ever*" vs. "first term of *this* career." The `is_first_term` flag in `CareerTerm` currently tracks the latter. The rule actually distinguishes:

- First career ever → gain *all* Service Skills at 0.
- Subsequent careers (first term of a new career, but not the character's first career) → pick *one* Service Skill at 0.
- Continuing terms in an existing career → no basic training.

## Fix

- Distinguish "first career ever" from "first term of this career" — track on `Character` or `GameSession`.
- Add a `PickServiceSkillStep` (StepType.CHOICE) that offers the service_skills list for new-but-not-first careers.
- Wire into `CareerTerm` construction / `advance()`.
