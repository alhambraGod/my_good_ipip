# CareerDNA India · Phase 2 Content Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the content infrastructure that Phase 4 (UI) renders: 24 cell content files (Holland double-letter archetypes with India-flavored labels + slogans + insights + strengths + growth tips + career references) + 40 career library entries (India-tuned, with companies, salary, education paths) + milestone copy module + loaders/validators/tests. Produce **complete schemas + stub-quality content for every cell and career** + **8 hand-curated exemplars** demonstrating the gold standard. Bulk content authoring by GPT-4o + native Indian copywriter happens out-of-band post-Phase-2; the schemas + loaders + cross-reference validators ensure their work integrates without code changes.

**Architecture:** New `backend/content/` package with `cells.py` (loader + dataclass) and `careers.py` (loader + dataclass) reading JSON files from `backend/content/data/cells/*.json` and `backend/content/data/careers/library.json`. New `backend/services/milestone_copy.py` for the Q10/Q20/Q30/Q40 progress page strings. Cross-reference validator ensures every `career_id` referenced in a cell exists in the career library, and every cell ID matches the 24 valid Holland combinations from Phase 1's `archetype.py::VALID_CELLS_24`.

**Tech Stack:** Python 3.11, Pydantic v2, JSON, pytest. No new system dependencies.

**Spec source:** `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` (Sections 3.10, 3.11, 3.12, S5)
**Phase 1 prerequisite:** commit `d3850b0` (Phase 1 complete with 60 tests + scoring infrastructure)

---

## Task 1: Cell content schema (Pydantic models)

**Files:**
- Create: `backend/content/__init__.py`
- Create: `backend/content/models.py`
- Create: `backend/tests/test_content_models.py`

- [ ] **Step 1: Write failing test**

```python
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
        core_insight_en="You think a lot. Maybe too much, but also exactly the right amount.",
        deep_description_en="A 300-500 word body that explains the archetype in depth, weaving stress signals, growth edges, and identity claims that resonate with Indian Gen Z context.",
        strengths_en=["Pattern recognition", "Synthesis", "Independent learning", "Comfort with ambiguity", "Strategic foresight"],
        growth_tips_en=["Set timeboxes", "Ship 70%-ready", "Externalize loops", "Peer rubber-duck", "Daily small wins"],
        career_directions=["data_scientist", "strategy_consultant", "ai_research_engineer"],
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
            label_en="abc", label_hi="b", slogan_en="x" * 15, rarity_pct=1.0,
            core_insight_en="x" * 25, deep_description_en="x" * 105,
            strengths_en=["a","b","c","d","e"], growth_tips_en=["a","b","c","d","e"],
            career_directions=["x", "y", "z"], share_lines_en=["x"],
            ocean_modifiers=OceanModifiers(),
        )


def test_cell_content_rejects_unknown_field():
    """extra='forbid' should reject typo'd field names like 'strengths' (without _en suffix)."""
    with pytest.raises(ValidationError):
        CellContent(
            cell="IA",
            label_en="abc", label_hi="b", slogan_en="x" * 15, rarity_pct=1.0,
            core_insight_en="x" * 25, deep_description_en="x" * 105,
            strengths=["a","b","c","d","e"],  # WRONG: should be strengths_en
            growth_tips_en=["a","b","c","d","e"],
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
```

- [ ] **Step 2: Run test, expect failure**

```bash
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate my_good_ipip && cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_content_models.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `backend/content/__init__.py`** (empty file).

- [ ] **Step 4: Implement `backend/content/models.py`**

```python
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

    Naming uses `neuroticism` (NOT `emotional_stability`) for consistency with
    services/scoring/archetype.py and the OCEAN percentile keys.
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

    All English content fields use the `_en` suffix so Phase 4 can add
    parallel `_hi` (Hindi) fields without schema migration.
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
    model_config = ConfigDict(extra="forbid")

    entry: str         # e.g., "6L"
    mid: str           # e.g., "12L–22L"
    senior: str        # e.g., "30L–80L"


class CareerEntry(BaseModel):
    """Content for one career in the library (40 total).

    `why_match` keys are validated as RIASEC cell IDs (CellId regex) so
    typo'd cell references fail at parse time, not at validator-run time.
    """

    model_config = ConfigDict(extra="forbid")

    career_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name_en: str
    name_hi: str
    tagline_en: str = Field(max_length=140)
    why_match: dict[CellId, str]   # cell_id → 1-line why; CellId regex enforces 2-letter RIASEC
    indian_companies: list[str] = Field(min_length=2, max_length=8)
    salary_inr: SalaryRange
    education_path: list[str]
    city_distribution: list[str] = Field(min_length=1)
```

- [ ] **Step 5: Run test, expect pass**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_content_models.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Verify pydantic v2 is already in requirements.txt**

```bash
cd /Users/antonio/god/my_good_ipip/backend && grep -i pydantic requirements.txt
```

Expected: pydantic appears (it's used by FastAPI). If missing, add `pydantic==2.9.2`.

- [ ] **Step 7: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/ backend/tests/test_content_models.py
git commit -m "feat(backend): add Pydantic schemas for cell + career content"
```

---

## Task 2: Cell content directory + loader + 24 stub files

**Files:**
- Create: `backend/content/cells.py`
- Create: `backend/content/data/cells/{IR,IA,IS,IC,RI,RA,RE,RC,AI,AR,AS,AE,SI,SA,SE,SC,ER,EA,ES,EC,CI,CR,CS,CE}.json` (24 files)
- Create: `backend/tests/test_cell_loader.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_cell_loader.py — verify all 24 cell content files load + validate."""
from content.cells import get_cell_content, load_all_cells
from content.models import CellContent
from services.scoring.archetype import VALID_CELLS_24


def test_all_24_cells_have_files():
    cells = load_all_cells()
    assert len(cells) == 24
    for cell_id in VALID_CELLS_24:
        assert cell_id in cells, f"missing content for {cell_id}"


def test_all_cells_validate_against_schema():
    cells = load_all_cells()
    for cell_id, content in cells.items():
        assert isinstance(content, CellContent)
        assert content.cell == cell_id


def test_get_cell_content_known_cell():
    c = get_cell_content("IA")
    assert c.cell == "IA"
    assert len(c.strengths_en) == 5
    assert len(c.growth_tips_en) == 5


def test_get_cell_content_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        get_cell_content("XX")


def test_no_orphan_cell_files():
    """No JSON file in data/cells/ that isn't one of the 24 valid cells."""
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "data", "cells")
    files = {f.replace(".json", "") for f in os.listdir(data_dir) if f.endswith(".json")}
    assert files == set(VALID_CELLS_24), f"orphan or missing files: {files ^ set(VALID_CELLS_24)}"
```

