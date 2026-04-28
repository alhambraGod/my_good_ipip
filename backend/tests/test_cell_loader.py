"""tests/test_cell_loader.py — verify all 24 cell content files load + validate."""
import pytest

from content.cells import CELLS_DIR, get_cell_content, load_all_cells
from content.models import CellContent
from services.scoring.archetype import VALID_CELLS_24


def test_all_24_cells_have_files():
    cells = load_all_cells()
    assert len(cells) == 24
    for cell_id in VALID_CELLS_24:
        assert cell_id in cells, f"missing content for {cell_id}"


def test_all_cells_validate_against_schema():
    cells = load_all_cells()
    for cell_id, content in cells.items():
        assert isinstance(content, CellContent)
        assert content.cell == cell_id


def test_get_cell_content_known_cell():
    c = get_cell_content("IA")
    assert c.cell == "IA"
    assert len(c.strengths_en) == 5
    assert len(c.growth_tips_en) == 5


def test_get_cell_content_unknown_raises():
    with pytest.raises(KeyError):
        get_cell_content("XX")


def test_no_orphan_cell_files():
    """No JSON file in data/cells/ that isn't one of the 24 valid cells."""
    files = {p.stem for p in CELLS_DIR.glob("*.json")}
    assert files == set(VALID_CELLS_24), f"orphan or missing files: {files ^ set(VALID_CELLS_24)}"
