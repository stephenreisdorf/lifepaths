# Automatic Steps Should Show Feedback Before Advancing

Automatic steps (e.g., automatic rolls) currently resolve silently and immediately present the next step. The user sees no indication of what happened unless they check the step log. This creates a confusing experience where results appear to be skipped.

## Current behavior

The engine auto-advances through consecutive automatic steps in `GameSession.submit()`, collecting their prompts in `SubmitResult.resolved_steps`. The frontend does not pause to show the user what occurred — it jumps straight to the next interactive step.

## Expected behavior

Even for automatic steps, the user should see what is about to happen, be given a button to proceed (e.g., "Roll" or "Continue"), and then see the result before the next step is presented. This turns automatic steps into "confirm to proceed" steps from a UX perspective while keeping the domain logic unchanged.

## Scope

This is primarily a frontend/UX change. Options include:

- Converting automatic steps to a lightweight interactive mode in the frontend (step through `resolved_steps` one at a time with a "Continue" button).
- Alternatively, changing the engine to not auto-advance, requiring a submit for each automatic step.

## Found during

Manual testing (documented in TESTING.md).