(Note: `import pytest` IS used here because `pytest.raises` is needed.)

- [ ] **Step 2: Run test, expect FAIL**

Expected: ModuleNotFoundError on first failing assertion.

- [ ] **Step 3: Implement `backend/content/cells.py`**

```python
"""Cell content loader — reads 24 JSON files from content/data/cells/, validates against schema."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from content.models import CellContent
from services.scoring.archetype import VALID_CELLS_24

_HERE = Path(__file__).resolve().parent
_CELLS_DIR = _HERE / "data" / "cells"


@lru_cache(maxsize=1)
def load_all_cells() -> dict[str, CellContent]:
    """Load all 24 cell JSON files into {cell_id: CellContent}.

    Raises:
      FileNotFoundError if any of the 24 expected files is missing.
      ValidationError if any file fails the CellContent schema.
    """
    cells: dict[str, CellContent] = {}
    for cell_id in VALID_CELLS_24:
        path = _CELLS_DIR / f"{cell_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing cell content file: {path}")
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        cells[cell_id] = CellContent.model_validate(raw)
    return cells


def get_cell_content(cell_id: str) -> CellContent:
    """Look up content for a single cell. Raises KeyError if not in 24 valid cells."""
    cells = load_all_cells()
    if cell_id not in cells:
        raise KeyError(f"unknown cell: {cell_id!r}; must be one of {VALID_CELLS_24}")
    return cells[cell_id]
```

- [ ] **Step 4: Generate 24 stub JSON files**

Create one JSON file per valid cell with placeholder content matching the schema. Use the cell-naming table from the spec (Section 3.10) for `label_en`. Each stub uses the same template:

For example, `backend/content/data/cells/IA.json`:

```json
{
  "cell": "IA",
  "label_en": "The 3AM Chai Philosopher",
  "label_hi": "Sochne Wala",
  "slogan_en": "You overthink your overthinking. Also this sentence.",
  "rarity_pct": 4.3,
  "core_insight_en": "PLACEHOLDER — 80-120 word core insight goes here. Phase 2.5 content authoring will replace this with India-flavored copy describing the IA archetype: investigative-dominant + artistic-supporting, prone to overthinking, late-night philosopher mode, but capable of deep synthesis when finally focused.",
  "deep_description_en": "PLACEHOLDER — 300-500 word deep description goes here. To be authored by GPT-4o + native Indian copywriter review. Should incorporate Hinglish accents (Sharma ji, Aunty, EMI references) where appropriate, and balance the dark-humor IBTI tone with a temperature-of-warmth that the cell rewards (versus pure roast).",
  "strengths_en": [
    "Pattern recognition across disparate fields",
    "Strategic foresight under ambiguity",
    "Independent learning without external prompting",
    "Synthesis of mixed signals into coherent insight",
    "Comfort holding multiple competing hypotheses"
  ],
  "growth_tips_en": [
    "Set strict timeboxes for analysis to avoid analysis paralysis",
    "Ship 70%-ready outputs and iterate, instead of polishing in private",
    "Use peer rubber-ducking to externalize the overthink loop",
    "Adopt a daily one-thing-shipped ritual to build momentum",
    "Externalize anxiety to a journal to reclaim cognitive bandwidth"
  ],
  "career_directions": [
    "data_scientist",
    "strategy_consultant",
    "ai_research_engineer",
    "academic_researcher",
    "policy_analyst",
    "quant_analyst"
  ],
  "share_lines_en": [
    "I'm IA. My personality is just Stack Overflow with trust issues.",
    "I'm IA. I overthink my overthinking. Also this sentence.",
    "I'm IA. 4.3% rare. I'd celebrate but I'm too busy doubting myself."
  ],
  "ocean_modifiers": {
    "high_conscientiousness": "Your high conscientiousness pulls IA toward rigorous execution rather than pure theory.",
    "high_neuroticism": "Under stress, you need to externalize the loop — write it down or talk it out.",
    "high_openness": "Your novelty-seeking can pull you across fields; consider a meta-discipline as your home base."
  }
}
```

For brevity: clone this template for the other 23 cells. The label_en values come from spec Section 3.10's table:

| Cell | Label |
|------|-------|
| RI | The Bangalore Engineer |
| RA | The Maker-Artisan |
| RE | The Site Foreman |
| RC | The Disciplined Technician |
| IR | The Lab Realist |
| IA | The 3AM Chai Philosopher *(exemplar above)* |
| IS | The Empathic Investigator |
| IC | The Quiet Analyst |
| AI | The Indie Auteur |
| AR | The Craft Maverick |
| AS | The Bollywood Storyteller |
| AE | The Brand Auteur |
| SI | The Reflective Mentor |
| SA | The Healing Performer |
| SE | The Marwari Mentor |
| SC | The All-Knowing Aunty |
| ER | The Hustle Founder |
| EA | The Showrunner |
| ES | The Charismatic Closer |
| EC | The Marwari Mindset |
| CI | The Compliance Brain |
| CR | The Operations Backbone |
| CS | The Customer Steward |
| CE | The Sarkari Babu |

For each stub:
- `cell`: the 2-letter cell ID
- `label_en` / `label_hi`: from above table + simple Hindi transliteration (placeholder OK)
- `slogan_en`: 1-line placeholder ending in `[PLACEHOLDER — Phase 2.5]`
- `rarity_pct`: starter value 4.0 (will be calibrated from real data later)
- `core_insight_en` / `deep_description_en`: PLACEHOLDER strings noting Phase 2.5 ownership
- `strengths_en`: 5 generic-but-cell-relevant items (same template adjusted by main type)
- `growth_tips_en`: 5 generic items
- `career_directions`: list of 5-6 career_ids that match the cell (use exemplar Phase 2 mapping in Task 5)
- `share_lines_en`: 1-3 placeholder share copy lines
- `ocean_modifiers`: at least 1 high/low pair populated for testability; rest can be omitted

Author **all 24 stubs** in this step. Total file count: 24.

- [ ] **Step 5: Run cell loader test**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_cell_loader.py -v
```

Expected: 5 passed. If any test fails, the schema or data is mismatched — debug per error.

- [ ] **Step 6: Run full backend suite for regression**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 69 passed (60 Phase 1 + 4 from Task 1 + 5 from this task).

- [ ] **Step 7: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/cells.py backend/content/data/cells/ backend/tests/test_cell_loader.py
git commit -m "feat(backend): add cell content loader + 24 stub JSON files for all valid Holland cells"
```

---

## Task 3: Hand-curated 4 cell exemplars

