# Option to Muster Out on Failed Survival

When a character fails their survival check, they should be given the option to muster out rather than being forced into career selection. Currently, a failed survival roll always routes the character to choose a new career with no muster-out option.

## Current behavior

After a mishap (failed survival), `CareerTerm.next_term()` routes the character directly to `ChooseCareerStep` via a `TransitionTerm`, with no option to collect muster-out benefits and stop.

## Expected behavior

After a failed survival check, the character should be presented with a choice: either select a new career or muster out (collecting benefits for terms served). This is consistent with the Traveller rules where a character can leave creation after any career ends, including involuntary exits.

## Found during

Manual testing (documented in TESTING.md).
