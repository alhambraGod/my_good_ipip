"""tests/test_content_models.py — content schema validation."""
import pytest
from pydantic import ValidationError

from content.models import CareerEntry, CellContent, OceanModifiers, SalaryRange


def test_ocean_modifiers_construct():
    m = OceanModifiers(
        high_conscientiousness="Your high conscientiousness pulls IA toward execution.",
        high_neuroticism="Under stress you need to externalize the loop.",
    )
    assert m.high_conscientiousness.startswith("Your high")
    assert m.high_openness is None  # optional


def test_cell_content_minimal():
    c = CellContent(
        cell="IA",
        label_en="The 3AM Chai Philosopher",
        label_hi="Sochne Wala",
        slogan_en="You overthink your overthinking. Also this sentence.",
        rarity_pct=4.3,
        core_insight_en="You think a lot. Maybe too much.",
        deep_description_en="A 300-500 word body that explains the archetype in depth, weaving stress signals, growth edges, and identity claims.",
        strengths_en=["Pattern recognition", "Synthesis", "Independent learning", "Comfort with ambiguity", "Strategic foresight"],
        growth_tips_en=["Set timeboxes", "Ship 70%-ready", "Externalize loops", "Peer rubber-duck", "Daily small wins"],
        career_directions=["data_scientist", "strategy_consultant", "research_scientist"],
        share_lines_en=["I'm IA. My personality is just Stack Overflow with trust issues."],
        ocean_modifiers=OceanModifiers(),
    )
    assert c.cell == "IA"
    assert len(c.strengths_en) == 5
    assert len(c.growth_tips_en) == 5


def test_cell_content_validates_cell_format():
    """Cell must be exactly 2 uppercase letters from RIASEC."""
    with pytest.raises(ValidationError):
        CellContent(
            cell="IAA",  # 3 chars, invalid
            label_en="x", label_hi="x", slogan_en="x" * 15, rarity_pct=1.0,
            core_insight_en="x" * 25, deep_description_en="x" * 105,
            strengths_en=["a", "b", "c", "d", "e"], growth_tips_en=["a", "b", "c", "d", "e"],
            career_directions=["x", "y", "z"], share_lines_en=["x"],
            ocean_modifiers=OceanModifiers(),
        )


def test_career_entry_minimal():
    c = CareerEntry(
        career_id="data_scientist",
        name_en="Data Scientist",
        name_hi="Aankde Vigyani",
        tagline_en="Turn chaos into signal",
        why_match={"IA": "You see patterns in noise.", "IC": "Numerical brain pays off."},
        indian_companies=["Razorpay", "Swiggy", "Flipkart"],
        salary_inr=SalaryRange(entry="6L", mid="12L–22L", senior="30L–80L"),
        education_path=["B.Tech CSE/Stats", "Online: Coursera"],
        city_distribution=["Bangalore", "Hyderabad"],
    )
    assert c.career_id == "data_scientist"
    assert c.salary_inr.entry == "6L"
    assert "IA" in c.why_match


def test_cell_content_rejects_unknown_field():
    """extra='forbid' should reject typo'd field names like 'strengths' (without _en suffix)."""
    with pytest.raises(ValidationError):
        CellContent(
            cell="IA",
            label_en="abc", label_hi="b", slogan_en="x" * 15, rarity_pct=1.0,
            core_insight_en="x" * 25, deep_description_en="x" * 105,
            strengths=["a", "b", "c", "d", "e"],  # WRONG: should be strengths_en
            growth_tips_en=["a", "b", "c", "d", "e"],
            career_directions=["x", "y", "z"], share_lines_en=["x"],
            ocean_modifiers=OceanModifiers(),
        )


def test_ocean_modifiers_rejects_typo():
    """extra='forbid' should reject typo'd field names like 'high_emotional_stability' (renamed to neuroticism)."""
    with pytest.raises(ValidationError):
        OceanModifiers(high_emotional_stability="x")  # OLD name; should now be high_neuroticism (inverted)


def test_why_match_rejects_invalid_cell_id():
    """why_match keys are CellId-validated; bad cell IDs fail at parse time."""
    with pytest.raises(ValidationError):
        CareerEntry(
            career_id="data_scientist",
            name_en="Data Scientist", name_hi="x",
            tagline_en="Turn chaos into signal",
            why_match={"XZ": "bogus cell id"},  # XZ is not a valid 2-letter RIASEC combo
            indian_companies=["x", "y"],
            salary_inr=SalaryRange(entry="6L", mid="12L", senior="30L"),
            education_path=["x"], city_distribution=["x"],
        )
