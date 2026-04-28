"""Milestone copy for Q10/Q20/Q30/Q40 progress screens.

Each milestone has a small pool of Hinglish-flavored encouragement strings.
The selector uses a seeded RNG so the same user (assessment_id seed) sees
consistent copy across re-renders within a session, but different users
see variety.
"""

from __future__ import annotations

import random

MILESTONE_THRESHOLDS: tuple[int, ...] = (10, 20, 30, 40)

_COPY_POOL: dict[int, tuple[str, ...]] = {
    10: (
        "10 down. Your patience already beats 60% of users.",
        "Bhai, you've started. Most don't even open the link.",
        "10 questions in. Aunty couldn't have done this. You can.",
        "10 down. The hard part is showing up — you already did.",
    ),
    20: (
        "Halfway. Even Sharma ji's beta started here.",
        "20 questions in. You're more disciplined than your last EMI day.",
        "Halfway through. 25 minutes from now you'll know your IBTI.",
        "20 down. Take a breath. The good part is starting.",
    ),
    30: (
        "Almost there. Your career insight is loading.",
        "30 down. The questions get more honest from here.",
        "30 in. You've outlasted 70% of who started this test.",
        "10 to go. Don't bail when the answer is this close.",
    ),
    40: (
        "5 more. Don't bail. Aunty's watching.",
        "40 down. The last 5 are the ones that decide your archetype.",
        "Almost done. Take the last 5 seriously — this is the deciding stretch.",
        "5 to go. Show your future self some respect and finish strong.",
    ),
}


def get_milestone_at(question_index: int) -> int | None:
    """Return the milestone threshold for the given 1-indexed question count, or None.

    Args:
      question_index: 1-indexed count of questions completed (e.g., 10 means user just answered Q10).

    Returns:
      The matching threshold (10/20/30/40) if `question_index` is one of those values; else None.
    """
    return question_index if question_index in MILESTONE_THRESHOLDS else None


def get_copy_for_milestone(milestone: int, seed: str) -> str:
    """Pick one milestone copy line, deterministic per (milestone, seed).

    Raises:
      ValueError: if `milestone` is not one of the canonical thresholds (10, 20, 30, 40).
    """
    if milestone not in _COPY_POOL:
        raise ValueError(f"unknown milestone {milestone!r}; must be one of {MILESTONE_THRESHOLDS}")
    rng = random.Random(f"{seed}::milestone::{milestone}")
    pool = _COPY_POOL[milestone]
    return rng.choice(pool)
