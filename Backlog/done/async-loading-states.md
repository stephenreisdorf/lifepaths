# No loading state or double-submit guard on async actions

Every server round-trip (`startCreation`, `submit`) is an `await fetch(...)` with no visible pending state and no guard against re-entry. On a slow response the UI looks frozen; a second click before the first resolves fires a duplicate request.

## Problem

`frontend/src/App.vue:15-75`: `startCreation()` and `submit()` await the fetch but never disable the triggering control or show progress. The Confirm/Continue/Begin buttons stay enabled and re-clickable while a request is in flight. A double-click on "Continue" can submit the same step twice (advancing the engine an extra step), and there is no spinner/skeleton so the app appears unresponsive on latency.

## Opportunity

- Track an `inFlight` (or `busy`) ref; disable the active button and/or show a pending indicator while a request is outstanding.
- Ignore/prevent submits while `inFlight` is true.

## Done when

- [ ] Buttons that trigger a fetch are disabled (or show a spinner) until it resolves.
- [ ] A rapid double-click cannot submit the same step twice.
- [ ] The pending state is visible enough that the user knows the app is working.

## Notes

Frontend only. Pairs naturally with [[network-error-handling]] (reset `inFlight` in a `finally`).
