"""tests/test_career_loader.py — career library validation."""
import pytest

from content.careers import get_career, get_careers_for_cell, load_career_library
from content.cells import load_all_cells
from content.models import CareerEntry


def test_career_library_size():
    library = load_career_library()
    assert len(library) >= 40, f"need at least 40 careers, got {len(library)}"


def test_career_entries_validate():
    library = load_career_library()
    for career_id, entry in library.items():
        assert isinstance(entry, CareerEntry)
        assert entry.career_id == career_id


def test_get_career_known():
    c = get_career("data_scientist")
    assert c.career_id == "data_scientist"
    # Should reference at least one major Indian tech company
    assert any(name in c.indian_companies for name in ["Razorpay", "Swiggy", "Flipkart", "Infosys", "TCS", "Cred", "PhonePe"])


def test_get_career_unknown_raises():
    with pytest.raises(KeyError):
        get_career("astronaut_to_mars")


def test_get_careers_for_cell_returns_list():
    """For a known cell, return the careers it points to in priority order."""
    careers = get_careers_for_cell("IA")
    assert len(careers) >= 3
    assert all(isinstance(c, CareerEntry) for c in careers)
    from content.cells import get_cell_content
    expected_first_id = get_cell_content("IA").career_directions[0]
    assert careers[0].career_id == expected_first_id


def test_library_covers_all_cell_career_directions():
    """Every career_id referenced in any cell.career_directions must exist in the library."""
    library = load_career_library()
    library_ids = set(library.keys())
    cells = load_all_cells()
    cell_referenced_ids: set[str] = set()
    for c in cells.values():
        cell_referenced_ids.update(c.career_directions)
    missing = cell_referenced_ids - library_ids
    assert not missing, f"library missing {len(missing)} careers referenced by cells: {sorted(missing)[:10]}..."


def test_library_distribution_across_industries():
    """Sanity check: library should span IT, finance, media, edu, sales, founder, govt, service."""
    library = load_career_library()
    ids = set(library.keys())
    # IT
    assert any(it_id in ids for it_id in ("data_scientist", "software_engineer", "devops_engineer"))
    # Finance
    assert any(fin_id in ids for fin_id in ("financial_analyst", "investment_analyst", "audit_associate"))
    # Media/Arts
    assert any(media_id in ids for media_id in ("screenwriter", "creative_director", "content_creator"))
    # Education
    assert any(edu_id in ids for edu_id in ("school_teacher", "academic_researcher", "education_administrator"))
    # Sales/Ops
    assert any(s_id in ids for s_id in ("sales_manager", "operations_manager", "hr_business_partner"))
    # Entrepreneurship
    assert any(e_id in ids for e_id in ("startup_founder", "founders_office", "family_office_principal"))
    # Government / Public
    assert any(g_id in ids for g_id in ("policy_analyst", "public_administration"))