**Files:**
- Modify: `backend/content/data/cells/{IA,SE,EC,SC}.json` (replace stub content)
- Create: `backend/tests/test_cell_exemplars.py`

We pick 4 cells representing the most common/recognizable Indian archetypes for the gold-standard exemplars. Phase 2.5 will follow this template to author the remaining 20 cells.

The 4 exemplars:
- **IA** — The 3AM Chai Philosopher (overthinker, common among Bangalore IT)
- **SE** — The Marwari Mentor (entrepreneurial mentor type)
- **EC** — The Marwari Mindset (entrepreneurial founder)
- **SC** — The All-Knowing Aunty (high prevalence; cultural staple)

- [ ] **Step 1: Write failing test for exemplar quality**

```python
"""tests/test_cell_exemplars.py — verify hand-curated exemplars meet quality bar."""
from content.cells import get_cell_content


EXEMPLAR_CELLS = ["IA", "SE", "EC", "SC"]


def test_exemplars_have_no_placeholder_text():
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        for field_value in [c.core_insight_en, c.deep_description_en]:
            assert "PLACEHOLDER" not in field_value, f"{cell_id} still has PLACEHOLDER text in content"


def test_exemplars_have_full_ocean_modifiers():
    """Exemplars should populate at least 4 OCEAN modifiers (gold standard for content authors)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        modifiers_set = sum(
            1 for v in c.ocean_modifiers.model_dump().values() if v is not None
        )
        assert modifiers_set >= 4, f"{cell_id} only has {modifiers_set} ocean_modifiers; exemplars need ≥4"


def test_exemplars_have_unique_share_lines():
    """Exemplars should have ≥3 unique share copy lines (gold standard)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert len(c.share_lines_en) >= 3, f"{cell_id} has only {len(c.share_lines_en)} share_lines_en"
        assert len(set(c.share_lines_en)) == len(c.share_lines_en), f"{cell_id} has duplicate share_lines_en"


def test_exemplars_deep_description_min_length():
    """Exemplars should have a real-length deep description (≥250 words / ~1500 chars)."""
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert len(c.deep_description_en) >= 1500, (
            f"{cell_id} deep_description is only {len(c.deep_description_en)} chars; needs ≥1500"
        )
```

