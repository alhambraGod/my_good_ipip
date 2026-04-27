# CareerDNA India · Phase 1 Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the question bank infrastructure (IPIP-NEO 120 + Holland RIASEC 60 + demographic + interest pool), L1.5 dynamic selection, hybrid scoring (RIASEC + OCEAN + Holland code + 24-cell archetype + MAST trigger), database schema migration, and pytest test suite. All backend, no API/UI changes yet (Phase 3+ for that).

**Architecture:** New `backend/questions/` modular package replacing monolithic `question_bank.py` (kept as compat shim). New `backend/services/scoring/` package replacing flat `scoring.py`. Forward-compat DB migration via existing `_ensure_assessment_columns` pattern. Existing `personalization.py` deprecated in favor of new selector but kept until Phase 3.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, SQLite (dev), Pydantic v2, pytest, pytest-asyncio.

**Spec source:** `docs/superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` (Sections 3 S1–S3, 4 Data Model)

---

## Task 1: Pytest infrastructure

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/pytest.ini`
- Create: `backend/tests/test_smoke.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add pytest to requirements**

```text
pydyf<0.12
jinja2==3.1.4
python-multipart==0.0.9
httpx==0.27.2
PyJWT==2.9.0
bcrypt==4.2.0
markdown==3.7
pytest==8.3.3
pytest-asyncio==0.24.0
```

Append the last two lines to `backend/requirements.txt`.

- [ ] **Step 2: Install dependencies**

```bash
conda activate my_good_ipip
cd backend && pip install -r requirements.txt
```

- [ ] **Step 3: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

- [ ] **Step 4: Create conftest.py**

```python
"""Shared pytest fixtures."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["PAYMENT_MODE"] = "mock"
    yield
```

- [ ] **Step 5: Write smoke test**

```python
"""tests/test_smoke.py — verify pytest setup works."""

def test_pytest_runs():
    assert True

def test_imports_work():
    from config import settings
    assert settings is not None
```

- [ ] **Step 6: Run smoke test**

```bash
cd backend && pytest tests/test_smoke.py -v
```

Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/pytest.ini backend/tests/
git commit -m "chore(backend): add pytest infrastructure with smoke test"
```

---

## Task 2: Question schema + JSON loaders

**Files:**
- Create: `backend/questions/models.py`
- Create: `backend/questions/holland_riasec.py`
- Create: `backend/questions/ipip_neo.py`
- Create: `backend/tests/test_question_loaders.py`

- [ ] **Step 1: Write failing test for Question model**

```python
"""tests/test_question_loaders.py"""
import pytest
from questions.models import Question, Instrument, ResponseType


