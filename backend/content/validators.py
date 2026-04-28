"""Cross-reference integrity checks for cell + career content.

Used by Task 5's tests to ensure every cell.career_directions points to a real
career, and every career.why_match references a valid 24-cell ID. These checks
run at test time (catching authoring errors) and can also be invoked at startup
or admin-script time for production sanity.
"""

from __future__ import annotations

from content.careers import load_career_library
from content.cells import load_all_cells
from services.scoring.archetype import VALID_CELLS_24


def find_orphan_career_references() -> list[tuple[str, str]]:
    """Return [(cell_id, career_id)] tuples where career_id is not in the library.

    A non-empty result means a cell references a career that doesn't exist.
    Phase 2 stub-quality bar requires this list to be empty.
    """
    cells = load_all_cells()
    library = load_career_library()
    library_ids = set(library.keys())
    orphans: list[tuple[str, str]] = []
    for cell_id, cell in cells.items():
        for career_id in cell.career_directions:
            if career_id not in library_ids:
                orphans.append((cell_id, career_id))
    return orphans


def find_unknown_cells_in_why_match() -> list[tuple[str, str]]:
    """Return [(career_id, cell_id)] tuples where why_match references a non-24-cell.

    The CellId schema regex catches format errors at parse time; this catches
    *unknown* (typo'd) but format-valid cell IDs (e.g. `RR`, `IE` — not in the 24).
    """
    library = load_career_library()
    valid = set(VALID_CELLS_24)
    unknowns: list[tuple[str, str]] = []
    for career_id, entry in library.items():
        for cell_id in entry.why_match.keys():
            if cell_id not in valid:
                unknowns.append((career_id, cell_id))
    return unknowns


def find_cells_with_zero_careers() -> list[str]:
    """Return cell_ids whose career_directions is empty (Phase 2.5 hard error)."""
    cells = load_all_cells()
    return [cell_id for cell_id, c in cells.items() if not c.career_directions]


def validate_content_integrity() -> dict:
    """Composite integrity check; returns structured results for admin scripts."""
    return {
        "orphan_career_refs": find_orphan_career_references(),
        "unknown_cells_in_why_match": find_unknown_cells_in_why_match(),
        "cells_with_zero_careers": find_cells_with_zero_careers(),
    }
