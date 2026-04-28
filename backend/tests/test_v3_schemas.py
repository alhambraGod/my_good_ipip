"""tests/test_v3_schemas.py — smoke check that v3 schemas are importable + constructible."""
from schemas import (
    DemographicAnswerSubmission,
    V3AnswerSubmission,
    V3AssessmentResultResponse,
    V3AssessmentStartRequest,
    V3AssessmentStartResponse,
    V3MilestoneResponse,
    V3PaymentIntentRequest,
    V3PaymentIntentResponse,
    V3QuestionOut,
    V3ReportResponse,
)


def test_demographic_submission_construct():
    d = DemographicAnswerSubmission(
        DEM_STAGE="experienced", DEM_AGE="25_29", DEM_GENDER="male",
        DEM_CITY_TIER="tier1", DEM_TOP_PRESSURE="career",
    )
    assert d.DEM_STAGE == "experienced"


def test_v3_assessment_start_request():
    req = V3AssessmentStartRequest(demographic=DemographicAnswerSubmission(
        DEM_STAGE="student", DEM_AGE="20_24", DEM_GENDER="female",
        DEM_CITY_TIER="tier2", DEM_TOP_PRESSURE="self_doubt",
    ))
    assert req.demographic.DEM_STAGE == "student"


def test_v3_question_out_with_options():
    q = V3QuestionOut(
        id="DEM_STAGE", text="Which best describes you?",
        instrument="demographic", response_type="single_choice",
        options=[{"value": "student", "label": "Student"}],
    )
    assert q.options[0]["value"] == "student"


def test_v3_assessment_start_response():
    resp = V3AssessmentStartResponse(
        assessment_id="abc-123",
        questions=[],
        seed="seed-1",
    )
    assert resp.assessment_id == "abc-123"


def test_v3_answer_submission_mixed_types():
    sub = V3AnswerSubmission(
        assessment_id="abc",
        answers={"DEM_STAGE": "student", "RIASEC_R01": 3, "IPIP_N1_1": 4},
    )
    assert sub.answers["RIASEC_R01"] == 3


def test_v3_payment_intent_response():
    resp = V3PaymentIntentResponse(
        assessment_id="abc",
        provider="mock",
        payment_url="https://example.com/mock",
        amount_inr=49,
        promo_active=True,
    )
    assert resp.provider == "mock"


def test_v3_milestone_response():
    resp = V3MilestoneResponse(milestone=20, copy="Halfway there!")
    assert resp.milestone == 20
