"""Public archetype catalog router — read-only browse of all 24 cells.

Used by the marketing pages (`/archetypes`, landing gallery) to render
archetype names + slogans without bundling content into the JS payload.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from content.cells import get_cell_content, load_all_cells


router = APIRouter(prefix="/api/v3/archetypes", tags=["archetypes"])


class ArchetypeSummary(BaseModel):
    cell_id: str
    label_en: str
    label_hi: str
    slogan_en: str
    rarity_pct: float


class ArchetypeDetail(ArchetypeSummary):
    core_insight_en: str
    deep_description_en: str
    strengths_en: list[str]
    growth_tips_en: list[str]
    career_directions: list[str]


@router.get("", response_model=list[ArchetypeSummary])
def list_archetypes():
    cells = load_all_cells()
    summaries: list[ArchetypeSummary] = []
    for cell_id, c in cells.items():
        summaries.append(
            ArchetypeSummary(
                cell_id=cell_id,
                label_en=c.label_en,
                label_hi=c.label_hi,
                slogan_en=c.slogan_en,
                rarity_pct=c.rarity_pct,
            )
        )
    summaries.sort(key=lambda s: s.cell_id)
    return summaries


@router.get("/{cell_id}", response_model=ArchetypeDetail)
def get_archetype_detail(cell_id: str):
    try:
        c = get_cell_content(cell_id.upper())
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown archetype: {cell_id}")
    return ArchetypeDetail(
        cell_id=cell_id.upper(),
        label_en=c.label_en,
        label_hi=c.label_hi,
        slogan_en=c.slogan_en,
        rarity_pct=c.rarity_pct,
        core_insight_en=c.core_insight_en,
        deep_description_en=c.deep_description_en,
        strengths_en=c.strengths_en,
        growth_tips_en=c.growth_tips_en,
        career_directions=c.career_directions,
    )
