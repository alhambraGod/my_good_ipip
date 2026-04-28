"""Pydantic v2 models for cell content + career library entries."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

CellId = Annotated[str, StringConstraints(pattern=r"^[RIASEC]{2}$")]

# A salary string must either be a sentinel ("Variable" / "N/A") or contain at least
# one lakh-/crore-notation token (e.g. "6L", "3.5L", "1.2Cr", "60L+", "5Cr+").
# Surrounding range separators (–/-), parentheticals like "(Postdoc)", and trailing
# descriptors like "per project" / "or exit" are allowed; bare numerals and free-form
# prose without an L/Cr token are rejected. Adjusted from the original "L-only"
# proposal so screenwriter/film/PE/quant ranges with Cr or "+" still validate.
_SALARY_PATTERN = re.compile(
    r"^(?:Variable|N/A|.*\d+(?:\.\d+)?(?:L|Cr)\+?.*)$",
    re.IGNORECASE,
)


class OceanModifiers(BaseModel):
    """Optional fine-grained personalization based on user's OCEAN scores.

    Each modifier is a 1-2 sentence override that the report generator
    weaves into the cell description when the corresponding OCEAN extreme
    is detected (e.g., percentile >= 80 for "high_*" or <= 20 for "low_*").

    Naming uses ``neuroticism`` (NOT ``emotional_stability``) for consistency
    with ``services/scoring/archetype.py`` and the OCEAN percentile keys.
    """

    model_config = ConfigDict(extra="forbid")

    high_openness: str | None = None
    low_openness: str | None = None
    high_conscientiousness: str | None = None
    low_conscientiousness: str | None = None
    high_extraversion: str | None = None
    low_extraversion: str | None = None
    high_agreeableness: str | None = None
    low_agreeableness: str | None = None
    high_neuroticism: str | None = None
    low_neuroticism: str | None = None


class CellContent(BaseModel):
    """Content for one of the 24 archetype cells (e.g., IA, RI, SE).

    All English content fields use the ``_en`` suffix so Phase 4 can add
    parallel ``_hi`` (Hindi) fields without schema migration.
    """

    model_config = ConfigDict(extra="forbid")

    cell: CellId
    label_en: str = Field(min_length=3, max_length=80)
    label_hi: str = Field(min_length=1, max_length=80)
    slogan_en: str = Field(min_length=10, max_length=140)
    rarity_pct: float = Field(ge=0.0, le=100.0)
    core_insight_en: str = Field(min_length=20, max_length=600)
    deep_description_en: str = Field(min_length=100, max_length=3000)
    strengths_en: list[str] = Field(min_length=5, max_length=5)
    growth_tips_en: list[str] = Field(min_length=5, max_length=5)
    career_directions: list[str] = Field(min_length=3, max_length=8)
    share_lines_en: list[str] = Field(min_length=1, max_length=5)
    ocean_modifiers: OceanModifiers = Field(default_factory=OceanModifiers)


class SalaryRange(BaseModel):
    """INR salary in lakh-notation strings.

    Format examples:
      - ``"6L"`` (single point)
      - ``"12L–22L"`` or ``"12L-22L"`` (range with en-dash or hyphen)
      - ``"0L–6L"`` (zero entry for early stage)
      - ``"30L–1Cr+ per project"`` / ``"15L–40L (Seed)"`` (descriptor-suffixed)
      - ``"Variable"`` / ``"N/A"`` — sentinel values for atypical careers
    """

    model_config = ConfigDict(extra="forbid")

    entry: str = Field(min_length=1, max_length=40)
    mid: str = Field(min_length=1, max_length=40)
    senior: str = Field(min_length=1, max_length=40)

    @field_validator("entry", "mid", "senior")
    @classmethod
    def _validate_salary_format(cls, v: str) -> str:
        if not _SALARY_PATTERN.match(v.strip()):
            raise ValueError(
                f"salary string {v!r} doesn't match lakh notation. "
                f"Examples: '6L', '12L–22L', '30L–80L', 'Variable', '0L (bootstrapped)'. "
                f"Did you forget the 'L' suffix?"
            )
        return v


class CareerEntry(BaseModel):
    """Content for one career in the library (40 total).

    ``why_match`` keys are validated as RIASEC cell IDs (``CellId`` regex) so
    typo'd cell references fail at parse time, not at validator-run time.
    """

    model_config = ConfigDict(extra="forbid")

    career_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name_en: str
    name_hi: str
    tagline_en: str = Field(max_length=140)
    why_match: dict[CellId, str]
    indian_companies: list[str] = Field(min_length=2, max_length=8)
    salary_inr: SalaryRange
    education_path: list[str]
    city_distribution: list[str] = Field(min_length=1)
