"""Derive 24-cell archetype from Holland code + check MAST 0.06% rare trigger.

Hexagon adjacency rules (Holland 1959/1997):
  R-I-A-S-E-C-R is the canonical hexagon order. Distance-3 (opposite) pairs
  represent fundamentally incompatible interest types and shouldn't form
  a stable archetype.

Opposite pairs (forbidden): R↔S, I↔E, A↔C.
Valid pairs: any non-self, non-opposite combination = 6 × 4 = 24 cells.

MAST trigger (override):
  Replaces the normal cell label with `MAST · The Vibing Outlier`. Reserved
  for users whose OCEAN profile is positively-skewed across openness,
  extraversion, agreeableness, and emotional stability simultaneously, AND
  whose RIASEC profile isn't dominated by a single type. Combined ~0.05–0.10%.
"""

from __future__ import annotations

from questions.holland_riasec import RIASEC_TYPES

OPPOSITE_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset(["R", "S"]),
    frozenset(["I", "E"]),
    frozenset(["A", "C"]),
})


def is_valid_pair(main: str, sub: str) -> bool:
    """True if (main, sub) is a non-self, non-opposite RIASEC pair."""
    if main == sub:
        return False
    if main not in RIASEC_TYPES or sub not in RIASEC_TYPES:
        return False
    return frozenset([main, sub]) not in OPPOSITE_PAIRS


def _build_valid_cells() -> tuple[str, ...]:
    return tuple(
        f"{m}{s}"
        for m in RIASEC_TYPES
        for s in RIASEC_TYPES
        if is_valid_pair(m, s)
    )


VALID_CELLS_24: tuple[str, ...] = _build_valid_cells()


def derive_archetype_cell(riasec_scores: dict[str, int], holland_code: str) -> str:
    """Pick a 2-letter archetype cell from the holland code's main + best valid sub.

    Strategy:
      1. main = holland_code[0]
      2. Try holland_code[1], then holland_code[2] — first valid wins
      3. Fallback: scan all RIASEC types by descending score for first valid sub
      4. If still nothing valid, raise (should be unreachable in practice)
    """
    main = holland_code[0]
    for candidate in holland_code[1:]:
        if is_valid_pair(main, candidate):
            return main + candidate

    sorted_by_score = sorted(
        riasec_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )
    for letter, _ in sorted_by_score:
        if letter == main:
            continue
        if is_valid_pair(main, letter):
            return main + letter

    raise ValueError(
        f"Cannot derive archetype cell for main={main!r} from scores {riasec_scores}. "
        f"This should be unreachable — every main type has 4 valid sub-types."
    )


def check_mast_trigger(
    ocean_percentiles: dict[str, int],
    riasec_scores: dict[str, int],
) -> bool:
    """MAST 0.06% rare-personality trigger.

    Conditions (all must hold):
      - openness percentile ≥ 90
      - extraversion percentile ≥ 85
      - agreeableness percentile ≥ 85
      - emotional stability ≥ 85 (= neuroticism percentile ≤ 15)
      - no RIASEC type below 40% of max (max 20, threshold 8)

    Returns True if all conditions hold; otherwise False.
    """
    if ocean_percentiles.get("openness", 0) < 90:
        return False
    if ocean_percentiles.get("extraversion", 0) < 85:
        return False
    if ocean_percentiles.get("agreeableness", 0) < 85:
        return False
    if ocean_percentiles.get("neuroticism", 100) > 15:
        return False
    if any(score < 8 for score in riasec_scores.values()):
        return False
    return True
