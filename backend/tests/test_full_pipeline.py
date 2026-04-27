"""End-to-end test: select 45 questions → simulate answers → run full scoring → archetype."""
from questions.selector import select_45_questions
from services.scoring.archetype import check_mast_trigger, derive_archetype_cell
from services.scoring.holland_code import compute_holland_code
from services.scoring.ocean import compute_ocean_percentiles, compute_ocean_scores
from services.scoring.riasec import compute_riasec_scores


def test_full_45_question_pipeline():
    """Run the full Phase 1 backend pipeline: select → answer → score → archetype."""
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

    # 2. Simulate answers (deterministic, varied — cycle 1..5 for non-demographic items)
    answers: dict[str, int] = {}
    for i, q in enumerate(questions):
        if q.id.startswith("DEM_"):
            continue  # demographics not numerically scored
        answers[q.id] = (i % 5) + 1

    # 3. Run scoring math
    riasec = compute_riasec_scores(answers)
    ocean = compute_ocean_scores(answers)
    ocean_pct = compute_ocean_percentiles(ocean)
    holland_code = compute_holland_code(riasec)

    # Sanity: scores in expected ranges
    assert sum(riasec.values()) > 0, "RIASEC scoring produced empty totals"
    assert all(0 <= s <= 100 for s in ocean.values()), "OCEAN scores out of 0-100 range"
    assert len(holland_code) == 3, f"Holland code must be 3 chars, got {holland_code!r}"

    # 4. Derive archetype cell
    cell = derive_archetype_cell(riasec, holland_code)
    assert len(cell) == 2, f"archetype cell must be 2 chars, got {cell!r}"
    assert cell[0] != cell[1], "main and sub of cell must differ"

    # 5. MAST trigger should be False with this synthetic answer set
    #    (artificial cycling values won't peak all 4 OCEAN gates simultaneously)
    assert check_mast_trigger(ocean_pct, riasec) is False


def test_full_pipeline_deterministic():
    """Identical (demographic + seed) → identical output across calls."""
    demographic = {"DEM_STAGE": "student", "DEM_AGE": "20_24"}
    qs1 = select_45_questions(demographic, seed="determinism-A")
    qs2 = select_45_questions(demographic, seed="determinism-A")
    assert [q.id for q in qs1] == [q.id for q in qs2]

    # Different seeds should produce different question sets (proves the seed actually matters)
    qs3 = select_45_questions(demographic, seed="determinism-B")
    assert [q.id for q in qs1] != [q.id for q in qs3]


def test_full_pipeline_with_different_demographics_diverges_in_dynamic_segment():
    """Different demographic answers → different INT_* picks (different profile tags weight differently)."""
    qs_student = select_45_questions(
        demographic_answers={"DEM_STAGE": "student", "DEM_AGE": "20_24", "DEM_TOP_PRESSURE": "career"},
        seed="diverge-test",
    )
    qs_experienced = select_45_questions(
        demographic_answers={"DEM_STAGE": "experienced", "DEM_AGE": "30_34", "DEM_TOP_PRESSURE": "money"},
        seed="diverge-test",
    )

    int_student = [q.id for q in qs_student if q.id.startswith("INT_")]
    int_experienced = [q.id for q in qs_experienced if q.id.startswith("INT_")]

    assert int_student != int_experienced, (
        "Different profile tags should weight pool differently, producing different INT_* selections"
    )
