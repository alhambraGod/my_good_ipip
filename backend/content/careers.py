"""Career library loader — single JSON file with all career stubs.

Uses MappingProxyType for read-only safety (consistent with content/cells.py pattern).
Cross-reference integrity (cell↔career) is enforced by tests in this module + Task 5 validators.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from content.models import CareerEntry

_HERE = Path(__file__).resolve().parent
LIBRARY_PATH = _HERE / "data" / "careers" / "library.json"


@lru_cache(maxsize=1)
def _library_cache() -> dict[str, CareerEntry]:
    """Internal: load + cache the career library. Use load_career_library() externally."""
    with open(LIBRARY_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    library: dict[str, CareerEntry] = {}
    for career_id, entry_dict in raw.items():
        if "career_id" not in entry_dict:
            entry_dict = {**entry_dict, "career_id": career_id}
        library[career_id] = CareerEntry.model_validate(entry_dict)
    return library


def load_career_library() -> Mapping[str, CareerEntry]:
    """Return the read-only mapping of {career_id: CareerEntry}."""
    return MappingProxyType(_library_cache())


def get_career(career_id: str) -> CareerEntry:
    """Look up a single career. Raises KeyError if not in the library."""
    library = _library_cache()
    if career_id not in library:
        raise KeyError(f"unknown career: {career_id!r}; check content/data/careers/library.json")
    return library[career_id]


def get_careers_for_cell(cell_id: str) -> list[CareerEntry]:
    """Return the ordered list of CareerEntry objects for a cell's career_directions."""
    from content.cells import get_cell_content

    cell = get_cell_content(cell_id)
    return [get_career(cid) for cid in cell.career_directions]
