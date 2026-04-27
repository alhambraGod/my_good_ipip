"""Scoring package — RIASEC + OCEAN + Holland code + archetype.

Phase 1 deliverables here:
  - services.scoring.riasec.compute_riasec_scores
  - services.scoring.ocean.compute_ocean_scores, compute_ocean_percentiles, score_to_percentile
  - services.scoring.holland_code.compute_holland_code

Task 7 will add:
  - services.scoring.archetype.derive_archetype_cell, check_mast_trigger, VALID_CELLS_24

Legacy `services.scoring_legacy` (formerly `services/scoring.py`) is kept until Phase 3
when routers/assessment.py is refactored to use this package.
"""
