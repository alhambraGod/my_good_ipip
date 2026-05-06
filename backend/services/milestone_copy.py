"""Milestone copy for Q10/Q20/Q30/Q40 progress screens.

Each milestone has a small pool of Hinglish-flavored encouragement strings
in two locales: ``en`` (English with mild Hinglish) and ``hi`` (Romanized
Hindi / Hinglish — Devanagari can come in v2). The selector uses a seeded
RNG so the same user (assessment_id seed) sees consistent copy across
re-renders within a session, but different users see variety.
"""

from __future__ import annotations

import random
from typing import Literal

__all__ = [
    "MILESTONE_THRESHOLDS",
    "Lang",
    "get_milestone_at",
    "get_copy_for_milestone",
]

Lang = Literal["en", "hi"]

MILESTONE_THRESHOLDS: tuple[int, ...] = (10, 20, 30, 40)

_COPY_POOL_EN: dict[int, tuple[str, ...]] = {
    10: (
        "10 down. Your patience already beats 60% of users.",
        "Bhai, you've started. Most don't even open the link.",
        "10 questions in. Aunty couldn't have done this. You can.",
        "10 down. The hard part is showing up — you already did.",
    ),
    20: (
        "Halfway. Even Sharma ji's beta started here.",
        "20 questions in. You're more disciplined than your last EMI day.",
        "Halfway through. 25 minutes from now you'll know your career archetype.",
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

_COPY_POOL_HI: dict[int, tuple[str, ...]] = {
    10: (
        "10 ho gaye. 60% log itna bhi nahi karte.",
        "Bhai, shuru toh kar diya. Zyaada log toh link bhi nahi kholte.",
        "10 sawal nikal gaye. Aunty se nahi ho paata, aap kar rahe ho.",
        "10 ho gaye. Sabse mushkil tha shuru karna — wo ho gaya.",
    ),
    20: (
        "Aadhi hua. Sharma ji ka beta bhi yahin se start hua tha.",
        "20 ho gaye. Aaj aap apni EMI date se zyaada disciplined ho.",
        "Halfway. 25 min me apna career archetype pata chal jaayega.",
        "20 ho gaye. Saans lo. Ab maza aane wala hai.",
    ),
    30: (
        "Bas ho hi gaya. Career insight load ho rahi hai.",
        "30 ho gaye. Yahan se sawal aur honest hote jaate hain.",
        "30 ho gaye. 70% logon se aage ho jo shuru kiya tha.",
        "Sirf 10 bache. Itne paas aake bail mat karna.",
    ),
    40: (
        "5 aur. Bail mat karna. Aunty dekh rahi hai.",
        "40 ho gaye. Last 5 sawal hi archetype decide karte hain.",
        "Bas ho gaya. Aakhri 5 ko seriously lo — yahi deciding stretch hai.",
        "5 to go. Future-self ko thoda respect do, strong finish karo.",
    ),
}

_POOLS: dict[Lang, dict[int, tuple[str, ...]]] = {
    "en": _COPY_POOL_EN,
    "hi": _COPY_POOL_HI,
}


def get_milestone_at(question_index: int) -> int | None:
    """Return the milestone threshold for the given 1-indexed question count, or None."""
    return question_index if question_index in MILESTONE_THRESHOLDS else None


def get_copy_for_milestone(milestone: int, seed: str, lang: Lang = "en") -> str:
    """Pick one milestone copy line, deterministic per (milestone, seed, lang).

    Raises:
      ValueError: if `milestone` is not one of the canonical thresholds.
    """
    if milestone not in MILESTONE_THRESHOLDS:
        raise ValueError(
            f"unknown milestone {milestone!r}; must be one of {MILESTONE_THRESHOLDS}"
        )
    pool_by_milestone = _POOLS.get(lang) or _POOLS["en"]
    pool = pool_by_milestone[milestone]
    rng = random.Random(f"{seed}::milestone::{milestone}::{lang}")
    return rng.choice(pool)
