"""Pydantic v2 models for cell content + career library entries."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CellId = Annotated[str, StringConstraints(pattern=r"^[RIASEC]{2}$")]


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
    """Indian salary bands (LPA shorthand, e.g. '6L', '12L–22L')."""

    model_config = ConfigDict(extra="forbid")

    entry: str
    mid: str
    senior: str


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
