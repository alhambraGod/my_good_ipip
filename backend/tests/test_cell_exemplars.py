"""tests/test_cell_exemplars.py — verify hand-curated exemplars meet quality bar."""
from content.cells import get_cell_content


EXEMPLAR_CELLS = ["IA", "SE", "EC", "SC"]


def test_exemplars_have_no_placeholder_text():
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        for field_value in [c.core_insight_en, c.deep_description_en]:
            assert "PLACEHOLDER" not in field_value, f"{cell_id} still has PLACEHOLDER text in content"


def test_exemplars_have_full_ocean_modifiers():
    """Exemplars should populate at least 4 OCEAN modifiers (gold standard for content authors)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        modifiers_set = sum(
            1 for v in c.ocean_modifiers.model_dump().values() if v is not None
        )
        assert modifiers_set >= 4, f"{cell_id} only has {modifiers_set} ocean_modifiers; exemplars need >=4"


def test_exemplars_have_unique_share_lines():
    """Exemplars should have ≥3 unique share copy lines (gold standard)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert len(c.share_lines_en) >= 3, f"{cell_id} has only {len(c.share_lines_en)} share_lines_en"
        assert len(set(c.share_lines_en)) == len(c.share_lines_en), f"{cell_id} has duplicate share_lines_en"


def test_exemplars_deep_description_min_length():
    """Exemplars should have a real-length deep description (≥1500 chars / ~250 words)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert len(c.deep_description_en) >= 1500, (
            f"{cell_id} deep_description is only {len(c.deep_description_en)} chars; needs >=1500"
        )
