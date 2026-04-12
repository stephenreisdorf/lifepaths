# Citizens and Drifters use Assignment Skills for basic training

Per the rules: "Citizens and Drifters use their Assignment Skills table for basic training instead of Service Skills."

`BasicTrainingStep` (`src/terms/careers.py:52-71`) unconditionally uses `service_skills`.

## Fix

- Special-case Citizen and Drifter in the career loader / `CareerTerm` construction so that basic training draws from the *chosen* assignment's skill table instead.
- Note: this means basic training must run *after* `ChooseAssignmentStep` for these careers, not before — reorder steps for Citizen/Drifter.
