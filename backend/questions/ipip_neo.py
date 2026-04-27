"""IPIP-NEO 120-item question loader (from docs/IPIP_NEO_120_questionbank.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from questions.models import Instrument, Question, ResponseType

OCEAN_DOMAINS: tuple[str, ...] = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
DOMAIN_LETTER_TO_NAME = {"O": "openness", "C": "conscientiousness", "E": "extraversion", "A": "agreeableness", "N": "neuroticism"}

_HERE = Path(__file__).resolve().parent
_BANK_PATH = _HERE.parent.parent / "docs" / "IPIP_NEO_120_questionbank.json"


@lru_cache(maxsize=1)
def load_ipip_questions() -> list[Question]:
    with open(_BANK_PATH, encoding="utf-8") as f:
        bank = json.load(f)

    questions: list[Question] = []
    for it in bank["items"]:
        questions.append(
            Question(
                id=f"IPIP_{it['id']}",
                text_en=it["text_en"],
                instrument=Instrument.IPIP,
                dimension=DOMAIN_LETTER_TO_NAME[it["domain"]],
                reverse=(it["keyed"] == "-"),  # explicit KeyError if upstream bank loses the field
                response_type=ResponseType.LIKERT_5,
                facet=it["facet"],
                role="core",
                tags=["ipip", "ocean"],
            )
        )
    return questions
