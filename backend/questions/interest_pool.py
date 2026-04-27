"""Indian-flavored IPIP-NEO interest pool — 30+ candidate items.

The L1.5 selector (questions.selector) picks 16 of these at runtime, weighted
by demographic-derived profile tags. Each item is double-coded:
  - dimension: maps to one OCEAN domain (for scoring)
  - tags: profile-tag affinities (for selector weighting)

Wording adopts IBTI-style Hinglish accents while preserving IPIP semantic intent.
"""

from questions.models import Instrument, Question, ResponseType


def _q(qid: str, text: str, dim: str, reverse: bool, tags: list[str]) -> Question:
    return Question(
        id=qid,
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
