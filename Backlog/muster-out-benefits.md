# Add Benefits / muster-out rolls

Per the rules: on leaving a career, the Traveller collects Benefit rolls. Currently `ContinueOrMusterOutStep` in `src/terms/careers.py:391-416` ends character creation when the player picks "Muster Out" (engine.py:73) with no benefits applied.

## Scope

- Load a career's benefits table (cash column + benefits column) from YAML.
- On muster-out, grant one benefit roll per term served (plus any rank bonuses per the rules).
- Add a `MusterOutStep` that presents cash-vs-benefit choices to the player.
- Handle "lose the Benefit roll for this term" on mishap (ties into mishap implementation).
- Benefit effects (skills, characteristic bumps, gear/ship shares, SOC bumps) need to apply to the character.
