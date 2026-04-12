# Track "ejected from career" to bar assignment changes

Per the rules: "You cannot change assignment if you were ejected from the career — no one will hire you."

Nothing in `Character` or `CareerRecord` tracks ejection (mishap-induced career end). `src/engine.py:88-95` routes mishap exits back to career selection without recording why.

## Fix

- Add `ejected: bool = False` to `CareerRecord` (`src/character.py:38-43`).
- Set the flag when a mishap ends the career.
- `assignment-change-flow.md` should check this flag before allowing an assignment change.
