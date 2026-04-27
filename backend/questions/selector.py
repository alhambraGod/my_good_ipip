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
    """Pick `n` items from `pool` matching dimension `dim`, weighted by profile-tag overlap."""
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
    Within each block, original order is preserved.
    """
    # The seed argument is reserved for future per-user shuffle within blocks (currently unused).
    _ = seed

    riasec_iter = iter(block_riasec)
    interest_iter = iter(block_interest)

    pattern: list[str] = []
    while len(pattern) < (len(block_riasec) + len(block_interest)):
        if pattern.count("R") < len(block_riasec):
            for _ in range(3):
                if pattern.count("R") < len(block_riasec):
                    pattern.append("R")
        if pattern.count("I") < len(block_interest):
            for _ in range(2):
                if pattern.count("I") < len(block_interest):
                    pattern.append("I")

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