def test_question_construction():
    q = Question(
        id="RIASEC_R_01",
        text_en="I like fixing mechanical problems.",
        instrument=Instrument.RIASEC,
        dimension="R",
        reverse=False,
        response_type=ResponseType.LIKERT_5,
    )
    assert q.id == "RIASEC_R_01"
    assert q.dimension == "R"
    assert q.weight == 1.0  # default
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && pytest tests/test_question_loaders.py::test_question_construction -v
```

Expected: FAIL — `ModuleNotFoundError: questions.models`

- [ ] **Step 3: Implement `backend/questions/models.py`**

```python
"""Question domain model — used by all loaders."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class Instrument(str, Enum):
    RIASEC = "riasec"
    IPIP = "ipip"
    DEMOGRAPHIC = "demographic"
    INTEREST = "interest"


class ResponseType(str, Enum):
    LIKERT_5 = "likert_5"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"


@dataclass
class Question:
    id: str
    text_en: str
    instrument: Instrument
    dimension: str
    reverse: bool = False
    response_type: ResponseType = ResponseType.LIKERT_5
    text_hi: str | None = None
    facet: str | None = None
    options: list[dict] | None = None
    scenes: list[str] = field(default_factory=list)
    role: Literal["core", "scene", "reverse", "filler"] = "core"
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    tags: list[str] = field(default_factory=list)
    weight: float = 1.0

    def to_api_payload(self) -> dict:
        """Return the public-facing JSON shape (excludes scoring metadata)."""
        return {
            "id": self.id,
            "text": self.text_en,
            "instrument": self.instrument.value,
            "response_type": self.response_type.value,
            "options": self.options,
        }
```

- [ ] **Step 4: Re-run, expect pass**

```bash
cd backend && pytest tests/test_question_loaders.py::test_question_construction -v
```

Expected: `1 passed`

- [ ] **Step 5: Add failing test for RIASEC loader**

Append to `tests/test_question_loaders.py`:

```python
from questions.holland_riasec import load_riasec_questions, RIASEC_TYPES


def test_load_riasec_60():
    qs = load_riasec_questions()
    assert len(qs) == 60, f"expected 60 RIASEC items, got {len(qs)}"
    # 10 per type
    by_dim: dict[str, int] = {}
    for q in qs:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for t in RIASEC_TYPES:
        assert by_dim[t] == 10, f"expected 10 items for {t}, got {by_dim.get(t, 0)}"
    # all forward-keyed (Holland convention)
    assert all(not q.reverse for q in qs)
    assert all(q.instrument == Instrument.RIASEC for q in qs)
```

Run: `pytest tests/test_question_loaders.py::test_load_riasec_60 -v` — Expected FAIL.

- [ ] **Step 6: Implement `backend/questions/holland_riasec.py`**

```python
"""Holland RIASEC 60-item question loader (from docs/Holland_RIASEC_60_questionbank.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from questions.models import Instrument, Question, ResponseType

RIASEC_TYPES = ["R", "I", "A", "S", "E", "C"]

_HERE = Path(__file__).resolve().parent
_BANK_PATH = _HERE.parent.parent / "docs" / "Holland_RIASEC_60_questionbank.json"


@lru_cache(maxsize=1)
def load_riasec_questions() -> list[Question]:
    with open(_BANK_PATH, encoding="utf-8") as f:
        bank = json.load(f)

    items = bank["items"]
    questions: list[Question] = []
    for it in items:
        questions.append(
            Question(
                id=f"RIASEC_{it['type']}_{it['item_index']:02d}",
                text_en=it["text_en"],
                instrument=Instrument.RIASEC,
                dimension=it["type"],
                reverse=False,
                response_type=ResponseType.LIKERT_5,
                role="core",
                tags=["holland", "career"],
            )
        )
    return questions


def get_riasec_by_id(question_id: str) -> Question | None:
    for q in load_riasec_questions():
        if q.id == question_id:
            return q
    return None
```

**Note:** This depends on `docs/Holland_RIASEC_60_questionbank.json` having `items` array with `type`, `item_index`, `text_en` fields. Verify the JSON shape:

```bash
cd backend && python -c "import json; b = json.load(open('../docs/Holland_RIASEC_60_questionbank.json')); print(list(b.keys())); print(b['items'][0] if 'items' in b else 'NO_ITEMS_KEY')"
```

If the JSON shape differs (e.g., grouped by type instead of flat items array), adjust the loader's parsing logic to match. Read the JSON top-level keys first and write a small parsing branch as needed. The test above (`len == 60`, `10 per type`, all RIASEC) will validate correctness regardless.

- [ ] **Step 7: Run RIASEC loader test**

```bash
cd backend && pytest tests/test_question_loaders.py::test_load_riasec_60 -v
```

Expected: PASS. If it fails, fix loader parsing per actual JSON shape.

- [ ] **Step 8: Add failing test for IPIP-NEO loader**

```python
from questions.ipip_neo import load_ipip_questions, OCEAN_DOMAINS


def test_load_ipip_120():
    qs = load_ipip_questions()
    assert len(qs) == 120
    by_dim: dict[str, int] = {}
    for q in qs:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in OCEAN_DOMAINS:
        assert by_dim[d] == 24, f"expected 24 items for {d}, got {by_dim.get(d, 0)}"
    # mix of forward and reverse keyed
    forward = sum(1 for q in qs if not q.reverse)
    reverse = sum(1 for q in qs if q.reverse)
    assert forward > 0 and reverse > 0
    assert all(q.instrument == Instrument.IPIP for q in qs)
    assert all(q.facet for q in qs), "every IPIP item should have a facet"
```

Run: expect FAIL.

- [ ] **Step 9: Implement `backend/questions/ipip_neo.py`**

```python
"""IPIP-NEO 120-item question loader (from docs/IPIP_NEO_120_questionbank.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from questions.models import Instrument, Question, ResponseType

OCEAN_DOMAINS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
DOMAIN_LETTER_TO_NAME = {"O": "openness", "C": "conscientiousness", "E": "extraversion", "A": "agreeableness", "N": "neuroticism"}

_HERE = Path(__file__).resolve().parent
_BANK_PATH = _HERE.parent.parent / "docs" / "IPIP_NEO_120_questionbank.json"


@lru_cache(maxsize=1)
def load_ipip_questions() -> list[Question]:
    with open(_BANK_PATH, encoding="utf-8") as f:
        bank = json.load(f)

    items = bank["items"]
    questions: list[Question] = []
    for it in items:
        domain_letter = it["domain"]
        questions.append(
            Question(
                id=f"IPIP_{it['facet']}_{it['item_index']:02d}",
                text_en=it["text_en"],
                instrument=Instrument.IPIP,
                dimension=DOMAIN_LETTER_TO_NAME[domain_letter],
                reverse=(it.get("keyed", "+") == "-"),
                response_type=ResponseType.LIKERT_5,
                facet=it["facet"],
                role="core",
                tags=["ipip", "ocean"],
            )
        )
    return questions
```

Verify JSON shape similarly:

```bash
cd backend && python -c "import json; b = json.load(open('../docs/IPIP_NEO_120_questionbank.json')); print(list(b.keys())); print(b['items'][0] if 'items' in b else 'NO_ITEMS_KEY')"
```

Adjust loader if field names differ.

- [ ] **Step 10: Run IPIP loader test**

```bash
cd backend && pytest tests/test_question_loaders.py -v
```

Expected: 3 passed.

- [ ] **Step 11: Commit**

```bash
git add backend/questions/__init__.py backend/questions/models.py backend/questions/holland_riasec.py backend/questions/ipip_neo.py backend/tests/test_question_loaders.py
git commit -m "feat(backend): add Question model + RIASEC 60 + IPIP-NEO 120 loaders"
```

(If `backend/questions/__init__.py` doesn't exist, create it as an empty file in this step.)

---

## Task 3: Demographic 5 + Interest pool

**Files:**
- Create: `backend/questions/demographic.py`
- Create: `backend/questions/interest_pool.py`
- Create: `backend/tests/test_demographic_interest.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_demographic_interest.py"""
import pytest
from questions.demographic import DEMOGRAPHIC_QUESTIONS, derive_profile_tags
from questions.interest_pool import INTEREST_POOL
from questions.models import Instrument


def test_demographic_count_and_shape():
    assert len(DEMOGRAPHIC_QUESTIONS) == 5
    for q in DEMOGRAPHIC_QUESTIONS:
        assert q.instrument == Instrument.DEMOGRAPHIC
        assert q.options is not None and len(q.options) >= 3
        assert q.id.startswith("DEM_")


def test_derive_profile_tags():
    answers = {"DEM_STAGE": "Working Professional", "DEM_TOP_PRESSURE": "Money/EMI"}
    tags = derive_profile_tags(answers)
    assert "experienced" in tags
    assert "EMI" in tags or "money" in tags


def test_interest_pool_size_and_shape():
    assert len(INTEREST_POOL) >= 30
    # Each item should have ocean dimension tag
    by_dim: dict[str, int] = {}
    for q in INTEREST_POOL:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    # at least 5 items per OCEAN dim so 16-pick selector has room
    for d in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        assert by_dim.get(d, 0) >= 5, f"only {by_dim.get(d, 0)} items for {d}"
```

Run: expect FAIL.

- [ ] **Step 2: Implement demographic**

`backend/questions/demographic.py`:

```python
"""5 demographic questions asked as Q1-5, before dynamic selection of remaining 40."""

from questions.models import Instrument, Question, ResponseType


DEMOGRAPHIC_QUESTIONS: list[Question] = [
    Question(
        id="DEM_STAGE",
        text_en="Which best describes you right now?",
        instrument=Instrument.DEMOGRAPHIC,
        dimension="meta",
        response_type=ResponseType.SINGLE_CHOICE,
        options=[
            {"value": "student", "label": "Student"},
            {"value": "fresher", "label": "Fresher (≤2 yr work experience)"},
            {"value": "experienced", "label": "Working Professional"},
            {"value": "switcher", "label": "Career Switcher"},
            {"value": "founder", "label": "Founder / Self-employed"},
        ],
    ),
    Question(
        id="DEM_AGE",
        text_en="Your age band",
        instrument=Instrument.DEMOGRAPHIC,
        dimension="meta",
        response_type=ResponseType.SINGLE_CHOICE,
        options=[
            {"value": "15_19", "label": "15–19"},
            {"value": "20_24", "label": "20–24"},
            {"value": "25_29", "label": "25–29"},
            {"value": "30_34", "label": "30–34"},
            {"value": "35_plus", "label": "35+"},
        ],
    ),
    Question(
        id="DEM_GENDER",
        text_en="Gender",
        instrument=Instrument.DEMOGRAPHIC,
        dimension="meta",
        response_type=ResponseType.SINGLE_CHOICE,
        options=[
            {"value": "male", "label": "Male"},
            {"value": "female", "label": "Female"},
            {"value": "nonbinary", "label": "Non-binary"},
            {"value": "private", "label": "Prefer not to say"},
        ],
    ),
    Question(
        id="DEM_CITY_TIER",
        text_en="Where do you live?",
        instrument=Instrument.DEMOGRAPHIC,
        dimension="meta",
        response_type=ResponseType.SINGLE_CHOICE,
        options=[
            {"value": "tier1", "label": "Tier-1 (Mumbai/Delhi/Bangalore/Chennai/Hyderabad/Pune)"},
            {"value": "tier2", "label": "Tier-2"},
            {"value": "tier3", "label": "Tier-3 / Town"},
            {"value": "outside_india", "label": "Outside India"},
        ],
    ),
    Question(
        id="DEM_TOP_PRESSURE",
        text_en="What's pressing you most these days?",
        instrument=Instrument.DEMOGRAPHIC,
        dimension="meta",
        response_type=ResponseType.SINGLE_CHOICE,
        options=[
            {"value": "career", "label": "Career direction"},
            {"value": "family", "label": "Family expectations"},
            {"value": "money", "label": "Money / EMI"},
            {"value": "self_doubt", "label": "Self-doubt"},
            {"value": "curious", "label": "Just curious"},
        ],
    ),
]


_STAGE_TAGS = {
    "student": ["student", "campus", "future-explore"],
    "fresher": ["fresher", "early-career", "first-job"],
    "experienced": ["experienced", "work-stress", "mid-career"],
    "switcher": ["switcher", "transition", "decision-fatigue"],
    "founder": ["founder", "hustle", "risk-tolerance"],
}

_PRESSURE_TAGS = {
    "career": ["career-uncertainty"],
    "family": ["family-pressure", "Sharma-ji-syndrome"],
    "money": ["EMI", "money", "financial-stress"],
    "self_doubt": ["self-doubt", "imposter"],
    "curious": [],
}


def derive_profile_tags(answers: dict[str, str]) -> list[str]:
    """Derive a list of profile tags from demographic answers, used by the selector to weight pool."""
    tags: list[str] = []
    stage = answers.get("DEM_STAGE")
    if stage in _STAGE_TAGS:
        tags.extend(_STAGE_TAGS[stage])
    pressure = answers.get("DEM_TOP_PRESSURE")
    if pressure in _PRESSURE_TAGS:
        tags.extend(_PRESSURE_TAGS[pressure])
    age = answers.get("DEM_AGE")
    if age in ("15_19", "20_24"):
        tags.append("gen-z")
    elif age in ("25_29", "30_34"):
        tags.append("millennial-early")
    return tags
```

- [ ] **Step 3: Curate `interest_pool.py`**

This is content authoring. The test only validates schema (≥30 items, ≥5 per OCEAN dim). The actual copy below is **starter content for v1**; expect Phase 2 to refine wording with native Indian copywriter review.

`backend/questions/interest_pool.py`:

```python
"""Indian-flavored IPIP-NEO 16-item interest pool — 30+ candidates, dynamic-selected at runtime.

Each item is double-coded:
  - dimension: maps to one OCEAN domain (for scoring)
  - tags: profile-tag affinities (for selector weighting)

Wording adopts IBTI-style Hinglish accents while preserving IPIP semantic intent."""

from questions.models import Instrument, Question, ResponseType


def _q(id: str, text: str, dim: str, reverse: bool, tags: list[str]) -> Question:
    return Question(
        id=id,
        text_en=text,
        instrument=Instrument.INTEREST,
        dimension=dim,
        reverse=reverse,
        response_type=ResponseType.LIKERT_5,
        role="scene",
        tags=tags,
    )


INTEREST_POOL: list[Question] = [
    # Openness (6 items)
    _q("INT_O_01", "Sharma ji ka beta got into IIM. Your first instinct: 'Let me explore what I actually want.'", "openness", False, ["family-pressure", "career-uncertainty", "student"]),
    _q("INT_O_02", "When EMI culture says 'safe path,' you secretly Google career switches at 2 AM.", "openness", False, ["EMI", "switcher", "millennial-early"]),
    _q("INT_O_03", "You read about a new field (AI / climate / Web3) and seriously consider pivoting.", "openness", False, ["future-explore", "experienced", "switcher"]),
    _q("INT_O_04", "You'd rather copy what worked for cousins than invent your own path.", "openness", True, ["family-pressure", "tradition"]),
    _q("INT_O_05", "Your weekend is spent on tutorials about a skill no one in your family understands.", "openness", False, ["future-explore", "self-driven"]),
    _q("INT_O_06", "You avoid decisions that require imagining yourself in a role you've never seen.", "openness", True, ["career-uncertainty", "self-doubt"]),

    # Conscientiousness (6)
    _q("INT_C_01", "Your Notion / Google Sheets is your second personality.", "conscientiousness", False, ["experienced", "founder", "early-career"]),
    _q("INT_C_02", "You miss deadlines because 'mood wasn't right'.", "conscientiousness", True, ["self-doubt", "student", "mid-career"]),
    _q("INT_C_03", "When EMI hits, you instinctively re-budget the next 3 months.", "conscientiousness", False, ["EMI", "money", "experienced"]),
    _q("INT_C_04", "You start a productivity app, abandon it, repeat. Currently on app #4.", "conscientiousness", True, ["millennial-early", "self-doubt"]),
    _q("INT_C_05", "You finish things you commit to — even when nobody's watching.", "conscientiousness", False, ["experienced", "founder", "mid-career"]),
    _q("INT_C_06", "Your room is a metaphor for your career: half done, vibe-based.", "conscientiousness", True, ["student", "fresher", "millennial-early"]),

    # Extraversion (6)
    _q("INT_E_01", "Wedding mein 200 log, you're the one telling the dulha old college stories.", "extraversion", False, ["gen-z", "millennial-early", "student"]),
    _q("INT_E_02", "Office party? You're already in the Uber home before pakode finished.", "extraversion", True, ["self-doubt", "experienced"]),
    _q("INT_E_03", "Public speaking is your karma — you light up, others find you exhausting.", "extraversion", False, ["founder", "fresher", "self-driven"]),
    _q("INT_E_04", "WhatsApp groups muted = you. All 47 of them.", "extraversion", True, ["self-doubt", "experienced", "millennial-early"]),
    _q("INT_E_05", "You prefer to text 'kal milte hai' — meeting people in person drains you.", "extraversion", True, ["self-doubt", "remote", "experienced"]),
    _q("INT_E_06", "When colleagues complain, you naturally take charge of fixing the energy.", "extraversion", False, ["founder", "experienced", "career"]),

    # Agreeableness (5)
    _q("INT_A_01", "Friend wants to borrow ₹5000. You say yes, regret quietly for 6 months.", "agreeableness", False, ["EMI", "self-doubt", "experienced"]),
    _q("INT_A_02", "When mom guilt-trips you about Sharma ji's beta, you stay polite no matter what.", "agreeableness", False, ["family-pressure", "self-doubt"]),
    _q("INT_A_03", "Office politics — you'd rather quit than play the game.", "agreeableness", False, ["self-doubt", "experienced", "switcher"]),
    _q("INT_A_04", "If aunty crosses a line, you'll cut her off mid-sentence.", "agreeableness", True, ["family-pressure", "self-driven"]),
    _q("INT_A_05", "Holding grudges takes too much energy. You forgive — eventually.", "agreeableness", False, ["mid-career", "experienced"]),

    # Neuroticism (7 — slightly extra to compensate for sensitivity)
    _q("INT_N_01", "It's 3 AM. You're awake. Career-related panic. Again.", "neuroticism", False, ["self-doubt", "career-uncertainty", "experienced"]),
    _q("INT_N_02", "Aunty asks salary at every wedding. Your gut: spiral. Your face: smile.", "neuroticism", False, ["family-pressure", "imposter", "self-doubt"]),
    _q("INT_N_03", "Your friend got promoted. You felt happy AND like the floor opened up.", "neuroticism", False, ["self-doubt", "millennial-early", "imposter"]),
    _q("INT_N_04", "Boss said 'we need to talk.' You're already drafting your resignation.", "neuroticism", False, ["self-doubt", "experienced", "imposter"]),
    _q("INT_N_05", "EMI day every month is a small heart attack.", "neuroticism", False, ["EMI", "money", "financial-stress"]),
    _q("INT_N_06", "You handle pressure without panic in most situations.", "neuroticism", True, ["experienced", "founder", "mid-career"]),
    _q("INT_N_07", "After rejection, you bounce back within a day.", "neuroticism", True, ["founder", "experienced", "self-driven"]),
]
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_demographic_interest.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/questions/demographic.py backend/questions/interest_pool.py backend/tests/test_demographic_interest.py
git commit -m "feat(backend): add 5 demographic questions + 30-item Indian-flavored interest pool"
```

---

## Task 4: Static 24 RIASEC selection

**Files:**
- Create: `backend/questions/riasec_static_24.py`
- Create: `backend/tests/test_riasec_static_24.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_riasec_static_24.py"""
from questions.riasec_static_24 import get_riasec_static_24
from questions.holland_riasec import RIASEC_TYPES


def test_static_24_size_and_coverage():
    selected = get_riasec_static_24()
    assert len(selected) == 24, f"expected 24, got {len(selected)}"

    by_dim: dict[str, int] = {}
    for q in selected:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1

    for t in RIASEC_TYPES:
        assert by_dim[t] == 4, f"expected 4 for {t}, got {by_dim.get(t, 0)}"


def test_static_24_is_deterministic():
    a = get_riasec_static_24()
    b = get_riasec_static_24()
    assert [q.id for q in a] == [q.id for q in b]


def test_static_24_subset_of_60():
    from questions.holland_riasec import load_riasec_questions
    selected = get_riasec_static_24()
    full_60 = load_riasec_questions()
    full_ids = {q.id for q in full_60}
    for q in selected:
        assert q.id in full_ids, f"{q.id} not in 60-bank"
```

Run: expect FAIL.

- [ ] **Step 2: Implement**

`backend/questions/riasec_static_24.py`:

```python
"""Static 24-item subset of Holland RIASEC 60 — same 24 items shown to ALL users.

Why static: RIASEC scores must be cross-user comparable so the resulting Holland
code maps to a stable archetype cell. If items varied per user, scores wouldn't
mean the same thing for cohort comparison.

Selection criteria (manual curation, hand-picked from the 60-item bank):
  - 4 items per RIASEC type
  - Prefer items that translate cleanly into Indian work/life contexts
  - Mix of vocational (career-leaning) and avocational (interest-leaning)
  - Avoid items requiring uncommon vocabulary or Western-only references
"""

from functools import lru_cache

from questions.holland_riasec import load_riasec_questions
from questions.models import Question

# Item indices per type, hand-selected from the 10-item-per-type RIASEC bank.
# Indices are 1-based and map to `item_index` field in the JSON bank.
# This list is the SOURCE OF TRUTH — adjust here when curators refine choices.
STATIC_24_ITEM_IDS: dict[str, list[str]] = {
    "R": ["RIASEC_R_01", "RIASEC_R_03", "RIASEC_R_05", "RIASEC_R_08"],
    "I": ["RIASEC_I_01", "RIASEC_I_03", "RIASEC_I_06", "RIASEC_I_09"],
    "A": ["RIASEC_A_01", "RIASEC_A_04", "RIASEC_A_06", "RIASEC_A_09"],
    "S": ["RIASEC_S_01", "RIASEC_S_03", "RIASEC_S_06", "RIASEC_S_08"],
    "E": ["RIASEC_E_01", "RIASEC_E_03", "RIASEC_E_06", "RIASEC_E_09"],
    "C": ["RIASEC_C_01", "RIASEC_C_03", "RIASEC_C_06", "RIASEC_C_09"],
}


@lru_cache(maxsize=1)
def get_riasec_static_24() -> list[Question]:
    all_riasec = {q.id: q for q in load_riasec_questions()}
    selected: list[Question] = []
    for t in ["R", "I", "A", "S", "E", "C"]:
        for qid in STATIC_24_ITEM_IDS[t]:
            if qid not in all_riasec:
                raise ValueError(f"Curated RIASEC id {qid} missing from 60-bank")
            selected.append(all_riasec[qid])
    return selected
```

- [ ] **Step 3: Run tests**

```bash
cd backend && pytest tests/test_riasec_static_24.py -v
```

Expected: 3 passed. If `RIASEC_X_NN` IDs don't exist in the 60-bank as named, adjust `STATIC_24_ITEM_IDS` to match the actual ID format produced by `load_riasec_questions()` (run `python -c "from questions.holland_riasec import load_riasec_questions; print([q.id for q in load_riasec_questions()][:10])"` to inspect).

- [ ] **Step 4: Commit**

```bash
git add backend/questions/riasec_static_24.py backend/tests/test_riasec_static_24.py
git commit -m "feat(backend): curate static 24-item RIASEC subset (4 per type)"
```

---

## Task 5: L1.5 dynamic selector engine

**Files:**
- Create: `backend/questions/selector.py`
- Create: `backend/tests/test_selector.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_selector.py"""
import pytest
from questions.selector import select_45_questions, derive_interleaved_order


def test_select_45_returns_exactly_45():
    answers = {"DEM_STAGE": "experienced", "DEM_TOP_PRESSURE": "money", "DEM_AGE": "25_29"}
    qs = select_45_questions(demographic_answers=answers, seed="test-seed-1")
    assert len(qs) == 45


def test_select_45_includes_all_demographic():
    qs = select_45_questions(demographic_answers={}, seed="test-seed-2")
    dem_ids = [q.id for q in qs if q.id.startswith("DEM_")]
    assert len(dem_ids) == 5


def test_select_45_includes_all_static_24_riasec():
    from questions.riasec_static_24 import get_riasec_static_24
    static_ids = {q.id for q in get_riasec_static_24()}
    qs = select_45_questions(demographic_answers={}, seed="test-seed-3")
    selected_ids = {q.id for q in qs}
    assert static_ids.issubset(selected_ids)


def test_select_45_has_16_dynamic_picks():
    qs = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="test-seed-4")
    interest_picks = [q for q in qs if q.id.startswith("INT_") or q.id.startswith("IPIP_")]
    assert len(interest_picks) == 16


