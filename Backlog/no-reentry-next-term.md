# "Cannot re-enter same career next term" rule not enforced

After mustering out or a mishap, `ChooseCareerStep` offers all careers (`src/engine.py:83-95` builds from `get_available_careers()` unconditionally). The rules forbid returning to a career in the immediately-following term.

## Fix

Track the most-recently-left career on `GameSession` (or `Character`). When building the next `ChooseCareerStep`, filter it out of the options. Clear the block after one term has passed.
