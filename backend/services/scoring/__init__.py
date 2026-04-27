"""Scoring package — RIASEC + OCEAN + Holland code + archetype.

Public API:
  - services.scoring.riasec.compute_riasec_scores
  - services.scoring.ocean.compute_ocean_scores, compute_ocean_percentiles, score_to_percentile, PERCENTILE_TABLE
  - services.scoring.holland_code.compute_holland_code
  - services.scoring.archetype.derive_archetype_cell, check_mast_trigger, is_valid_pair,
                                  VALID_CELLS_24, OPPOSITE_PAIRS

Legacy `services.scoring_legacy` (formerly `services/scoring.py`) is the
v2-Big-Five-only scoring module, still used by the legacy router until the
Phase 3 refactor switches callers to this package.
"""