def test_select_45_ocean_coverage():
    qs = select_45_questions(demographic_answers={"DEM_STAGE": "founder"}, seed="test-seed-5")
    interest_picks = [q for q in qs if q.id.startswith("INT_") or q.id.startswith("IPIP_")]
    by_dim: dict[str, int] = {}
    for q in interest_picks:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        assert by_dim.get(d, 0) >= 3, f"{d} has {by_dim.get(d, 0)} items, need ≥3"


def test_select_45_deterministic_per_seed():
    a = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="seed-X")
    b = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="seed-X")
    assert [q.id for q in a] == [q.id for q in b]


def test_demographic_first_then_interleaved():
    qs = select_45_questions(demographic_answers={}, seed="test-seed-7")
    # First 5 are demographic
    for i in range(5):
        assert qs[i].id.startswith("DEM_"), f"Q{i+1} should be demographic, got {qs[i].id}"
    # Last 40 should NOT be all RIASEC then all interest — must be interleaved
    last_40 = qs[5:]
    riasec_idx = [i for i, q in enumerate(last_40) if q.id.startswith("RIASEC_")]
    interest_idx = [i for i, q in enumerate(last_40) if q.id.startswith("INT_") or q.id.startswith("IPIP_")]
    # Verify interleaving: RIASEC items shouldn't all come before interest items
    assert max(riasec_idx) > min(interest_idx), "RIASEC and interest items should be interleaved"
