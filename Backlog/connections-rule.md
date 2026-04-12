# Implement the Connections Rule (multi-character creation)

Per the rules: events can be shared between two Travellers. Both gain one extra free skill of their choice. Max two free skills from connections per Traveller, each with a different partner, cannot raise a skill above 3, and Jack-of-all-Trades is excluded.

The current engine handles a single character per `GameSession` (`src/engine.py:24-28`) with no hook for pairing.

## Scope

- Multi-character session model (or a "create party" wrapper that coordinates multiple `GameSession`s).
- Event comparison step where two players can agree to link an event.
- Per-character counter for connection skills used (max 2).
- Validation: skill cap 3 for connection grants, exclude Jack-of-all-Trades.
- Depends on associates data model (the linked Travellers typically become contacts/allies/rivals of each other).

This is a substantial feature; may be deferred indefinitely for a single-player creator tool.
