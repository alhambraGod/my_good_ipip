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