```

Run: expect ALL FAIL.

- [ ] **Step 2: Implement selector**

`backend/questions/selector.py`:

```python
"""L1.5 dynamic question selection — 5 demographic + 24 static RIASEC + 16 dynamic IPIP/interest."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Iterable

from questions.demographic import DEMOGRAPHIC_QUESTIONS, derive_profile_tags
from questions.interest_pool import INTEREST_POOL
from questions.ipip_neo import OCEAN_DOMAINS
from questions.models import Question
from questions.riasec_static_24 import get_riasec_static_24


def _tag_match_score(question: Question, profile_tags: list[str]) -> int:
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
    candidates = [q for q in pool if q.dimension == dim]
    if len(candidates) < n:
        raise ValueError(f"Pool has only {len(candidates)} items for dimension {dim}, need {n}")

    scored = [(q, _tag_match_score(q, profile_tags) + rng.random()) for q in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [q for q, _ in scored[:n]]


def _select_16_dynamic(
    profile_tags: list[str],
    seed: str,
) -> list[Question]:
    rng = random.Random(f"{seed}::dynamic16")
    selected: list[Question] = []
    targets = {"openness": 3, "conscientiousness": 3, "extraversion": 3, "agreeableness": 3, "neuroticism": 4}
    assert sum(targets.values()) == 16

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
    """Interleave RIASEC and interest blocks so users don't see one homogeneous chunk.

    Pattern: alternates RIASEC and interest with a slight RIASEC bias (24 vs 16 = 3:2 ratio).
    Within each block, original order is preserved.
    """
    rng = random.Random(f"{seed}::order")
    riasec_iter = iter(block_riasec)
    interest_iter = iter(block_interest)

    pattern: list[str] = []
    while len(pattern) < 40:
        for _ in range(3):
            if len([p for p in pattern if p == "R"]) < len(block_riasec):
                pattern.append("R")
        for _ in range(2):
            if len([p for p in pattern if p == "I"]) < len(block_interest):
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
    profile_tags = derive_profile_tags(demographic_answers)

    block_demographic = list(DEMOGRAPHIC_QUESTIONS)
    block_riasec = list(get_riasec_static_24())
    block_interest = _select_16_dynamic(profile_tags, seed)

    interleaved_40 = derive_interleaved_order(block_riasec, block_interest, seed)
    return block_demographic + interleaved_40
```

- [ ] **Step 3: Run tests**

```bash
cd backend && pytest tests/test_selector.py -v
```

Expected: 7 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/questions/selector.py backend/tests/test_selector.py
git commit -m "feat(backend): add L1.5 selector engine (5 demo + 24 RIASEC + 16 dynamic interest)"
```

---

## Task 6: Scoring math (RIASEC + OCEAN + Holland code)

**Files:**
- Create: `backend/services/scoring/__init__.py`
- Create: `backend/services/scoring/riasec.py`
- Create: `backend/services/scoring/ocean.py`
- Create: `backend/services/scoring/holland_code.py`
- Create: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write failing tests**

```python
"""tests/test_scoring.py"""
from services.scoring.riasec import compute_riasec_scores
from services.scoring.ocean import compute_ocean_scores, score_to_percentile
from services.scoring.holland_code import compute_holland_code


def test_compute_riasec_all_max():
    answers = {f"RIASEC_{t}_{i:02d}": 5 for t in ["R", "I", "A", "S", "E", "C"] for i in (1, 3, 6, 9)}
    scores = compute_riasec_scores(answers)
    for t in ["R", "I", "A", "S", "E", "C"]:
        assert scores[t] == 20, f"{t} should be 20, got {scores[t]}"


def test_compute_riasec_partial():
    answers = {"RIASEC_I_01": 5, "RIASEC_I_03": 5, "RIASEC_I_06": 4, "RIASEC_I_09": 4}
    scores = compute_riasec_scores(answers)
    assert scores["I"] == 18  # 5+5+4+4
    assert scores["R"] == 0   # not answered


def test_compute_ocean_with_reverse():
    # IPIP items use facet+index naming. Forward-keyed with all 5s should max out.
    from questions.ipip_neo import load_ipip_questions
    ipip = {q.id: q for q in load_ipip_questions()}
    # build a synthetic answer set that should yield mid scores
    answers = {q.id: 3 for q in ipip.values() if q.dimension == "openness"}
    scores = compute_ocean_scores(answers)
    assert scores["openness"] == 60.0  # 3 * 20 = 60 (mid)


def test_score_to_percentile_boundaries():
    assert score_to_percentile(50.0) >= 50 and score_to_percentile(50.0) <= 60
    assert score_to_percentile(95.0) >= 98
    assert score_to_percentile(15.0) <= 5


def test_holland_code_basic():
    riasec_scores = {"R": 5, "I": 19, "A": 17, "S": 9, "E": 11, "C": 13}
    code = compute_holland_code(riasec_scores)
    assert code == "IAC"


def test_holland_code_tiebreak_alphabetical():
    riasec_scores = {"R": 10, "I": 10, "A": 10, "S": 5, "E": 5, "C": 5}
    code = compute_holland_code(riasec_scores)
    # A, I, R all tied at 10. Tiebreak: alphabetical → A, I, R
    assert code == "AIR"
```

Run: expect ALL FAIL.

- [ ] **Step 2: Implement RIASEC scoring**

`backend/services/scoring/__init__.py` (empty file):

```python
```

`backend/services/scoring/riasec.py`:

```python
"""RIASEC scoring: 4 items per type × 1-5 likert = score range 4-20 per type."""

from questions.holland_riasec import RIASEC_TYPES, load_riasec_questions


def compute_riasec_scores(answers: dict[str, int]) -> dict[str, int]:
    by_id = {q.id: q for q in load_riasec_questions()}
    totals: dict[str, int] = {t: 0 for t in RIASEC_TYPES}

    for qid, value in answers.items():
        q = by_id.get(qid)
        if q is None:
            continue
        if not (1 <= value <= 5):
            raise ValueError(f"RIASEC answer for {qid} must be 1-5, got {value}")
        totals[q.dimension] += value

    return totals
```

- [ ] **Step 3: Implement OCEAN scoring**

`backend/services/scoring/ocean.py`:

```python
"""OCEAN scoring with reverse-key handling and percentile mapping."""

from collections import defaultdict

from questions.interest_pool import INTEREST_POOL
from questions.ipip_neo import OCEAN_DOMAINS, load_ipip_questions


# Approximate IPIP-NEO percentile lookup (kept from legacy scoring.py).
PERCENTILE_TABLE: dict[tuple[float, float], int] = {
    (0.0, 20.0): 2,
    (20.0, 30.0): 8,
    (30.0, 35.0): 15,
    (35.0, 40.0): 25,
    (40.0, 45.0): 35,
    (45.0, 50.0): 50,
    (50.0, 55.0): 58,
    (55.0, 60.0): 68,
    (60.0, 65.0): 75,
    (65.0, 70.0): 82,
    (70.0, 75.0): 88,
    (75.0, 80.0): 93,
    (80.0, 85.0): 96,
    (85.0, 90.0): 98,
    (90.0, 101.0): 99,
}


def score_to_percentile(score: float) -> int:
    for (lo, hi), pct in PERCENTILE_TABLE.items():
        if lo <= score < hi:
            return pct
    return 50


def _build_question_index() -> dict:
    index: dict = {}
    for q in load_ipip_questions():
        index[q.id] = q
    for q in INTEREST_POOL:
        index[q.id] = q
    return index


def compute_ocean_scores(answers: dict[str, int]) -> dict[str, float]:
    """Compute OCEAN domain scores (0-100 scale).

    Args:
        answers: {question_id: 1-5 likert}. Includes both IPIP and INTEREST items.

    Returns:
        {"openness": 0-100, "conscientiousness": 0-100, ...}
    """
    qindex = _build_question_index()
    sums: dict[str, list[float]] = defaultdict(list)

    for qid, value in answers.items():
        q = qindex.get(qid)
        if q is None or q.dimension not in OCEAN_DOMAINS:
            continue
        if not (1 <= value <= 5):
            raise ValueError(f"OCEAN answer for {qid} must be 1-5, got {value}")
        scored = (6 - value) if q.reverse else value
        sums[q.dimension].append(scored)

    scores: dict[str, float] = {}
    for dim in OCEAN_DOMAINS:
        vals = sums.get(dim, [])
        if not vals:
            scores[dim] = 50.0
        else:
            mean = sum(vals) / len(vals)
            scores[dim] = round(mean * 20, 1)  # scale 1-5 → 0-100

    return scores


def compute_ocean_percentiles(scores: dict[str, float]) -> dict[str, int]:
    return {dim: score_to_percentile(s) for dim, s in scores.items()}
```

- [ ] **Step 4: Implement Holland code**

`backend/services/scoring/holland_code.py`:

```python
"""Compute 3-letter Holland code from 6 RIASEC scores."""

from questions.holland_riasec import RIASEC_TYPES


def compute_holland_code(riasec_scores: dict[str, int]) -> str:
    """Return top-3 RIASEC types as a 3-letter string. Ties broken alphabetically."""
    items = sorted(
        riasec_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),  # desc by score, asc by letter
    )
    code = "".join(letter for letter, _ in items[:3])
    if len(code) != 3:
        raise ValueError(f"Holland code must be 3 letters, got {code!r}")
    return code
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/test_scoring.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/services/scoring/ backend/tests/test_scoring.py
git commit -m "feat(backend): add scoring package — RIASEC + OCEAN + Holland code"
```

---

## Task 7: Cell match + MAST trigger

**Files:**
- Create: `backend/services/scoring/archetype.py`
- Create: `backend/tests/test_archetype.py`

- [ ] **Step 1: Write failing tests**

```python
"""tests/test_archetype.py"""
import pytest
from services.scoring.archetype import (
    derive_archetype_cell,
    is_valid_pair,
    check_mast_trigger,
    OPPOSITE_PAIRS,
    VALID_CELLS_24,
)


def test_valid_cells_count():
    assert len(VALID_CELLS_24) == 24


def test_no_opposite_pair_is_valid():
    for a, b in OPPOSITE_PAIRS:
        assert not is_valid_pair(a, b)
        assert not is_valid_pair(b, a)
    # Same letter not valid
    assert not is_valid_pair("R", "R")


def test_neighbor_pairs_valid():
    assert is_valid_pair("I", "R")
    assert is_valid_pair("I", "A")
    assert is_valid_pair("S", "E")
    assert is_valid_pair("C", "R")


def test_derive_cell_simple():
    cell = derive_archetype_cell({"I": 19, "A": 17, "C": 13, "R": 12, "E": 11, "S": 9}, holland_code="IAC")
    assert cell == "IA"


def test_derive_cell_skips_opposite():
    # Top 3 = I, E, A — but IE is forbidden. Should fall through to IA.
    cell = derive_archetype_cell({"I": 19, "E": 17, "A": 15, "S": 9, "R": 8, "C": 7}, holland_code="IEA")
    assert cell == "IA"


def test_derive_cell_extreme_fallback():
    # Top 3 = I, E, X where X is also forbidden — no, that's impossible,
    # since main I has 4 valid subs. But test that 3rd letter works as fallback.
    cell = derive_archetype_cell({"R": 19, "S": 18, "I": 5, "A": 4, "E": 3, "C": 2}, holland_code="RSI")
    # R-S forbidden, R-I valid → "RI"
    assert cell == "RI"


def test_mast_trigger_positive():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is True


def test_mast_trigger_negative_low_openness():
    ocean_pct = {"openness": 60, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is False


def test_mast_trigger_negative_high_neuroticism():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 30}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is False


def test_mast_trigger_negative_riasec_too_skewed():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    # Convert raw 0-20 RIASEC to ~percentile by multiplying by 5: 14*5=70, 6*5=30
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 6}  # C too low
    assert check_mast_trigger(ocean_pct, riasec_scores) is False
```

Run: expect ALL FAIL.

- [ ] **Step 2: Implement archetype derivation**

`backend/services/scoring/archetype.py`:

```python
"""Derive 24-cell archetype from Holland code + check MAST 0.06% trigger."""

from itertools import permutations

from questions.holland_riasec import RIASEC_TYPES

OPPOSITE_PAIRS: set[frozenset[str]] = {
    frozenset(["R", "S"]),
    frozenset(["I", "E"]),
    frozenset(["A", "C"]),
}


def is_valid_pair(main: str, sub: str) -> bool:
    if main == sub:
        return False
    if main not in RIASEC_TYPES or sub not in RIASEC_TYPES:
        return False
    return frozenset([main, sub]) not in OPPOSITE_PAIRS


def _build_valid_cells() -> list[str]:
    return [
        f"{m}{s}"
        for m in RIASEC_TYPES
        for s in RIASEC_TYPES
        if is_valid_pair(m, s)
    ]


VALID_CELLS_24: list[str] = _build_valid_cells()


def derive_archetype_cell(riasec_scores: dict[str, int], holland_code: str) -> str:
    """Pick a 2-letter archetype cell from main + best valid sub.

    Strategy:
      1. main = holland_code[0]
      2. try holland_code[1], holland_code[2] — first valid wins
      3. fallback: scan all RIASEC types by descending score
    """
    main = holland_code[0]
    for candidate in holland_code[1:]:
        if is_valid_pair(main, candidate):
            return main + candidate

    # Fallback: scan all types by descending score
    sorted_by_score = sorted(
        riasec_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )
    for letter, _ in sorted_by_score:
        if letter == main:
            continue
        if is_valid_pair(main, letter):
            return main + letter

    raise ValueError(f"Cannot derive archetype cell for main={main} from scores {riasec_scores}")


def check_mast_trigger(
    ocean_percentiles: dict[str, int],
    riasec_scores: dict[str, int],
) -> bool:
    """MAST 0.06% trigger:
      - openness ≥ 90 percentile
      - extraversion ≥ 85
      - agreeableness ≥ 85
      - emotional stability ≥ 85 (i.e., neuroticism percentile ≤ 15)
      - no RIASEC type < 40% of max (max is 20, so ≥ 8)
    """
    if ocean_percentiles.get("openness", 0) < 90:
        return False
    if ocean_percentiles.get("extraversion", 0) < 85:
        return False
    if ocean_percentiles.get("agreeableness", 0) < 85:
        return False
    if ocean_percentiles.get("neuroticism", 100) > 15:
        return False  # emotional stability must be high → low neuroticism
    if any(score < 8 for score in riasec_scores.values()):
        return False
    return True
```

- [ ] **Step 3: Run tests**

```bash
cd backend && pytest tests/test_archetype.py -v
```

Expected: 9 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/services/scoring/archetype.py backend/tests/test_archetype.py
git commit -m "feat(backend): add 24-cell archetype derivation + MAST 0.06% trigger"
```

---

## Task 8: Database migration (new columns)

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/database.py`
- Create: `backend/tests/test_db_migration.py`

- [ ] **Step 1: Write failing test**

```python
"""tests/test_db_migration.py"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import inspect

