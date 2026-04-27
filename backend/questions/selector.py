"""L1.5 dynamic question selection — 5 demographic + 24 static RIASEC + 16 dynamic IPIP/interest."""

from __future__ import annotations

import random

from questions.demographic import DEMOGRAPHIC_QUESTIONS, derive_profile_tags
from questions.interest_pool import INTEREST_POOL
from questions.ipip_neo import OCEAN_DOMAINS
from questions.models import Question
from questions.riasec_static_24 import get_riasec_static_24


def _tag_match_score(question: Question, profile_tags: list[str]) -> int:
    """How many of the question's tags overlap with the user's profile tags."""
    if not profile_tags:
        return 0
    return sum(1 for t in question.tags if t in profile_tags)


def _weighted_sample_for_dim(
    pool: list[Question],
    dim: str,
    n: int,
    profile_tags: list[str],
    rng: random.Random,
) -> list[Question]:
    """Pick `n` items from `pool` matching dimension `dim`, weighted by profile-tag overlap.

    Strategy: rank-based with rng tiebreaker (deterministic top-N), NOT softmax-style
    probabilistic. A 1-tag-match item always beats a 0-tag-match item; ties broken
    randomly per the seeded RNG. To switch to probabilistic weighting (where high-match
    is more likely but low-match is still possible), use weighted sampling without
    replacement instead.
    """
    candidates = [q for q in pool if q.dimension == dim]
    if len(candidates) < n:
        raise ValueError(f"Pool has only {len(candidates)} items for dimension {dim}, need {n}")

    # Score = tag-match count + small random tiebreaker (so deterministic per RNG seed)
    scored = [(q, _tag_match_score(q, profile_tags) + rng.random()) for q in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [q for q, _ in scored[:n]]


def _select_16_dynamic(
    profile_tags: list[str],
    seed: str,
) -> list[Question]:
    """Pick 16 items from INTEREST_POOL: 3 each O/C/E/A + 4 N (slight neuroticism weighting)."""
    rng = random.Random(f"{seed}::dynamic16")
    selected: list[Question] = []
    targets: dict[str, int] = {
        "openness": 3,
        "conscientiousness": 3,
        "extraversion": 3,
        "agreeableness": 3,
        "neuroticism": 4,
    }
    assert sum(targets.values()) == 16, "targets must total 16"

    for dim in OCEAN_DOMAINS:
        n = targets[dim]
        picked = _weighted_sample_for_dim(INTEREST_POOL, dim, n, profile_tags, rng)
        selected.extend(picked)

    return selected


def derive_interleaved_order(
    block_riasec: list[Question],
    block_interest: list[Question],
    seed: str,
) -> list[Question]:
    """Interleave RIASEC and interest blocks so users don't see homogeneous chunks.

    Pattern: RRRII repeating — alternates 3 RIASEC + 2 interest matching the 24:16 ratio.
    RIASEC block keeps its R-I-A-S-E-C type order (locked by Task 4 invariant).
    Interest block is shuffled per seed to prevent OCEAN clustering by test position
    (Neuroticism items would otherwise always land at the back, risking late-test
    fatigue bias on emotionally-heavy self-report).
    """
    rng = random.Random(f"{seed}::interleave")
    block_interest = list(block_interest)
    rng.shuffle(block_interest)

    riasec_iter = iter(block_riasec)
    interest_iter = iter(block_interest)

    r_count = i_count = 0
    pattern: list[str] = []
    while r_count < len(block_riasec) or i_count < len(block_interest):
        for _ in range(min(3, len(block_riasec) - r_count)):
            pattern.append("R")
            r_count += 1
        for _ in range(min(2, len(block_interest) - i_count)):
            pattern.append("I")
            i_count += 1

    interleaved: list[Question] = []
    for kind in pattern:
        if kind == "R":
            interleaved.append(next(riasec_iter))
        else:
            interleaved.append(next(interest_iter))

    return interleaved


def select_45_questions(
    demographic_answers: dict[str, str],
    seed: str,
) -> list[Question]:
    """Compose a 45-question test: 5 demographic + 24 static RIASEC + 16 dynamic IPIP-interest.

    Args:
      demographic_answers: {DEM_STAGE: "...", DEM_AGE: "...", ...}. May be empty in tests.
      seed: deterministic RNG seed (typically the assessment ID).

    Returns:
      45 Question objects in test-presentation order:
        Q1-5  demographic (fixed)
        Q6-45 RIASEC (24) + interest (16) interleaved in RRRII pattern
    """
    profile_tags = derive_profile_tags(demographic_answers)

    block_demographic = list(DEMOGRAPHIC_QUESTIONS)
    block_riasec = list(get_riasec_static_24())
    block_interest = _select_16_dynamic(profile_tags, seed)

    interleaved_40 = derive_interleaved_order(block_riasec, block_interest, seed)
    return block_demographic + interleaved_40
