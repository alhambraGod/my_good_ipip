"""Compute 3-letter Holland code from 6 RIASEC scores."""

from __future__ import annotations


def compute_holland_code(riasec_scores: dict[str, int]) -> str:
    """Return top-3 RIASEC types as a 3-letter string. Ties broken alphabetically.

    Example:
      {"R": 5, "I": 19, "A": 17, "S": 9, "E": 11, "C": 13} -> "IAC"
    """
    items = sorted(
        riasec_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),  # desc by score, asc by letter (alphabetical tiebreak)
    )
    code = "".join(letter for letter, _ in items[:3])
    if len(code) != 3:
        raise ValueError(f"Holland code must be 3 letters, got {code!r} from scores {riasec_scores}")
    return code
