"""tests/test_content_validators.py — cell ↔ career cross-reference integrity."""
from content.validators import (
    find_cells_with_zero_careers,
    find_orphan_career_references,
    find_unknown_cells_in_why_match,
    validate_content_integrity,
)


def test_no_orphan_career_references():
    """Every career_id mentioned in any cell.career_directions exists in the library."""
    orphans = find_orphan_career_references()
    assert orphans == [], f"orphan career references: {orphans[:5]}..."


def test_no_unknown_cells_in_why_match():
    """Every cell mentioned in any career.why_match is a valid 24-cell ID."""
    unknowns = find_unknown_cells_in_why_match()
    assert unknowns == [], f"unknown cell IDs in why_match: {unknowns[:5]}..."


def test_no_cells_with_zero_careers():
    """No cell has empty career_directions (Phase 2.5 hard error)."""
    empty = find_cells_with_zero_careers()
    assert empty == [], f"cells with zero careers: {empty}"


def test_validate_content_integrity_runs_clean():
    """Composite check returning structured results; all green = healthy library."""
    result = validate_content_integrity()
    assert result["orphan_career_refs"] == []
    assert result["unknown_cells_in_why_match"] == []
    assert result["cells_with_zero_careers"] == []


def test_find_dormant_why_match_entries_runs():
    """Dormant entries are informational, not errors. Just verify the function works.

    After Task 6, ~5 careers have why_match cells beyond their listing cells (one-way reference).
    This is intentional dormant content for a future career-detail Path B page.
    """
    from content.validators import find_dormant_why_match_entries
    dormant = find_dormant_why_match_entries()
    assert isinstance(dormant, list)
    for entry in dormant:
        assert isinstance(entry, tuple) and len(entry) == 2
