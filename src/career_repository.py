"""Career catalogue access, decoupled from storage.

Terms read careers through a ``CareerRepository`` carried on
``CareerContext`` rather than calling the filesystem loader directly. This
decouples the domain layer from disk, lets transitions be exercised against an
in-memory catalogue, and gives a natural cache point: a career YAML is parsed
and validated at most once per repository instance (i.e. once per session)
instead of being re-globbed, re-read, and re-validated on every career-selection
prompt.

The default ``FilesystemCareerRepository`` wraps the existing loader helpers in
``career_loader`` and adds caching; ``InMemoryCareerRepository`` is the test
stub.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.career_data import CareerData
from src.career_loader import DATA_DIR, _load_file


@runtime_checkable
class CareerRepository(Protocol):
    """Read access to the career catalogue.

    Two operations mirror the two loader functions terms used to call:
    a lightweight summary list for selection, and a full validated load.
    """

    def get_available(self) -> list[dict]:
        """Return a ``qualification_summary()`` dict for every known career."""
        ...

    def load(self, name: str) -> CareerData:
        """Return the full, validated ``CareerData`` for ``name``."""
        ...


class FilesystemCareerRepository:
    """Default repository backed by ``data/careers/*.yaml``.

    Each career YAML is parsed and validated at most once per instance. Both
    ``load`` and ``get_available`` populate/read a shared per-name cache (keyed
    by the lowercased filename stem), so a session that re-prompts career
    selection never re-reads or re-validates the catalogue.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir
        self._cache: dict[str, CareerData] = {}
        self._available: list[dict] | None = None

    def load(self, name: str) -> CareerData:
        key = name.lower()
        cached = self._cache.get(key)
        if cached is None:
            cached = _load_file(self._data_dir / f"{key}.yaml")
            self._cache[key] = cached
        return cached

    def get_available(self) -> list[dict]:
        if self._available is None:
            summaries: list[dict] = []
            for path in sorted(self._data_dir.glob("*.yaml")):
                key = path.stem
                career = self._cache.get(key)
                if career is None:
                    career = _load_file(path)
                    self._cache[key] = career
                summaries.append(career.qualification_summary())
            self._available = summaries
        return self._available


class InMemoryCareerRepository:
    """Repository over an in-memory career set — no filesystem access.

    For tests that exercise term transitions without touching disk. Keyed by
    career name (case-insensitive), matching ``FilesystemCareerRepository``.
    """

    def __init__(self, careers: dict[str, CareerData]) -> None:
        self._careers = {name.lower(): data for name, data in careers.items()}

    def load(self, name: str) -> CareerData:
        return self._careers[name.lower()]

    def get_available(self) -> list[dict]:
        return [career.qualification_summary() for career in self._careers.values()]
