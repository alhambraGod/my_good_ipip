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
    "family": ["family-pressure", "sharma-ji-syndrome"],
    "money": ["EMI", "money", "financial-stress"],
    "self_doubt": ["self-doubt", "imposter"],
    "curious": [],
}


def derive_profile_tags(answers: dict[str, str]) -> list[str]:
    """Derive profile tags from demographic answers; selector uses these to weight pool."""
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
