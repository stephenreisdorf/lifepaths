# Aging rules

Traveller career terms are four years each, and RAW includes aging rolls (typically from age 34 onward) that can damage physical characteristics. The codebase has no aging mechanic: no `age` on `Character`, no aging step in `CareerTerm`.

## Scope

- Add `age: int` to `Character` (starts at 18 after childhood, +4 per completed term).
- Add an `AgingStep` that runs per term past the threshold (rules-dependent: 34, 50, 66, 74).
- Apply characteristic damage based on the aging table.
- Consider medical debt / anagathics rules if in scope.

Out of scope of the current rules excerpt but implied by the four-year-term mechanic — confirm with the user whether this should be tracked here or in a separate rules chapter.
