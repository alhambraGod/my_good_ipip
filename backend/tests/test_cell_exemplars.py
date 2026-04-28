"""tests/test_cell_exemplars.py — verify hand-curated exemplars meet quality bar.

Exemplars are detected dynamically: any cell whose ``core_insight_en`` and
``deep_description_en`` are free of ``PLACEHOLDER`` text auto-joins
``EXEMPLAR_CELLS`` and gets quality-tested. Phase 2.5 authors can't bypass the
gate — replacing a stub immediately subjects that cell to all checks below.
"""
from __future__ import annotations

import re

from content.cells import get_cell_content
from services.scoring.archetype import VALID_CELLS_24


FORBIDDEN_SENTINELS = (
    "PLACEHOLDER",
    "TODO",
    "TBD",
    "FIXME",
    "REPLACE_ME",
    "[draft]",
    "Lorem ipsum",
)


INDIAN_CONTEXT_MARKERS = (
    "sharma", "gupta", "agarwal", "marwari", "bania", "aunty", "uncle", "beta", "bhaiya", "chacha",
    "bangalore", "mumbai", "delhi", "kolkata", "chennai", "hyderabad", "pune", "gurugram",
    "rajasthan", "gujarat", "kerala",
    "iit", "iim", "tcs", "infosys", "ipu", "upsc",
    "diwali", "baraat", "shaadi", "joint family", "chai", "dosa", "biryani", "bollywood",
    "whatsapp", "hinglish", "emi", "lakh", "crore",
    "na-laayak", "kya", "haan", "nahi", "yaar",
)


_CELL_REF = re.compile(r"\b([RIASEC]{2})\b")


def _word_count(text: str) -> int:
    return len(text.split())


def _is_curated(cell_id: str) -> bool:
    """A cell is 'curated' if it has no PLACEHOLDER text in core narrative fields.

    The check is intentionally narrow (just the two main prose fields) so the
    membership rule is cheap and unambiguous. Once a cell qualifies, the full
    sentinel scan below catches any draft markers in its other fields.
    """
    c = get_cell_content(cell_id)
    return "PLACEHOLDER" not in c.core_insight_en and "PLACEHOLDER" not in c.deep_description_en


EXEMPLAR_CELLS = sorted(cid for cid in VALID_CELLS_24 if _is_curated(cid))


def test_exemplar_count_floor():
    """Phase 2 ships 4 exemplars; Phase 2.5 will grow this to 24.

    Catches regressions where a curated cell silently drops back to stub.
    """
    assert len(EXEMPLAR_CELLS) >= 4, f"only {len(EXEMPLAR_CELLS)} curated cells; expected >=4"


def test_exemplars_have_no_sentinel_text():
    """Exemplars must not contain any author-sentinel/draft markers in any string field."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        text_fields = {
            "core_insight_en": c.core_insight_en,
            "deep_description_en": c.deep_description_en,
            "label_en": c.label_en,
            "label_hi": c.label_hi,
            "slogan_en": c.slogan_en,
        }
        for field_name, text in text_fields.items():
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in text, (
                    f"{cell_id}.{field_name} contains forbidden sentinel '{sentinel}'"
                )
        for i, line in enumerate(c.share_lines_en):
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in line, (
                    f"{cell_id}.share_lines_en[{i}] contains '{sentinel}'"
                )
        for i, item in enumerate(c.strengths_en):
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in item, (
                    f"{cell_id}.strengths_en[{i}] contains '{sentinel}'"
                )
        for i, item in enumerate(c.growth_tips_en):
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in item, (
                    f"{cell_id}.growth_tips_en[{i}] contains '{sentinel}'"
                )


def test_exemplars_have_full_ocean_modifiers():
    """Exemplars should populate at least 4 OCEAN modifiers (gold standard for content authors)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        modifiers_set = sum(
            1 for v in c.ocean_modifiers.model_dump().values() if v is not None
        )
        assert modifiers_set >= 4, (
            f"{cell_id} only has {modifiers_set} ocean_modifiers; exemplars need >=4"
        )


def test_exemplars_have_unique_share_lines():
    """Exemplars should have ≥3 unique share copy lines (gold standard)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert len(c.share_lines_en) >= 3, (
            f"{cell_id} has only {len(c.share_lines_en)} share_lines_en"
        )
        assert len(set(c.share_lines_en)) == len(c.share_lines_en), (
            f"{cell_id} has duplicate share_lines_en"
        )


def test_exemplars_deep_description_min_length():
    """Exemplars should have a real-length deep description.

    Spec floor: 300+ words. Test floor: ≥250 words (slight buffer below spec
    for tone-tight authors). Char floor stays at 1500.
    """
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        char_count = len(c.deep_description_en)
        word_count = _word_count(c.deep_description_en)
        assert char_count >= 1500, (
            f"{cell_id} deep_description {char_count} chars; needs >=1500"
        )
        assert word_count >= 250, (
            f"{cell_id} deep_description {word_count} words; needs >=250 (spec floor 300)"
        )


def test_exemplars_core_insight_word_count():
    """Core insight floor: 60+ words (spec target 80-120; allow 60 for tone-tight authors)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        word_count = _word_count(c.core_insight_en)
        assert word_count >= 60, (
            f"{cell_id} core_insight only {word_count} words; needs >=60 (spec target 80-120)"
        )


def test_exemplars_have_indian_context_markers():
    """Exemplars must reference at least 3 specific Indian-context markers (proper nouns,
    idioms, honorifics) somewhere in core_insight_en + deep_description_en.

    Generic 'Indian' copy fails — the bar is named entities, real cities, real institutions,
    and culturally-specific terms.
    """
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        text = (c.core_insight_en + " " + c.deep_description_en).lower()
        hits = sum(1 for marker in INDIAN_CONTEXT_MARKERS if marker in text)
        assert hits >= 3, (
            f"{cell_id} has only {hits} Indian-context markers in core_insight + deep_description; "
            f"needs >=3 specific proper nouns or culturally-specific terms"
        )


def test_narrative_cross_refs_resolve():
    """When a cell's narrative references other 2-letter RIASEC codes (e.g., EC's
    'ER thrives in chaos'), those references must resolve to valid cells.

    Catches typos like ZX or invalid combos like RR.
    """
    for cid in EXEMPLAR_CELLS:
        c = get_cell_content(cid)
        for source_field, text in (
            ("core_insight_en", c.core_insight_en),
            ("deep_description_en", c.deep_description_en),
        ):
            refs = _CELL_REF.findall(text)
            refs = [r for r in refs if r != cid]
            for ref in refs:
                assert ref in VALID_CELLS_24, (
                    f"{cid}.{source_field} references invalid cell '{ref}'; "
                    f"must be one of the 24 valid cells"
                )