from database import engine, init_db
from models import Assessment


def test_assessment_has_new_columns():
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("assessments")}
    expected_new = {
        "ocean_scores", "riasec_scores", "holland_code",
        "archetype_cell", "archetype_label_en", "archetype_rarity_pct",
        "demographic", "share_code",
        "payment_provider", "payment_txn_id", "payment_status", "payment_amount_inr",
        "report_data", "pdf_path",
    }
    missing = expected_new - cols
    assert not missing, f"missing columns: {missing}"


def test_short_links_table_exists():
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("short_links")}
    expected = {"code", "assessment_id", "target_url", "clicks", "created_at"}
    missing = expected - cols
    assert not missing, f"missing short_links columns: {missing}"


def test_legacy_columns_still_present():
    """Backward compat: old columns must still exist (kept nullable)."""
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("assessments")}
    # legacy columns kept for backward compat (≥1 release deprecation window)
    legacy = {"scores", "stripe_session_id", "report_markdown", "report_html"}
    missing = legacy - cols
    assert not missing, f"legacy columns removed prematurely: {missing}"
```

Run: expect FAIL.

- [ ] **Step 2: Modify `backend/models.py`**

Replace the entire file with:

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, Float, ForeignKey

from database import Base


def gen_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=now_utc)
    answers = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)

    # NEW: scoring fields (v3 hybrid)
    ocean_scores = Column(JSON, nullable=True)            # {"openness": 0-100, ...}
    ocean_percentiles = Column(JSON, nullable=True)       # {"openness": 0-99, ...}
    riasec_scores = Column(JSON, nullable=True)           # {"R": 4-20, ...}
    holland_code = Column(String(3), nullable=True)       # "IRC"
    archetype_cell = Column(String(2), nullable=True, index=True)
    archetype_label_en = Column(String(80), nullable=True)
    archetype_rarity_pct = Column(Float, nullable=True)

    # NEW: demographic (raw answers from first 5 questions)
    demographic = Column(JSON, nullable=True)

    # NEW: short link / share
    share_code = Column(String(8), unique=True, nullable=True, index=True)

    # NEW: payment fields (v3)
    payment_provider = Column(String, nullable=True)      # "razorpay" | "mock" | "wechat" | "stripe"
    payment_txn_id = Column(String, nullable=True)
    payment_status = Column(String, default="pending")    # pending | confirmed | failed | refunded
    payment_amount_inr = Column(Integer, nullable=True)

    # NEW: report (replaces report_markdown/html, but those kept nullable)
    report_data = Column(JSON, nullable=True)
    pdf_path = Column(String, nullable=True)

    # LEGACY (kept nullable for ≥1 release backward compat)
    scores = Column(JSON, nullable=True)
    percentiles = Column(JSON, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    report_markdown = Column(Text, nullable=True)
    report_html = Column(Text, nullable=True)

    profile_source = Column(String, nullable=True)
    profile_data = Column(JSON, nullable=True)
    question_set_version = Column(String, nullable=False, default="v3_45_hybrid")
    question_ids = Column(JSON, nullable=True)
    selection_seed = Column(String, nullable=True)
    profile_session_token = Column(String, nullable=True, index=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_token = Column(String, unique=True, index=True, nullable=False, default=gen_uuid)
    provider = Column(String, nullable=False, default="manual")
    external_id = Column(String, nullable=True, index=True)
    external_handle = Column(String, nullable=True)
    external_public_data = Column(JSON, nullable=True)
    manual_answers = Column(JSON, nullable=True)
    profile_vector = Column(JSON, nullable=True)
    is_dev_account = Column(Boolean, default=False, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class ShortLink(Base):
    __tablename__ = "short_links"

    code = Column(String(8), primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    target_url = Column(String, nullable=False)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=now_utc)
```

