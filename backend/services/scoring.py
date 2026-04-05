"""Big Five scoring engine with percentile mapping."""

from questions.question_bank import get_question_map

# Normative percentile lookup (approximate, based on global IPIP-NEO data
# with Indian population adjustments per validation report)
PERCENTILE_TABLE = {
    # score_range: percentile
    (0, 20): 2,
    (20, 30): 8,
    (30, 35): 15,
    (35, 40): 25,
    (40, 45): 35,
    (45, 50): 50,
    (50, 55): 58,
    (55, 60): 68,
    (60, 65): 75,
    (65, 70): 82,
    (70, 75): 88,
    (75, 80): 93,
    (80, 85): 96,
    (85, 90): 98,
    (90, 101): 99,
}


def score_to_percentile(score: float) -> int:
    for (lo, hi), pct in PERCENTILE_TABLE.items():
        if lo <= score < hi:
            return pct
    return 50


DIMENSIONS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def validate_answer_set(answers: dict[str, int], expected_ids: list[str] | None = None) -> None:
    if expected_ids is None:
        return

    expected = set(expected_ids)
    received = set(answers.keys())

    if received != expected:
        missing = sorted(list(expected - received))
        extra = sorted(list(received - expected))
        raise ValueError(f"Answer set mismatch. missing={missing[:5]} extra={extra[:5]}")

    for value in answers.values():
        if value < 1 or value > 5:
            raise ValueError("Likert values must be between 1 and 5")


def calculate_scores(answers: dict[str, int]) -> dict[str, float]:
    """Calculate Big Five dimension scores from answers.

    Args:
        answers: {question_id: likert_value (1-5)}

    Returns:
        {dimension: score (0-100)}
    """
    qmap = get_question_map()
    dim_scores: dict[str, list[float]] = {d: [] for d in DIMENSIONS}

    for qid, value in answers.items():
        if qid not in qmap:
            continue
        q = qmap[qid]
        if q["reverse"]:
            value = 6 - value  # reverse score: 1->5, 2->4, etc.
        dim_scores[q["dimension"]].append(value)

    scores = {}
    for dim in DIMENSIONS:
        values = dim_scores[dim]
        if values:
            scores[dim] = round((sum(values) / len(values)) * 20, 1)  # scale to 0-100
        else:
            scores[dim] = 50.0

    return scores


def calculate_percentiles(scores: dict[str, float]) -> dict[str, int]:
    return {dim: score_to_percentile(score) for dim, score in scores.items()}
