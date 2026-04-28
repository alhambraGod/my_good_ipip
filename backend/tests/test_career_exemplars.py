"""tests/test_career_exemplars.py — verify hand-curated career exemplars meet quality bar."""
from content.careers import get_career


EXEMPLARS = [
    "data_scientist", "strategy_consultant", "screenwriter", "school_teacher",
    "sales_manager", "startup_founder", "policy_analyst", "customer_success_manager",
]


FORBIDDEN_SENTINELS = ("PLACEHOLDER", "TODO", "TBD", "FIXME", "REPLACE_ME", "[draft]", "Lorem ipsum")


INDIAN_CONTEXT_MARKERS = (
    "sharma", "gupta", "agarwal", "marwari", "bania", "aunty", "uncle", "beta", "bhaiya", "chacha",
    "bangalore", "mumbai", "delhi", "kolkata", "chennai", "hyderabad", "pune", "gurugram",
    "rajasthan", "gujarat", "kerala", "bihar",
    "iit", "iim", "tcs", "infosys", "razorpay", "swiggy", "flipkart", "phonepe", "cred",
    "ipu", "upsc", "niti aayog", "iiit", "iisc", "ftii", "lutyens",
    "diwali", "baraat", "shaadi", "joint family", "chai", "dosa", "biryani", "bollywood",
    "whatsapp", "hinglish", "emi", "lakh", "crore", "sarkari", "babu", "fintech",
    "na-laayak", "kya", "haan", "nahi", "yaar", "anm",
)


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
        assert 4 <= len(c.indian_companies) <= 8, f"{career_id} has {len(c.indian_companies)} companies; need 4-8"
        for company in c.indian_companies:
            assert "PLACEHOLDER" not in company


def test_exemplars_have_at_least_3_why_match_cells():
    """Each exemplar career describes matches for at least 3 cells."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert len(c.why_match) >= 3, f"{career_id} only matches {len(c.why_match)} cells; need >=3"


def test_exemplars_have_complete_salary_range():
    """Exemplars have non-empty entry/mid/senior salary in lakh notation."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert c.salary_inr.entry and c.salary_inr.mid and c.salary_inr.senior
        # Each should contain "L" (lakh) or "Cr" (crore) — not bare numerals
        for s in (c.salary_inr.entry, c.salary_inr.mid, c.salary_inr.senior):
            assert ("L" in s) or ("Cr" in s) or s.lower() in ("variable", "n/a"), (
                f"{career_id} salary {s!r} should contain L or Cr (lakh/crore notation)"
            )


def test_exemplars_have_quality_taglines():
    """Exemplar tagline_en should be non-trivial (≥30 chars, evocative not generic)."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        assert len(c.tagline_en) >= 30, (
            f"{career_id} tagline_en is only {len(c.tagline_en)} chars; need >=30 for exemplar quality"
        )


def test_exemplars_have_quality_why_match():
    """Each why_match string should be ≥40 chars (1-2 sentences of actual analysis)."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        for cell_id, why in c.why_match.items():
            assert len(why) >= 40, (
                f"{career_id}.why_match[{cell_id}] is only {len(why)} chars; need >=40 for real content"
            )


def test_exemplars_have_no_sentinel_text():
    """Exemplars must not contain any author-sentinel/draft markers in their content."""
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        text_fields = {
            "tagline_en": c.tagline_en,
            "name_en": c.name_en,
            "name_hi": c.name_hi,
        }
        for field_name, text in text_fields.items():
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in text, f"{career_id}.{field_name} contains forbidden sentinel '{sentinel}'"
        for cell_id, why in c.why_match.items():
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in why, f"{career_id}.why_match[{cell_id}] contains '{sentinel}'"
        for i, company in enumerate(c.indian_companies):
            for sentinel in FORBIDDEN_SENTINELS:
                assert sentinel not in company, f"{career_id}.indian_companies[{i}] contains '{sentinel}'"


def test_exemplars_have_indian_context_markers():
    """Exemplars must reference at least 2 Indian-context markers across tagline + why_match values.

    Cell exemplars use floor 3; career exemplars are shorter per-cell so floor 2 is realistic.
    Generic 'Indian' copy without specific proper nouns fails.
    """
    for career_id in EXEMPLARS:
        c = get_career(career_id)
        text = c.tagline_en.lower() + " " + " ".join(why.lower() for why in c.why_match.values())
        hits = sum(1 for marker in INDIAN_CONTEXT_MARKERS if marker in text)
        assert hits >= 2, (
            f"{career_id} has only {hits} Indian-context markers in tagline + why_match; "
            f"needs >=2 specific proper nouns or culturally-specific terms"
        )
