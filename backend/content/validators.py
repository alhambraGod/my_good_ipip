"""Cross-reference integrity checks for cell + career content.

Used by Task 5's tests to ensure every cell.career_directions points to a real
career, and every career.why_match references a valid 24-cell ID. These checks
run at test time (catching authoring errors) and can also be invoked at startup
or admin-script time for production sanity.

Design note — one-way cell↔career references:
    `cell.career_directions` is the canonical "careers to surface for this archetype" list
    (Path A — the spec's main user-facing render). `career.why_match` provides per-cell
    match copy WHEN that path renders this career.

    `why_match` MAY contain extra cell IDs beyond the cells that list this career — these
    are 'dormant content' (see find_dormant_why_match_entries) reserved for a future
    career-detail browse page (Path B) that doesn't exist in v1. Bidirectional symmetry
    is NOT enforced by validators; only the v1 minimum-symmetry rule (every cell that
    lists a career has a why_match string for that career) is enforced via the loader's
    behavior + the existing validators.
"""

from __future__ import annotations

from content.careers import load_career_library
from content.cells import load_all_cells
from services.scoring.archetype import VALID_CELLS_24

__all__ = [
    "find_orphan_career_references",
    "find_unknown_cells_in_why_match",
    "find_cells_with_zero_careers",
    "find_dormant_why_match_entries",
    "validate_content_integrity",
]


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


def find_dormant_why_match_entries() -> list[tuple[str, str]]:
    """Return (career_id, cell_id) pairs where why_match has the cell but cell.career_directions
    does NOT list this career.

    These entries are 'dormant content' — present in the data, but not surfaced by the spec's
    Path A (cell.career_directions → render careers with why_match strings). They are reserved
    for a future career-detail browse page (Path B) that doesn't exist in v1.

    This is INFORMATIONAL, not an error. Validators do not assert on this — it's exposed for
    admin scripts and content authors to introspect coverage.
    """
    cells = load_all_cells()
    library = load_career_library()

    surfacing_cells: dict[str, set[str]] = {cid: set() for cid in library.keys()}
    for cell_id, c in cells.items():
        for career_id in c.career_directions:
            if career_id in surfacing_cells:
                surfacing_cells[career_id].add(cell_id)

    dormant: list[tuple[str, str]] = []
    for career_id, entry in library.items():
        listed_in = surfacing_cells.get(career_id, set())
        for cell_id in entry.why_match.keys():
            if cell_id not in listed_in:
                dormant.append((career_id, cell_id))
    return dormant


def validate_content_integrity() -> dict:
    """Composite integrity check; returns structured results for admin scripts.

    The ``dormant_why_match_entries`` key is INFORMATIONAL (not an error) — see
    ``find_dormant_why_match_entries`` for the design rationale.
    """
    return {
        "orphan_career_refs": find_orphan_career_references(),
        "unknown_cells_in_why_match": find_unknown_cells_in_why_match(),
        "cells_with_zero_careers": find_cells_with_zero_careers(),
        "dormant_why_match_entries": find_dormant_why_match_entries(),
    }
