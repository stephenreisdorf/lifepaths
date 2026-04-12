# Draft and Drifter fallback on failed qualification

`src/engine.py:76-86` routes a failed `RollQualificationStep` straight back to career selection. The rules require offering either:

1. **Draft** — assigned randomly to a military career via a 1d6 table (once per lifetime).
2. **Drifter** — always available.

## Scope

- Add a `draft_used: bool = False` flag on `Character` (or track on `GameSession`).
- After a failed qualification, insert a `ChooseDraftOrDrifterStep` (or similar).
- Implement the Draft 1d6 table: `1 Navy, 2 Army, 3 Marine, 4 Merchant (Merchant Marine), 5 Scout (any), 6 Agent (Law Enforcement)`.
- Depends on the Drifter career being available in the loader.
