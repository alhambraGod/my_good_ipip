"""RIASEC scoring: 4 items per type × 1-5 likert = score range 4-20 per type.

For unanswered types, score is 0 (caller can detect 'no data' from this).
"""

from __future__ import annotations

from questions.holland_riasec import RIASEC_TYPES, load_riasec_questions


def compute_riasec_scores(answers: dict[str, int]) -> dict[str, int]:
    """Sum likert values per RIASEC type. Returns {R: 0-20, I: 0-20, ...}.

    Items not in the RIASEC bank are silently ignored (caller may pass IPIP/INT items mixed in).
    """
    by_id = {q.id: q for q in load_riasec_questions()}
    totals: dict[str, int] = {t: 0 for t in RIASEC_TYPES}

    for qid, value in answers.items():
        q = by_id.get(qid)
        if q is None:
            continue
        if not (1 <= value <= 5):
            raise ValueError(f"RIASEC answer for {qid} must be 1-5, got {value}")
        totals[q.dimension] += value

    return totals
