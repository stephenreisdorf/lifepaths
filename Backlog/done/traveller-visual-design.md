# Traveller Core Rulebook Visual Design

Apply a visual design inspired by the Traveller Core Rulebook Update 2022 to the Vue frontend. Current UI is utilitarian; this would give the app a cohesive sci-fi/TTRPG aesthetic that matches the source material.

## Visual identity

- **Logo/header**: heavy, condensed block sans-serif wordmark in crimson-red gradient (`#C41E3A`) with a silver/white orbit ring accent. SVG for crispness.
- **Sub-branding**: wide letter-spaced, medium-weight sans-serif in white/silver.

## Color palette

| Usage | Name | Hex |
| :--- | :--- | :--- |
| Background (dark) | Deep Space Black | `#050505` |
| Accent (primary CTA) | Imperial Red | `#C41E3A` |
| Interior background | Parchment White | `#FFFFFF` |
| Container background | Tactical Tan | `#F4E9D5` |
| Borders / section accents | Burned Orange | `#D17B47` |
| Body text | Graphite | `#222222` |

## Typography

- **Section titles**: all-caps, condensed sans-serif bold, 1px tracking, `#D17B47`.
- **Category headers**: all-caps, sans-serif semi-bold, `#000000`.
- **Body**: Inter/Helvetica/Roboto, 16px web, 1.4–1.5 line height.
- **Metadata/credits**: 12–14px, standard sans-serif.

## Layout / UI components

- **Chamfered containers**: 1px `#D17B47` border, angled (cut) top-right and bottom-left corners via `clip-path: polygon()` or `border-image`, ~20px internal padding. This is the defining visual element and should wrap step prompts, character sheet sections, and career cards.
- **Tables / contents lists**: two-column flex (title left, value right with dot leader), stack to single column on mobile.
- **Footer**: solid black bar, small centered white sans-serif, optional circular page/step badge.
- **Hover states**: subtle tint or text color shift to Imperial Red for interactive elements.

## Imagery

- Cinematic, high-contrast digital painting style for any hero imagery.
- Background images use `background-size: cover` with a linear gradient overlay to black at the bottom for clean text placement.

## UX considerations

- Responsive: two-column layouts collapse to single column on mobile.
- Optional "Space Mode" dark variant that swaps Parchment White for Deep Space Black and inverts text.
- Keep all text selectable (no text baked into images).
- Ensure sufficient contrast on all color combinations (AA at minimum).

## Scope notes

This is a pure frontend change — no backend or domain model changes. Would likely touch: root `App.vue`, global CSS/theme, every step prompt component, character sheet display, and career selection screens. Could be staged: (1) palette + typography tokens, (2) chamfered container component, (3) logo/header, (4) imagery + polish.
