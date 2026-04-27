"""Static 24-item subset of Holland RIASEC 60 — same 24 items shown to ALL users.

Why static: RIASEC scores must be cross-user comparable so the resulting Holland
code maps to a stable archetype cell. If items varied per user, scores wouldn't
mean the same thing for cohort comparison.

Selection structure (preserved across all 6 types):
  - 2 items from `activities` (JSON ids 01–04) — what the person likes to do
  - 1 item from `competencies` (05–07) — self-reported ability
  - 1 item from `occupations` (08–10) — vocational preference
This 2+1+1 split samples each RIASEC measurement facet so total scores
aren't dominated by one category. When swapping IDs, preserve this split.

Specific item choices within each category are starter content — picked to
favor universally translatable wording. Phase 2 should review with a native
copywriter and may swap items inside a category without changing the structure.
"""

from __future__ import annotations

from functools import lru_cache

from questions.holland_riasec import RIASEC_TYPES, load_riasec_questions
from questions.models import Question

# Item ids correspond to `RIASEC_<JSON_id>` from the holland_riasec loader.
# JSON ids are like "R01"..."C10" (10 per type), so loader-produced ids are "RIASEC_R01"..."RIASEC_C10".
# This dict is the SOURCE OF TRUTH — adjust here when curators refine choices.
STATIC_24_ITEM_IDS: dict[str, tuple[str, ...]] = {
    "R": ("RIASEC_R01", "RIASEC_R03", "RIASEC_R05", "RIASEC_R08"),
    "I": ("RIASEC_I01", "RIASEC_I03", "RIASEC_I06", "RIASEC_I09"),
    "A": ("RIASEC_A01", "RIASEC_A04", "RIASEC_A06", "RIASEC_A09"),
    "S": ("RIASEC_S01", "RIASEC_S03", "RIASEC_S06", "RIASEC_S08"),
    "E": ("RIASEC_E01", "RIASEC_E03", "RIASEC_E06", "RIASEC_E09"),
    "C": ("RIASEC_C01", "RIASEC_C03", "RIASEC_C06", "RIASEC_C09"),
}


@lru_cache(maxsize=1)
def get_riasec_static_24() -> list[Question]:
    """Return the 24 hand-picked RIASEC questions, deterministically ordered by RIASEC type."""
    all_riasec = {q.id: q for q in load_riasec_questions()}
    selected: list[Question] = []
    for t in RIASEC_TYPES:
        for qid in STATIC_24_ITEM_IDS[t]:
            if qid not in all_riasec:
                raise ValueError(
                    f"Curated RIASEC id {qid!r} not found in load_riasec_questions(). "
                    f"Either remove it from STATIC_24_ITEM_IDS in {__name__} or "
                    f"restore it in docs/Holland_RIASEC_60_questionbank.json."
                )
            selected.append(all_riasec[qid])
    return selected
