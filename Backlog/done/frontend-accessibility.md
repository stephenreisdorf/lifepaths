# Accessibility gaps: color-only status, missing ARIA state, no focus management

Several states are conveyed by color alone, selection state isn't exposed to assistive tech, and focus is never moved as the flow advances. Screen-reader and keyboard-only users, and anyone with a color-vision deficiency, lose information.

## Problem

- **Color-only pass/fail.** `CreationScreen.vue:117-135` recolors the review-card frame green/red/orange by status (`PASSED`/`FAILED`/`MISHAP`/…) with no text label or icon. A red vs green frame is the only signal that a roll succeeded or failed.
- **Selection not exposed.** `SkillGrid.vue` toggles a `.selected` class (red background) but sets no `aria-pressed`. Screen readers can't tell which skills are chosen.
- **No focus management.** `App.vue` swaps the prompt each submit, but focus stays on the just-clicked button. Keyboard/SR users get no announcement and must hunt for the new step.

## Opportunity

- Add a text/icon status badge to the review card (e.g. "✓ Survived" / "✗ Mishap") so status isn't color-only.
- Set `:aria-pressed="selected.has(skill)"` on skill buttons; consider `role`/`aria-live` on the selection counter.
- Move focus (or an `aria-live` announcement) to the new prompt heading after each transition.

## Done when

- [ ] Roll outcomes are distinguishable without relying on color.
- [ ] Skill selection state is programmatically exposed (`aria-pressed` or equivalent).
- [ ] Advancing a step moves focus / announces the new prompt to assistive tech.

## Notes

Frontend only. Independent of the other UX items but touches the same components.
