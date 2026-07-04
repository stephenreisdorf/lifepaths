# Anagathics rule is implemented but unreachable from the UI

The backend supports starting a session with the anti-aging (anagathics) rule enabled, but the frontend always starts with it off. An entire modelled game mechanic can't be turned on by a player.

## Problem

`src/api.py:22-33`: `StartRequest.anagathics_enabled: bool = False` is a real option honoured by `GameSession`. But `frontend/src/App.vue:17` calls `fetch('/api/start', { method: 'POST' })` with **no request body**, so `anagathics_enabled` is always the default `False`. The `WelcomeScreen` offers no settings — just a single "Begin" button — so the rule is dead UI.

## Opportunity

- Add an "Enable anagathics (anti-aging drugs)" toggle to the welcome screen.
- Pass it through `startCreation()` as a JSON body: `POST /api/start` with `{ anagathics_enabled }` and the `Content-Type: application/json` header.

## Done when

- [ ] The welcome screen exposes the anagathics option (with a one-line explanation).
- [ ] The choice is sent to `/api/start` and observably changes the run (the anagathics start-of-term step appears).

## Notes

Frontend + a one-line body change. This is the natural place to add future start-of-session options too.
