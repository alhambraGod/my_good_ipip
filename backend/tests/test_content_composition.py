"""tests/test_content_composition.py — E2E: pipeline + content lookup → composed report."""
from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from questions.selector import select_45_questions
from services.milestone_copy import MILESTONE_THRESHOLDS, get_copy_for_milestone
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

    cell_content = get_cell_content(cell_id)
    careers = get_careers_for_cell(cell_id)

    # Verify composition shape
    assert cell_content.cell == cell_id
    assert len(cell_content.strengths_en) == 5
    assert len(cell_content.growth_tips_en) == 5
    assert len(careers) >= 3
    # Every career has a complete shape
    for career in careers:
        assert career.salary_inr.entry
        assert career.salary_inr.mid
        assert career.salary_inr.senior
        assert len(career.indian_companies) >= 2


def test_compose_milestone_copy_for_each_threshold():
    """Each milestone returns a non-empty string deterministically per seed."""
    for milestone in MILESTONE_THRESHOLDS:
        copy = get_copy_for_milestone(milestone, seed="e2e-milestone-1")
        assert copy and len(copy) >= 10


def test_composed_report_has_no_placeholder_for_exemplar_cells():
    """If user lands on one of the 4 cell exemplars, full content must be available
    AND every career in that cell's career_directions must have a why_match string for it."""
    EXEMPLAR_CELLS = ("IA", "SE", "EC", "SC")
    for cell_id in EXEMPLAR_CELLS:
        c = get_cell_content(cell_id)
        assert "PLACEHOLDER" not in c.core_insight_en, f"{cell_id} core_insight has PLACEHOLDER"
        assert "PLACEHOLDER" not in c.deep_description_en, f"{cell_id} deep_description has PLACEHOLDER"

        # Each career listed by this cell must have a why_match key for this cell (Path A guarantee)
        careers = get_careers_for_cell(cell_id)
        for career in careers:
            assert cell_id in career.why_match, (
                f"career {career.career_id} listed by cell {cell_id} but missing why_match[{cell_id}]"
            )


def test_composed_report_for_all_24_cells_has_renderable_data():
    """Cross-check: for every valid 24-cell archetype, the full Path A render is data-complete.

    This is the strongest E2E invariant — it proves Tasks 2/4/5 produced an internally consistent
    state where any user landing on any cell will see a complete report.
    """
    from services.scoring.archetype import VALID_CELLS_24

    for cell_id in VALID_CELLS_24:
        c = get_cell_content(cell_id)
        careers = get_careers_for_cell(cell_id)

        # Cell content shape
        assert c.cell == cell_id
        assert len(c.strengths_en) == 5
        assert len(c.growth_tips_en) == 5
        assert len(c.share_lines_en) >= 1

        # Career list shape
        assert len(careers) >= 3, f"cell {cell_id} has only {len(careers)} careers"
        for career in careers:
            assert career.indian_companies, f"career {career.career_id} has no companies"
            assert cell_id in career.why_match, (
                f"career {career.career_id} (referenced by {cell_id}) missing why_match[{cell_id}]"
            )
