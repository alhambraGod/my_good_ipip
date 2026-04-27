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

    questions: list[Question] = []
    for it in bank["items"]:
        questions.append(
            Question(
                id=f"RIASEC_{it['id']}",
                text_en=it["text_en"],
                instrument=Instrument.RIASEC,
                dimension=it["type"],
                reverse=(it.get("keyed", "+") == "-"),
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