- [ ] **Step 3: Modify `backend/database.py`** — extend the migration helper to add new columns to existing DB files (since SQLite is used in dev and ALTER TABLE is the migration path).

Replace the body of `_ensure_assessment_columns` (keep function signature) with:

```python
def _ensure_assessment_columns() -> None:
    columns_sql = {
        # Pre-existing
        "profile_source": "ALTER TABLE assessments ADD COLUMN profile_source VARCHAR",
        "profile_data": "ALTER TABLE assessments ADD COLUMN profile_data JSON",
        "question_set_version": "ALTER TABLE assessments ADD COLUMN question_set_version VARCHAR DEFAULT 'v3_45_hybrid'",
        "question_ids": "ALTER TABLE assessments ADD COLUMN question_ids JSON",
        "selection_seed": "ALTER TABLE assessments ADD COLUMN selection_seed VARCHAR",
        "profile_session_token": "ALTER TABLE assessments ADD COLUMN profile_session_token VARCHAR",
        # NEW v3
        "ocean_scores": "ALTER TABLE assessments ADD COLUMN ocean_scores JSON",
        "ocean_percentiles": "ALTER TABLE assessments ADD COLUMN ocean_percentiles JSON",
        "riasec_scores": "ALTER TABLE assessments ADD COLUMN riasec_scores JSON",
        "holland_code": "ALTER TABLE assessments ADD COLUMN holland_code VARCHAR(3)",
        "archetype_cell": "ALTER TABLE assessments ADD COLUMN archetype_cell VARCHAR(2)",
        "archetype_label_en": "ALTER TABLE assessments ADD COLUMN archetype_label_en VARCHAR(80)",
        "archetype_rarity_pct": "ALTER TABLE assessments ADD COLUMN archetype_rarity_pct FLOAT",
        "demographic": "ALTER TABLE assessments ADD COLUMN demographic JSON",
        "share_code": "ALTER TABLE assessments ADD COLUMN share_code VARCHAR(8)",
        "payment_provider": "ALTER TABLE assessments ADD COLUMN payment_provider VARCHAR",
        "payment_txn_id": "ALTER TABLE assessments ADD COLUMN payment_txn_id VARCHAR",
        "payment_status": "ALTER TABLE assessments ADD COLUMN payment_status VARCHAR DEFAULT 'pending'",
        "payment_amount_inr": "ALTER TABLE assessments ADD COLUMN payment_amount_inr INTEGER",
        "report_data": "ALTER TABLE assessments ADD COLUMN report_data JSON",
        "pdf_path": "ALTER TABLE assessments ADD COLUMN pdf_path VARCHAR",
    }

    with engine.begin() as conn:
        existing_rows = conn.execute(text("PRAGMA table_info(assessments)"))
        existing = {row[1] for row in existing_rows}

        for col, ddl in columns_sql.items():
            if col not in existing:
                conn.execute(text(ddl))
```

