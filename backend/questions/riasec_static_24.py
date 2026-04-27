"""Static 24-item subset of Holland RIASEC 60 — same 24 items shown to ALL users.

Why static: RIASEC scores must be cross-user comparable so the resulting Holland
code maps to a stable archetype cell. If items varied per user, scores wouldn't
mean the same thing for cohort comparison.

Selection criteria (manual curation, hand-picked from the 60-item bank):
  - 4 items per RIASEC type
  - Prefer items that translate cleanly into Indian work/life contexts
  - Mix of vocational (career-leaning) and avocational (interest-leaning)
  - Avoid items requiring uncommon vocabulary or Western-only references
"""

from __future__ import annotations

from functools import lru_cache

from questions.holland_riasec import RIASEC_TYPES, load_riasec_questions
from questions.models import Question

# Item ids correspond to `RIASEC_<JSON_id>` from the holland_riasec loader.
# JSON ids are like "R01"..."C10" (10 per type), so loader-produced ids are "RIASEC_R01"..."RIASEC_C10".
# This dict is the SOURCE OF TRUTH — adjust here when curators refine choices.
STATIC_24_ITEM_IDS: dict[str, list[str]] = {
    "R": ["RIASEC_R01", "RIASEC_R03", "RIASEC_R05", "RIASEC_R08"],
    "I": ["RIASEC_I01", "RIASEC_I03", "RIASEC_I06", "RIASEC_I09"],
    "A": ["RIASEC_A01", "RIASEC_A04", "RIASEC_A06", "RIASEC_A09"],
    "S": ["RIASEC_S01", "RIASEC_S03", "RIASEC_S06", "RIASEC_S08"],
    "E": ["RIASEC_E01", "RIASEC_E03", "RIASEC_E06", "RIASEC_E09"],
    "C": ["RIASEC_C01", "RIASEC_C03", "RIASEC_C06", "RIASEC_C09"],
}


@lru_cache(maxsize=1)
def get_riasec_static_24() -> list[Question]:
    """Return the 24 hand-picked RIASEC questions, deterministically ordered by RIASEC type."""
    all_riasec = {q.id: q for q in load_riasec_questions()}
    selected: list[Question] = []
    for t in RIASEC_TYPES:
        for qid in STATIC_24_ITEM_IDS[t]:
            if qid not in all_riasec:
                raise ValueError(f"Curated RIASEC id {qid} missing from 60-bank")
            selected.append(all_riasec[qid])
    return selected
