# Network and non-OK responses break the UI silently

`startCreation()` has no error handling at all, and neither path recovers from a failed `fetch`. If the backend is down, returns a 500, or sends a non-JSON body, the app throws an uncaught promise rejection and the user is left on a dead screen with no message.

## Problem

`frontend/src/App.vue:15-26`: `startCreation()` calls `await fetch('/api/start')` then `res.json()` with **no `res.ok` check and no try/catch**. A 500 or a network failure throws and nothing is shown. `submit()` (`:45-75`) checks `res.ok` and reads `err.detail`, but (a) a rejected `fetch` (server unreachable) is still uncaught, and (b) `await res.json()` on a non-JSON error body throws. The `error` ref is the only user-facing channel and it isn't populated on these failures.

## Opportunity

- Wrap both fetch flows in try/catch; on failure set a user-visible `error` message ("Couldn't reach the server — try again").
- Guard `res.ok` on start as well as submit; tolerate non-JSON error bodies.
- Surface the error on the welcome screen too (start failures currently have nowhere to show).

## Done when

- [ ] A backend that is down / returns 500 shows a readable error instead of a blank or frozen screen.
- [ ] `res.json()` is never called on a body that might not be JSON without a guard.
- [ ] Start-phase errors are visible to the user (not just console).

## Notes

Frontend only. Best done alongside [[async-loading-states]] so the busy flag is cleared in `finally`.