The unique index on `share_code` is created by `Base.metadata.create_all` for new DBs; for existing DBs, add this after the loop:

```python
        existing_indexes = conn.execute(text("PRAGMA index_list(assessments)"))
        index_names = {row[1] for row in existing_indexes}
        if "ix_assessments_share_code" not in index_names:
            try:
                conn.execute(text("CREATE UNIQUE INDEX ix_assessments_share_code ON assessments(share_code)"))
            except Exception:
                pass  # may fail if existing duplicate NULLs; safe to skip until v3 data lands
```

- [ ] **Step 4: Run migration test**

```bash
cd backend && pytest tests/test_db_migration.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run all backend tests for regression**

```bash
cd backend && pytest tests/ -v
```

Expected: all previous tests still pass + 3 new passes.

- [ ] **Step 6: Commit**

```bash
git add backend/models.py backend/database.py backend/tests/test_db_migration.py
git commit -m "feat(backend): add v3 hybrid columns + ShortLink table; preserve legacy nullable"
```

---

## Task 9: Compat shim + integration test

**Files:**
- Modify: `backend/questions/question_bank.py` (turn into compat shim)
- Create: `backend/tests/test_full_pipeline.py`

- [ ] **Step 1: Read existing `question_bank.py` callers**

```bash
cd backend && rg "from questions.question_bank|from questions import question_bank|import question_bank" --type py
```

Identify all import sites. Likely callers: `services/scoring.py`, `services/personalization.py`, `routers/assessment.py`. Document them as the surface that the compat shim must preserve.

- [ ] **Step 2: Refactor `backend/questions/question_bank.py` to a compat shim**

Replace its contents with:

```python
"""DEPRECATED: legacy 100-item Big-Five-only question bank.

This module is kept as a compat shim during the v2 → v3 transition.
Phase 3 of the redesign will remove all callers; Phase 4 will delete this file.

For new code, use:
  - questions.holland_riasec.load_riasec_questions
  - questions.ipip_neo.load_ipip_questions
  - questions.demographic.DEMOGRAPHIC_QUESTIONS
  - questions.interest_pool.INTEREST_POOL
  - questions.selector.select_45_questions
"""