Run: expect failures (stubs don't meet exemplar bar).

- [ ] **Step 2: Author the IA exemplar (full content)**

Replace `backend/content/data/cells/IA.json` with full hand-authored content. This file is the gold standard reference for Phase 2.5 authors — write it carefully.

Required:
- `core_insight_en`: 80-120 words, India-flavored, captures the IA archetype's essence (investigative + artistic, overthinker, philosopher of ordinary)
- `deep_description_en`: 1500+ chars (≈ 250-400 words), mixes IBTI dark humor with warmth, references real Indian Gen Z context (3 AM Chrome tabs about past, IIT/IIM comparisons, Bangalore tech scene context)
- `share_lines_en`: 3 distinct lines (at least one each of self-roast, surprise, challenge tone)
- `ocean_modifiers`: at least 4 of the 10 fields populated, each 1-2 sentences

Use this content (you can refine wording but preserve the structure):

```json
{
  "cell": "IA",
  "label_en": "The 3AM Chai Philosopher",
  "label_hi": "Sochne Wala",
  "slogan_en": "You overthink your overthinking. Also this sentence.",
  "rarity_pct": 4.3,
  "core_insight_en": "Your brain is 87 Chrome tabs and 86 of them are about your past. You think more before breakfast than most people do all week — research papers, life decisions, weird connections between things nobody else is putting together. Sharma ji's beta got into IIM and you're still in bed mapping career trajectory #47. The world calls it overthinking. You call it staying loyal to the truth.",
  "deep_description_en": "You're the friend everyone calls at 3 AM when their world is ending — not because you fix it, but because you're already awake, already thinking, and you actually care enough to spiral with them. You read three books a month, none of them assigned. You've abandoned five different career plans in the last year and each one taught you something that's still rattling around in your head. Your LinkedIn says 'Software Engineer @ TCS' but your soul is a chai-shop philosopher with a Notion full of unfinished essays. India calls people like you 'over-educated,' 'too-emotional,' or 'na-laayak' — but the truth is you're the person who'd actually fix the things everyone else just complains about, IF you ever stopped doubting yourself long enough to ship. The IIT-or-IIM script your family wrote for you doesn't fit because the script doesn't have a column for 'sees patterns nobody asked you to see.' Your strength is the one nobody talks about in placement training: you can sit with ambiguity without flinching, hold three competing hypotheses without getting attached, and explain why a Bollywood plot is actually a microcosm of Indian middle-class anxiety in three sentences. The danger is the same thing in reverse — you'll spend three months of late-night research on whether to take a job, then take the job, then spend another three months researching whether the job was right. Strategy consulting, data science, academic research, and policy analysis are not just paychecks for you — they're the rare professions where 'thinking too much' is the actual job description. Stop apologizing. Find a manager who values depth over speed. And ship something every Friday, even if you don't think it's ready. You're never going to think it's ready. That's the price of being IA.",
  "strengths_en": [
    "Pattern recognition across disparate fields where others see only noise",
    "Strategic foresight under ambiguity — you can sit in 'I don't know' without panicking",
    "Independent learning without external prompts — you'll teach yourself anything that interests you",
    "Synthesis of mixed signals into a coherent thesis nobody else saw coming",
    "Holding multiple competing hypotheses simultaneously without forcing premature closure"
  ],
  "growth_tips_en": [
    "Set strict 30-minute timeboxes for any analysis; commit to a decision when timer rings",
    "Ship 70%-ready writing publicly each Friday — your bar is too high for first drafts",
    "Use peer rubber-ducking: schedule weekly 15-minute calls to externalize the overthink loop",
    "Adopt a daily 'one tangible thing shipped' ritual to break analysis-paralysis cycles",
    "Externalize anxiety to a structured journal so it stops occupying foreground cognition"
  ],
  "career_directions": [
    "data_scientist",
    "strategy_consultant",
    "ai_research_engineer",
    "academic_researcher",
    "policy_analyst",
    "quant_analyst"
  ],
  "share_lines_en": [
    "I'm IA. My personality is just Stack Overflow with trust issues.",
    "Got IA in this test. So apparently 4.3% of Indians are exactly this dramatic at 3 AM. Worth a try → [link]",
    "I'm IA. I overthink my overthinking. I overthought writing this caption."
  ],
  "ocean_modifiers": {
    "high_conscientiousness": "Your high conscientiousness pulls IA toward rigorous execution rather than pure theory — you'll actually finish the research paper, not just plan it for two months.",
    "high_neuroticism": "Under stress, you need to externalize the loop — write it down, talk it out, anything to stop your brain from running the same rehearsal at 3 AM.",
    "high_openness": "Your novelty-seeking can pull you across too many fields; consider committing to a 'meta-discipline' as your home base, then range freely.",
    "high_extraversion": "If you've got high extraversion mixed with IA, you're a teacher in disguise — you can translate complex ideas to non-experts in a way most analysts can't.",
    "low_agreeableness": "Low-A IAs make brutal critics; channel this into editing/peer-review work rather than client-facing roles where the same instinct burns bridges."
  }
}
```

- [ ] **Step 3: Author the SE exemplar**

Replace `backend/content/data/cells/SE.json` with hand-authored content following the IA template's structure. Theme: "The Marwari Mentor" — Social-dominant + Enterprising-supporting. Common archetype: senior sales coach, HR partner who became an entrepreneur, education leader who built a school from scratch.

Sample minimum content (refine in implementation):

```json
{
  "cell": "SE",
  "label_en": "The Marwari Mentor",
  "label_hi": "Salah-Kar",
  "slogan_en": "You don't run the business. You raise the people who do.",
  "rarity_pct": 5.1,
  "core_insight_en": "Every team you've ever joined had a 'before you' and an 'after you.' You don't lead by command — you lead by lifting. You spot the kid in the corner with the spark before HR notices, and three years later that kid is running a department. People say 'Sharma uncle changed my life.' For most people, that's a compliment. For you, it's a job description.",
  "deep_description_en": "...250-400 words on Marwari Mentor archetype, mentor capital, building people not just businesses, balancing warmth with commercial discipline, the trap of losing your own career to lifting others, the Indian context of joint-family elder-mentor figures who become bosses, etc...",
  "strengths_en": ["...5 strengths covering coaching, EQ, network depth, business pragmatism, retention/loyalty..."],
  "growth_tips_en": ["...5 tips covering boundaries, own-career advocacy, written legacy, scaling beyond direct reports, mentor burnout..."],
  "career_directions": ["sales_manager", "hr_business_partner", "education_administrator", "founders_office", "executive_coach", "ngo_director"],
  "share_lines_en": ["I'm SE. Half my team is now my competitor and I'm fine with that.", "...", "..."],
  "ocean_modifiers": {"high_agreeableness": "...", "high_neuroticism": "...", "high_extraversion": "...", "high_conscientiousness": "..."}
}
```

(Implement the full content; I've abbreviated the template here.)

- [ ] **Step 4: Author the EC exemplar (Marwari Mindset / Empire Builder)**

Replace `backend/content/data/cells/EC.json`. Theme: Enterprising-dominant + Conventional-supporting. Founder/investor archetype.

```json
{
  "cell": "EC",
  "label_en": "The Marwari Mindset",
  "label_hi": "Vyapari Akal",
  "slogan_en": "You think in margins even during a wedding.",
  "rarity_pct": 3.1,
  "core_insight_en": "...80-120 words on Marwari mindset: portfolio thinking, Excel as a personality, multi-generational wealth building, pattern of compound returns, but also the loneliness of always optimizing...",
  "deep_description_en": "...250-400 words covering bania family business legacy, modern startup version, the difference between Marwari-mindset-EC and pure-E hustle-founder ER, when EC works (capital allocation, multi-business empires, family offices) and when it fails (creative work, deep tech R&D), the Indian context of business families across Rajasthan/Gujarat...",
  "strengths_en": ["Capital allocation across volatile environments", "Multi-business mental model (portfolio, not single bet)", "Generational time horizon (compound returns)", "Risk-adjusted decision making", "Detail-orientation under scale"],
  "growth_tips_en": ["Don't optimize all your relationships like spreadsheets", "Hire creative talent and resist the urge to micromanage their P&L", "Take six weeks off — your business won't collapse and you'll be a better owner", "Invest in technical advisors before you understand the field, not after", "Rotate between 'operator mode' and 'investor mode' deliberately"],
  "career_directions": ["startup_founder", "investment_analyst", "family_office_principal", "private_equity_associate", "cross_border_ecommerce", "wealth_advisor"],
  "share_lines_en": ["I'm EC. I don't have hobbies. I have portfolios.", "...", "..."],
  "ocean_modifiers": {"high_conscientiousness": "...", "low_agreeableness": "...", "high_extraversion": "...", "low_openness": "..."}
}
```

(Implement the full content.)

- [ ] **Step 5: Author the SC exemplar (All-Knowing Aunty)**

Replace `backend/content/data/cells/SC.json`. Theme: Social-dominant + Conventional-supporting. The cultural staple — community knowledge keeper, HR matriarch, family-network operator.

```json
{
  "cell": "SC",
  "label_en": "The All-Knowing Aunty",
  "label_hi": "Sab-Jaanne-Wali Aunty",
  "slogan_en": "You know everyone's salary. Your parents don't. Yet.",
  "rarity_pct": 6.1,
  "core_insight_en": "...80-120 words: encyclopedic memory of who-married-whom, who-got-into-which-college, who-divorced-whom; the operating system of Indian middle-class community life; runs the WhatsApp groups; can find any kid a job; can find any kid a spouse; pre-Internet Google for the family network...",
  "deep_description_en": "...250-400 words covering aunty culture as actually-essential infrastructure, the difference between gossip-aunty and matriarch-aunty, the modern career version (HR, customer success, community management), how to lean into the strength without becoming the joke, the underrated commercial value of knowing-everyone-and-their-cousin in a country where networks beat resumes, etc...",
  "strengths_en": ["Encyclopedic recall of names, roles, relationships, and timelines", "Network depth + active maintenance (you don't lose touch)", "Reading the room across generational and class lines", "Conflict de-escalation through 'I know everyone' soft power", "Community-scale information synthesis"],
  "growth_tips_en": ["Channel the gossip instinct into structured writing (newsletters, reports)", "Build a digital CRM for your network — your memory is good, but it won't last forever", "Resist the urge to give unsolicited advice; offer it 1 in 5 times", "Find a domain (HR, partnerships, alumni) where 'aunty mode' is the actual job description", "Schedule alone-time deliberately; you'll burn out on always being 'on' for the network"],
  "career_directions": ["hr_business_partner", "customer_success_manager", "alumni_engagement", "community_manager", "ngo_program_director", "wedding_planner"],
  "share_lines_en": ["I'm SC. I know your salary. Your parents don't. Yet.", "...", "..."],
  "ocean_modifiers": {"high_extraversion": "...", "high_agreeableness": "...", "high_conscientiousness": "...", "low_openness": "..."}
}
```

(Implement the full content.)

- [ ] **Step 6: Run exemplar tests**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_cell_exemplars.py -v
```

Expected: 4 passed (one test per exemplar quality dimension).

- [ ] **Step 7: Run full suite**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 73 passed (69 prior + 4 new exemplar tests).

- [ ] **Step 8: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/data/cells/IA.json backend/content/data/cells/SE.json backend/content/data/cells/EC.json backend/content/data/cells/SC.json backend/tests/test_cell_exemplars.py
git commit -m "feat(content): hand-curate 4 cell exemplars (IA, SE, EC, SC) as gold standard for Phase 2.5"
```

---

## Task 4: Career library schema + loader + 40 stub careers

**Files:**
- Create: `backend/content/careers.py`
- Create: `backend/content/data/careers/library.json`
- Create: `backend/tests/test_career_loader.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_career_loader.py"""
import pytest

from content.careers import get_career, get_careers_for_cell, load_career_library
from content.models import CareerEntry


def test_career_library_size():
    library = load_career_library()
    assert len(library) >= 40, f"need at least 40 careers, got {len(library)}"


def test_career_entries_validate():
    library = load_career_library()
    for career_id, entry in library.items():
        assert isinstance(entry, CareerEntry)
        assert entry.career_id == career_id


def test_get_career_known():
    c = get_career("data_scientist")
    assert c.career_id == "data_scientist"
    assert "Razorpay" in c.indian_companies or "Swiggy" in c.indian_companies


def test_get_career_unknown_raises():
    with pytest.raises(KeyError):
        get_career("astronaut_to_mars")


def test_get_careers_for_cell_returns_list():
    """For a known cell, return the careers it points to in priority order."""
    careers = get_careers_for_cell("IA")
    assert len(careers) >= 3
    assert all(isinstance(c, CareerEntry) for c in careers)
    # First career listed in IA's career_directions field should be first in result
    from content.cells import get_cell_content
    expected_first_id = get_cell_content("IA").career_directions[0]
    assert careers[0].career_id == expected_first_id


def test_career_distribution_across_industries():
    """v1 target distribution: 12 IT, 6 finance, 6 media/arts, 4 edu/research,
    5 sales/ops, 3 entrepreneurship, 2 govt, 2 service. Allow ±2 per category."""
    library = load_career_library()
    # This is a rough sanity check — just verify size + a few canonical categories
    assert any("data" in c.career_id or "engineer" in c.career_id or "developer" in c.career_id for c in library.values()), "no IT roles"
    assert any("financial" in c.career_id or "investment" in c.career_id or "analyst" in c.career_id for c in library.values()), "no finance roles"
```

Run: expect failure.

- [ ] **Step 2: Implement `backend/content/careers.py`**

```python
"""Career library loader — single JSON file with all 40 entries."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from content.models import CareerEntry

_HERE = Path(__file__).resolve().parent
_LIBRARY_PATH = _HERE / "data" / "careers" / "library.json"


@lru_cache(maxsize=1)
def load_career_library() -> dict[str, CareerEntry]:
    with open(_LIBRARY_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    library: dict[str, CareerEntry] = {}
    for career_id, entry_dict in raw.items():
        if "career_id" not in entry_dict:
            entry_dict = {**entry_dict, "career_id": career_id}
        library[career_id] = CareerEntry.model_validate(entry_dict)
    return library


def get_career(career_id: str) -> CareerEntry:
    library = load_career_library()
    if career_id not in library:
        raise KeyError(f"unknown career: {career_id!r}")
    return library[career_id]


def get_careers_for_cell(cell_id: str) -> list[CareerEntry]:
    """Return ordered list of CareerEntry for a cell's career_directions."""
    from content.cells import get_cell_content
    cell = get_cell_content(cell_id)
    return [get_career(cid) for cid in cell.career_directions]
```

- [ ] **Step 3: Create `backend/content/data/careers/library.json` with 40 stub entries**

The career library covers ~75–78 careers — expanded from the spec's 40 because
cell stubs (Task 2) reference broader RIASEC-thematic professions that better
differentiate between cells. Distribution remains spec-aligned by industry but
each industry has more roles:

- **IT (~14)**: data_scientist, software_engineer, devops_engineer, ai_research_engineer, data_engineer, backend_developer, mobile_developer, frontend_developer, qa_engineer, sre, security_engineer, ml_engineer, embedded_engineer, technician
- **Engineering (hands-on, ~5)**: electrical_engineer, mechanical_engineer, maintenance_engineer, manufacturing_lead, site_supervisor
- **Finance (~7)**: financial_analyst, investment_analyst, quant_analyst, audit_associate, wealth_advisor, risk_analyst, compliance_officer
- **Media/Arts (~10)**: screenwriter, content_creator, brand_strategist, fashion_designer, indie_filmmaker, creative_director, photographer, animator, film_producer, kol_creator
- **Education/Research (~8)**: academic_researcher, education_administrator, edtech_curriculum_designer, school_teacher, counseling_psychologist, clinical_psychologist, art_therapist, drama_teacher
- **Sales/Ops (~10)**: sales_manager, business_development, customer_success_manager, operations_manager, hr_business_partner, project_manager, brand_manager, training_manager, public_relations, customer_success
- **Entrepreneurship/Investing (~6)**: startup_founder, founders_office, family_office_principal, private_equity_associate, cross_border_ecommerce, product_manager
- **Government/Public (~4)**: policy_analyst, public_administration, legal_associate, public_health_researcher
- **Service/Community (~7)**: alumni_engagement, ngo_program_director, ngo_advisor, community_manager, wedding_planner, administrative_lead, child_psychologist
- **Specialty cross-cutting (~6)**: strategy_consultant, executive_coach, media_manager, concept_artist, industrial_designer, product_designer, architect

Total: ~75–78 careers. The exact set is enumerated by `find_orphan_career_references()` (Task 5) once Tasks 4 + 2 are both green.

Each stub follows this template (example for `data_scientist`):

```json
{
  "data_scientist": {
    "name_en": "Data Scientist",
    "name_hi": "Aankde Vigyani / डेटा साइंटिस्ट",
    "tagline_en": "Turn chaos into signal",
    "why_match": {
      "IA": "PLACEHOLDER — why IA matches data_scientist (1 line)",
      "IC": "PLACEHOLDER — why IC matches data_scientist (1 line)",
      "IR": "PLACEHOLDER — why IR matches data_scientist (1 line)"
    },
    "indian_companies": ["Razorpay", "Swiggy", "Flipkart", "Mu Sigma", "Fractal Analytics", "TCS Research"],
    "salary_inr": {"entry": "6L", "mid": "12L–22L", "senior": "30L–80L"},
    "education_path": [
      "B.Tech CSE/Stats",
      "Master's preferred for research roles",
      "Online: Coursera/DataCamp/Kaggle"
    ],
    "city_distribution": ["Bangalore", "Hyderabad", "Pune", "Gurugram"]
  },
  ...
}
```

For all 40 stubs, follow the pattern. PLACEHOLDER strings in `tagline`, `why_match` values, and (acceptable for stubs) sparse `salary_inr` ranges. Phase 2.5 content authors will fill in.

For `salary_inr`, use Indian lakh notation: e.g., entry `"4L"`, mid `"8L–15L"`, senior `"20L–60L"`. Estimates based on Glassdoor/AmbitionBox; refine in Phase 2.5.

Author all 40 entries in this step. Total file: 1 large JSON file at `backend/content/data/careers/library.json`.

- [ ] **Step 4: Run career loader test**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_career_loader.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Run full suite**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 79 passed (73 prior + 6 new).

- [ ] **Step 6: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/careers.py backend/content/data/careers/ backend/tests/test_career_loader.py
git commit -m "feat(backend): add career library loader + 40 stub entries spanning IT/finance/media/edu/sales/entrep/govt/service"
```

---

## Task 5: Cross-reference validator (cell ↔ career integrity)

**Files:**
- Create: `backend/content/validators.py`
- Create: `backend/tests/test_content_validators.py`

We need a CI-time check that catches authoring errors: every `career_id` referenced in any cell must exist in the career library, and every cell mentioned in any career's `why_match` must be a valid 24-cell ID.

- [ ] **Step 1: Write failing test**

```python
"""tests/test_content_validators.py — cross-reference integrity."""
from content.validators import (
    find_orphan_career_references,
    find_unknown_cells_in_why_match,
    validate_content_integrity,
)


def test_no_orphan_career_references():
    """Every career_id mentioned in any cell.career_directions exists in the library."""
    orphans = find_orphan_career_references()
    assert orphans == [], f"orphan career references: {orphans}"


def test_no_unknown_cells_in_why_match():
    """Every cell mentioned in any career.why_match is a valid 24-cell ID."""
    unknowns = find_unknown_cells_in_why_match()
    assert unknowns == [], f"unknown cell IDs in why_match: {unknowns}"


def test_validate_content_integrity_runs_clean():
    """Composite check returning structured results; all green = healthy library."""
    result = validate_content_integrity()
    assert result["orphan_career_refs"] == []
    assert result["unknown_cells_in_why_match"] == []
    assert result["cells_with_zero_careers"] == []
```

Run: expect failure.

- [ ] **Step 2: Implement `backend/content/validators.py`**

```python
"""Cross-reference integrity checks for cell + career content."""

from __future__ import annotations

from content.careers import load_career_library
from content.cells import load_all_cells
from services.scoring.archetype import VALID_CELLS_24


def find_orphan_career_references() -> list[tuple[str, str]]:
    """Return [(cell_id, career_id)] tuples where the career_id is not in the library."""
    cells = load_all_cells()
    library = load_career_library()
    library_ids = set(library.keys())
    orphans: list[tuple[str, str]] = []
    for cell_id, cell in cells.items():
        for career_id in cell.career_directions:
            if career_id not in library_ids:
                orphans.append((cell_id, career_id))
    return orphans


def find_unknown_cells_in_why_match() -> list[tuple[str, str]]:
    """Return [(career_id, cell_id)] tuples where why_match references a non-24-cell."""
    library = load_career_library()
    valid = set(VALID_CELLS_24)
    unknowns: list[tuple[str, str]] = []
    for career_id, entry in library.items():
        for cell_id in entry.why_match.keys():
            if cell_id not in valid:
                unknowns.append((career_id, cell_id))
    return unknowns


def find_cells_with_zero_careers() -> list[str]:
    """Cells with empty career_directions (a Phase 2.5 hard error)."""
    cells = load_all_cells()
    return [cell_id for cell_id, c in cells.items() if not c.career_directions]


def validate_content_integrity() -> dict:
    return {
        "orphan_career_refs": find_orphan_career_references(),
        "unknown_cells_in_why_match": find_unknown_cells_in_why_match(),
        "cells_with_zero_careers": find_cells_with_zero_careers(),
    }
```

- [ ] **Step 3: Run validator tests**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_content_validators.py -v
```

Expected: 3 passed if Tasks 2-4 stubs are internally consistent. If failures emerge, the failure messages will print the orphan IDs — fix by either adding the missing career stubs to library.json OR removing the dangling reference from the cell file.

- [ ] **Step 4: Run full suite**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 82 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/validators.py backend/tests/test_content_validators.py
git commit -m "feat(backend): add content integrity validators (orphan careers, unknown cells, empty cells)"
```

---

## Task 6: Hand-curate 8 career exemplars

**Files:**
- Modify: `backend/content/data/careers/library.json` (replace 8 stub entries with full content)
- Create: `backend/tests/test_career_exemplars.py`

We pick 8 careers that exemplify the spread (IT, finance, media, edu, sales, founder, govt, service). Phase 2.5 follows this template for the remaining 32.

The 8 exemplars: `data_scientist`, `strategy_consultant`, `screenwriter`, `school_teacher`, `sales_manager`, `startup_founder`, `policy_analyst`, `customer_success_manager`.

- [ ] **Step 1: Write failing exemplar quality test**

```python
"""tests/test_career_exemplars.py"""
from content.careers import get_career


EXEMPLARS = [
    "data_scientist", "strategy_consultant", "screenwriter", "school_teacher",
    "sales_manager", "startup_founder", "policy_analyst", "customer_success_manager",
]


def test_exemplars_have_no_placeholder():
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        for cell_id, why in c.why_match.items():
            assert "PLACEHOLDER" not in why, f"{career_id}.why_match[{cell_id}] has PLACEHOLDER"
        assert "PLACEHOLDER" not in c.tagline_en, f"{career_id} tagline_en still placeholder"


def test_exemplars_have_realistic_companies():
    """Exemplars list 4-8 real Indian companies (no placeholder names)."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert 4 <= len(c.indian_companies) <= 8
        for company in c.indian_companies:
            assert "PLACEHOLDER" not in company


def test_exemplars_have_at_least_3_why_match_cells():
    """Each exemplar career should describe matches for at least 3 cells."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert len(c.why_match) >= 3, f"{career_id} only matches {len(c.why_match)} cells"


def test_exemplars_have_complete_salary_range():
    """Exemplars have non-empty entry/mid/senior salary."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert c.salary_inr.entry and c.salary_inr.mid and c.salary_inr.senior
        # Each should contain "L" (lakh notation)
        assert "L" in c.salary_inr.entry
        assert "L" in c.salary_inr.mid
        assert "L" in c.salary_inr.senior
```

Run: expect failures (stubs have PLACEHOLDER strings).

- [ ] **Step 2: Author the 8 exemplars**

For each of the 8 careers, replace the stub in `library.json` with full hand-authored content. Use this template (showing `data_scientist` fully fleshed):

```json
"data_scientist": {
  "name_en": "Data Scientist",
  "name_hi": "Aankde Vigyani / डेटा साइंटिस्ट",
  "tagline_en": "Turn chaos into signal — India's fintech and consumer-internet sectors are on fire for this skill.",
  "why_match": {
    "IA": "Your pattern-recognition obsession plus tolerance for ambiguous data is the actual job description. Where others see noise, you see the model.",
    "IC": "Your numerical brain plus structured pipeline mindset means you'll go from analyst to ML engineer faster than your peers; comfort with rigor is the moat.",
    "IR": "Your engineering-first instinct (load the data, profile it, automate it) makes you the rare data scientist who ships production code, not just notebooks."
  },
  "indian_companies": ["Razorpay", "Swiggy", "Flipkart", "Mu Sigma", "Fractal Analytics", "TCS Research", "Cred", "PhonePe"],
  "salary_inr": {"entry": "8L", "mid": "16L–28L", "senior": "35L–90L"},
  "education_path": [
    "B.Tech in CSE / Stats / EE; or B.Sc Math/Stats with self-taught Python",
    "Master's recommended for research roles (IIIT, IIT, IISc preferred)",
    "Online portfolios: Kaggle competitions, GitHub side projects, technical blog",
    "Internships at consumer-internet companies (Swiggy/PhonePe/Flipkart) > pure consulting"
  ],
  "city_distribution": ["Bangalore", "Hyderabad", "Pune", "Gurugram", "Mumbai"]
}
```

Repeat the depth-of-content pattern for the other 7 careers. Each `why_match` entry should be 1-2 sentences with India-specific context (Sharma ji, EMI, IIT/IIM, Bangalore IT, Marwari business, etc., where it fits naturally — don't force).

- [ ] **Step 3: Run exemplar tests**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_career_exemplars.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Run full suite**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 86 passed (82 prior + 4 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/content/data/careers/library.json backend/tests/test_career_exemplars.py
git commit -m "feat(content): hand-curate 8 career exemplars across IT/finance/media/edu/sales/founder/govt/service"
```

---

## Task 7: Milestone copy module

**Files:**
- Create: `backend/services/milestone_copy.py`
- Create: `backend/tests/test_milestone_copy.py`

The frontend renders a milestone screen after Q10/Q20/Q30/Q40 with a progress ring + a single line of encouragement. The backend exposes the lines as a typed module so the frontend stays language-aware (English v1; Hindi pool added v2).

- [ ] **Step 1: Write failing test**

```python
"""tests/test_milestone_copy.py"""
from services.milestone_copy import (
    MILESTONE_THRESHOLDS,
    get_copy_for_milestone,
    get_milestone_at,
)


def test_thresholds_match_design():
    assert MILESTONE_THRESHOLDS == (10, 20, 30, 40)


def test_milestone_at_returns_threshold_or_none():
    assert get_milestone_at(10) == 10
    assert get_milestone_at(20) == 20
    assert get_milestone_at(40) == 40
    assert get_milestone_at(15) is None
    assert get_milestone_at(45) is None
    assert get_milestone_at(0) is None


def test_get_copy_for_each_milestone():
    for m in MILESTONE_THRESHOLDS:
        copy = get_copy_for_milestone(m, seed="test-seed")
        assert isinstance(copy, str)
        assert len(copy) >= 10
        assert len(copy) <= 200


def test_get_copy_deterministic_per_seed():
    a = get_copy_for_milestone(20, seed="X")
    b = get_copy_for_milestone(20, seed="X")
    assert a == b


def test_get_copy_unknown_milestone_raises():
    import pytest
    with pytest.raises(ValueError):
        get_copy_for_milestone(15, seed="X")
```

- [ ] **Step 2: Implement `backend/services/milestone_copy.py`**

```python
"""Milestone copy for Q10/Q20/Q30/Q40 progress screens.

Each milestone has a small pool of Hinglish-flavored encouragement strings.
The selector uses a seeded RNG so the same user sees consistent copy across
re-renders within a session, but different users see variety.
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
    """Return the milestone threshold for the given 1-indexed question count, or None."""
    return question_index if question_index in MILESTONE_THRESHOLDS else None


def get_copy_for_milestone(milestone: int, seed: str) -> str:
    """Pick one milestone copy line, deterministic per (milestone, seed)."""
    if milestone not in _COPY_POOL:
        raise ValueError(f"unknown milestone {milestone!r}; must be one of {MILESTONE_THRESHOLDS}")
    rng = random.Random(f"{seed}::milestone::{milestone}")
    pool = _COPY_POOL[milestone]
    return rng.choice(pool)
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_milestone_copy.py -v
```

Expected: 5 passed.

- [ ] **Step 4: Run full suite**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 91 passed (86 prior + 5 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/services/milestone_copy.py backend/tests/test_milestone_copy.py
git commit -m "feat(backend): add milestone copy module with deterministic per-seed selection"
```

---

## Task 8: E2E content composition test

**Files:**
- Create: `backend/tests/test_content_composition.py`

Final integration check: run the Phase 1 pipeline (select → answer → score → archetype), then use the resulting `archetype_cell` to fetch cell content + look up matching careers. Verify the composed report data has all the fields a frontend would need to render.

- [ ] **Step 1: Write failing test**

```python
"""tests/test_content_composition.py — E2E: pipeline + content lookup → composed report."""
from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from questions.selector import select_45_questions
from services.milestone_copy import get_copy_for_milestone
from services.scoring.archetype import derive_archetype_cell
from services.scoring.holland_code import compute_holland_code
from services.scoring.ocean import compute_ocean_percentiles, compute_ocean_scores
from services.scoring.riasec import compute_riasec_scores


def test_compose_report_for_synthetic_user():
    """Full simulation: select questions, answer, score, derive cell, fetch content, fetch careers."""
    demographic = {"DEM_STAGE": "experienced", "DEM_AGE": "25_29", "DEM_TOP_PRESSURE": "career"}
    questions = select_45_questions(demographic, seed="content-e2e-1")

    answers: dict[str, int] = {}
    for i, q in enumerate(questions):
        if q.id.startswith("DEM_"):
            continue
        answers[q.id] = (i % 5) + 1

    riasec = compute_riasec_scores(answers)
    ocean = compute_ocean_scores(answers)
    ocean_pct = compute_ocean_percentiles(ocean)
    holland_code = compute_holland_code(riasec)
    cell_id = derive_archetype_cell(riasec, holland_code)

    # Fetch content + careers
    cell_content = get_cell_content(cell_id)
    careers = get_careers_for_cell(cell_id)

    # Verify composition shape
    assert cell_content.cell == cell_id
    assert len(cell_content.strengths_en) == 5
    assert len(careers) >= 3
    assert all(c.salary_inr.entry for c in careers)


def test_compose_milestone_copy_for_each_threshold():
    """Each milestone returns a non-empty string deterministically per seed."""
    for milestone in (10, 20, 30, 40):
        copy = get_copy_for_milestone(milestone, seed="e2e-milestone")
        assert copy and len(copy) >= 10


def test_composed_report_has_no_placeholder_for_exemplar_cells():
    """If user lands on one of the 4 cell exemplars, full content must be available."""
    for cell_id in ("IA", "SE", "EC", "SC"):
        c = get_cell_content(cell_id)
        assert "PLACEHOLDER" not in c.core_insight_en, f"{cell_id} core_insight has PLACEHOLDER"
        assert "PLACEHOLDER" not in c.deep_description_en, f"{cell_id} deep_description has PLACEHOLDER"
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/test_content_composition.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Run full suite (final regression check)**

```bash
cd /Users/antonio/god/my_good_ipip/backend && pytest tests/ -v
```

Expected: 94 passed (91 prior + 3 new).

- [ ] **Step 4: Commit**

```bash
cd /Users/antonio/god/my_good_ipip && git add backend/tests/test_content_composition.py
git commit -m "feat(backend): add E2E content composition test (pipeline → cell content → careers)"
```

---

## Phase 2 Acceptance Criteria

After all 8 tasks complete, the following must hold:

- [ ] `pytest tests/ -v` returns ≥ 94 passing tests, 0 failures.
- [ ] `from content.cells import get_cell_content` and `from content.careers import get_career` are importable.
- [ ] `load_all_cells()` returns 24 entries, one per `VALID_CELLS_24`.
- [ ] `load_career_library()` returns ≥ 40 entries.
- [ ] All 4 cell exemplars (IA, SE, EC, SC) have full content (no PLACEHOLDER strings, ≥4 OCEAN modifiers, ≥3 unique share lines, ≥1500-char deep description).
- [ ] All 8 career exemplars have full content (no PLACEHOLDER, ≥3 why_match cells, complete salary range, ≥4 Indian companies).
- [ ] Cross-reference validators return clean: every cell's career_directions points to a real career; every career's why_match references a valid cell ID.
- [ ] Milestone copy module returns deterministic per-seed strings for each of Q10/Q20/Q30/Q40.
- [ ] All work committed in well-scoped commits with conventional messages.
- [ ] Phase 1 backend tests still pass (no regressions).

## Phase 2 → Spec Coverage

- ✅ S4 24-Cell Content Library — Tasks 1, 2, 3
- ✅ S5 Career Library — Tasks 4, 6
- ✅ Cross-reference integrity — Task 5
- ✅ Milestone copy (S2 §3.6 follow-up) — Task 7
- ✅ E2E content composition — Task 8
- ⏭ S6 Result Pages — Phase 4 (frontend)
- ⏭ S7 Auth & Payment — Phase 3
- ⏭ S8 Sharing — Phase 4

## Phase 2.5 — Out of Band

The 20 non-exemplar cells (RI, RA, RE, RC, IR, IS, IC, AI, AR, AS, AE, SI, SA, ER, EA, ES, CI, CR, CS) and ~70 non-exemplar careers are stubs after Phase 2. These get filled out in **Phase 2.5**, a content production sprint:

1. Antonio + GPT-4o run a batch generation script (`scripts/generate_content.py`, optional Task) using the 4 cell + 8 career exemplars as few-shot examples.
2. Native Indian copywriter reviews the generated batch, edits for cultural authenticity.
3. PR with the 20 + 32 filled-out files lands in a single content commit (no code changes needed — just JSON).
4. The exemplar tests + cross-reference validators catch regressions automatically.

This split keeps Phase 2 size bounded while ensuring the schemas + loaders + validators are battle-tested before the bulk content lands.

---

## Estimated Effort

~10-14 hours of engineering for 1 engineer (similar to Phase 1 by structural complexity, but content authoring of the 4+8 exemplars adds 3-5 hours of writing time). Phase 2.5 (bulk content) is additional 12-18 hours mostly outside engineering.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-28-careerdna-phase-2-content-library.md`.

**Two execution options:**

1. **Subagent-Driven (recommended, same as Phase 1)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans skill, batch execution with checkpoints.

---

## Phase 2 — COMPLETED 2026-04-28

All 8 tasks delivered via subagent-driven development with TDD + spec/code reviews per task.

**Final state:**
- 112 backend tests passing total (60 Phase 1 + 52 Phase 2)
- 15+ implementation/polish commits on `main` (commit range: `c9466d5` → `0c70831`)
- New packages: `backend/content/` (5 modules: models, cells, careers, validators, __init__) + `backend/services/milestone_copy.py`
- Content data: 24 cell JSONs + 78-entry career library (real Indian companies + Devanagari + lakh-notation salary)
- Hand-curated: 4 cell exemplars (IA/SE/EC/SC) + 8 career exemplars across industries
- Cross-reference integrity: 0 orphans / 0 unknowns / 0 empty cells / 8 dormant entries (informational, by design)
- All 24 cells × career integration data-complete (proven by E2E composition test)

**All Phase 2 acceptance criteria verified by final code reviewer.**

**Phase 3 prep follow-ups** (deferred, none blocking):
- Add `__all__` to each public `content/` module to lock public surface
- Add `clear_cache()` helpers to `cells.py` and `careers.py` for hot-reload support
- Add `min_length=1` constraint to `why_match: dict[CellId, str]` (catches empty-dict edge case)
- Document or implement `[link]` substitution helper before Phase 4 frontend
- Decide `city_distribution` schema split (city pills vs descriptors) before Phase 4

**Phase 2.5 prep** (out of band — content production sprint):
- Author full content for 20 non-exemplar cells (replacing PLACEHOLDER core_insight + deep_description)
- Author real why_match strings for 70 non-exemplar careers
- Native Indian copywriter review pass on the 4+8 exemplars
- All quality gates auto-apply via `_is_curated()` exemplar discovery — no test list maintenance

**Next**: Phase 3 plan (API/auth/payment refactor) — separate writing-plans pass.