from __future__ import annotations

import warnings

from questions.ipip_neo import OCEAN_DOMAINS as DIMENSIONS  # re-export

_DEPRECATION_NOTICE = (
    "questions.question_bank.* is deprecated. "
    "Use questions.{holland_riasec, ipip_neo, demographic, interest_pool, selector} instead."
)


def get_question_pool(version: str | None = None) -> list[dict]:
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return _build_legacy_dict_pool()


def get_question_map() -> dict[str, dict]:
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return {q["id"]: q for q in _build_legacy_dict_pool()}


def get_question_by_ids(ids: list[str]) -> list[dict]:
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    qmap = get_question_map()
    return [qmap[qid] for qid in ids if qid in qmap]


def get_all_questions() -> list[dict]:
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return _build_legacy_dict_pool()


def _build_legacy_dict_pool() -> list[dict]:
    """Map IPIP-NEO 120 → legacy dict shape used by personalization.py / scoring.py.

    Legacy shape per item:
      {"id", "text", "dimension", "reverse", "facet", "scenes", "role", "difficulty", "tags", "language"}
    """
    from questions.ipip_neo import load_ipip_questions

    out: list[dict] = []
    for q in load_ipip_questions():
        out.append({
            "id": q.id,
            "text": q.text_en,
            "dimension": q.dimension,
            "reverse": q.reverse,
            "facet": q.facet or q.id,
            "scenes": q.scenes,
            "role": q.role,
            "difficulty": q.difficulty,
            "tags": q.tags,
            "language": "en",
        })
    return out
```

- [ ] **Step 3: Run existing tests + verify legacy callers still work**

```bash
cd backend && pytest tests/ -v -W ignore::DeprecationWarning
```

Expected: all tests pass (with deprecation warnings filtered).

If a legacy caller breaks (e.g., expects `O1`/`C21` style IDs from the old 100-item bank), document the failure. Two options:
1. **Accept the break** if the caller will be rewritten in Phase 3 anyway (mark caller with `# v3-pending` comment).
2. **Add ID translation** in the shim if Phase 1 must keep the legacy API stable.

For Phase 1, prefer option 1 — Phase 3 will rewrite assessment/scoring routers to use the new package directly.

- [ ] **Step 4: Write end-to-end integration test**

`backend/tests/test_full_pipeline.py`:

```python
"""End-to-end test: select 45 questions → simulate answers → run full scoring → archetype."""
from questions.selector import select_45_questions
from services.scoring.riasec import compute_riasec_scores
from services.scoring.ocean import compute_ocean_scores, compute_ocean_percentiles
from services.scoring.holland_code import compute_holland_code
from services.scoring.archetype import derive_archetype_cell, check_mast_trigger


def test_full_45_question_pipeline():
    # 1. Select 45 questions for an experienced professional with EMI pressure
    demographic_answers = {
        "DEM_STAGE": "experienced",
        "DEM_AGE": "25_29",
        "DEM_GENDER": "male",
        "DEM_CITY_TIER": "tier1",
        "DEM_TOP_PRESSURE": "money",
    }
    questions = select_45_questions(demographic_answers, seed="pipeline-test-1")
    assert len(questions) == 45

    # 2. Simulate answers (deterministic, varied)
    answers: dict[str, int] = {}
    for i, q in enumerate(questions):
        if q.id.startswith("DEM_"):
            continue  # demographics not numerically scored
        answers[q.id] = (i % 5) + 1  # 1..5 cycling

    # 3. Run scoring
    riasec = compute_riasec_scores(answers)
    ocean = compute_ocean_scores(answers)
    ocean_pct = compute_ocean_percentiles(ocean)
    holland_code = compute_holland_code(riasec)

    assert sum(riasec.values()) > 0
    assert all(0 <= s <= 100 for s in ocean.values())
    assert len(holland_code) == 3

    # 4. Derive archetype cell
    cell = derive_archetype_cell(riasec, holland_code)
    assert len(cell) == 2
    assert cell[0] != cell[1]

    # 5. MAST trigger should be False (synthetic answers won't peak all 4 conditions)
    assert check_mast_trigger(ocean_pct, riasec) is False
```

- [ ] **Step 5: Run end-to-end test**

```bash
cd backend && pytest tests/test_full_pipeline.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: all passing. Note any deprecation warnings — they're informational.

- [ ] **Step 7: Commit**

```bash
git add backend/questions/question_bank.py backend/tests/test_full_pipeline.py
git commit -m "feat(backend): make legacy question_bank.py a compat shim + add E2E pipeline test"
```

---

## Phase 1 Acceptance Criteria

After all 9 tasks complete, the following must hold:

- [ ] `pytest tests/ -v` returns all green (≥ 30 tests passing).
- [ ] `from questions.selector import select_45_questions` produces deterministic 45-item lists per (demographic, seed).
- [ ] `select_45_questions(...)` always includes the 5 demographic + 24 static RIASEC + 16 dynamic IPIP/interest items.
- [ ] `compute_riasec_scores`, `compute_ocean_scores`, `compute_holland_code`, `derive_archetype_cell`, `check_mast_trigger` are all importable from their respective modules.
- [ ] `Assessment` table has all v3 columns (ocean_scores, riasec_scores, holland_code, archetype_cell, archetype_label_en, archetype_rarity_pct, demographic, share_code, payment_*, report_data, pdf_path).
- [ ] `ShortLink` table exists.
- [ ] Legacy `questions.question_bank.*` API still importable (with DeprecationWarning).
- [ ] Existing routers (`/api/assessment/questions`, `/api/assessment/submit`, `/api/report/{id}`) still respond to existing E2E flows (Phase 3 will refactor them — Phase 1 only requires they don't crash).
- [ ] All work committed in well-scoped commits with conventional messages.

## Spec Coverage (Phase 1 → Spec Sections)

- ✅ S1 Question Bank Infrastructure — Tasks 2, 3, 4
- ✅ S2 Dynamic Selection (L1.5) — Task 5
- ✅ S3 Scoring Model — Tasks 6, 7
- ✅ Data Model Changes (assessments + short_links) — Task 8
- ⚠️ Compat shim — Task 9 (covers Phase 3 prep, not a spec section)
- ⏭ S4-S10 — out of scope for Phase 1 (later plans)

## What's NOT in Phase 1

- API surface refactor (assessment/payment/report routers) — **Phase 3**
- Content authoring (24 cell content files, 40 careers) — **Phase 2**
- Razorpay / payment driver implementation — **Phase 3**
- Frontend changes — **Phase 4**
- Auth modal + Facebook OAuth — **Phase 3**
- OG image / sharing — **Phase 4**
- IBTI Hinglish copy refinement — **Phase 2**

## Estimated Effort

~12-15 hours of focused engineering (1 engineer, 2 working days). Content tasks (interest pool curation in Task 3) account for ~3 hours of writing time.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-27-careerdna-phase-1-backend-foundation.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Each subagent gets just one task's context.

2. **Inline Execution** — Execute tasks in this session using executing-plans skill, batch execution with checkpoints for review.

**Which approach?**
