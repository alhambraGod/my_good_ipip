"""Cell content loader — reads 24 JSON files from content/data/cells/, validates against schema.

Stub-quality note (Phase 2):
  Phase 2 ships stubs where ``strengths_en`` / ``growth_tips_en`` are deduped by RIASEC
  main type (all I-* cells share 5 strengths, all R-* cells share 5 strengths, etc.).
  Phase 2.5 content authoring will replace these with cell-specific copy. The 4 cell
  exemplars (IA, SE, EC, SC) authored in Task 3 are the gold standard for this
  refinement.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from content.models import CellContent
from services.scoring.archetype import VALID_CELLS_24

__all__ = ["CELLS_DIR", "load_all_cells", "get_cell_content", "render_share_line", "clear_cache"]

_HERE = Path(__file__).resolve().parent
CELLS_DIR = _HERE / "data" / "cells"


@lru_cache(maxsize=1)
def _cells_cache() -> dict[str, CellContent]:
    """Internal: load + cache all 24 cell JSON files. Use ``load_all_cells()`` externally.

    Raises:
      FileNotFoundError if any of the 24 expected files is missing.
      pydantic.ValidationError if any file fails the CellContent schema.
    """
    cells: dict[str, CellContent] = {}
    for cell_id in VALID_CELLS_24:
        path = CELLS_DIR / f"{cell_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing cell content file: {path}")
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        cells[cell_id] = CellContent.model_validate(raw)
    return cells


def load_all_cells() -> Mapping[str, CellContent]:
    """Return the read-only mapping of {cell_id: CellContent} for all 24 valid cells.

    The underlying dict is cached process-lifetime; this returns a ``MappingProxyType``
    view to prevent accidental mutation that would corrupt every subsequent caller.
    """
    return MappingProxyType(_cells_cache())


def get_cell_content(cell_id: str) -> CellContent:
    """Look up content for a single cell. Raises KeyError if not in 24 valid cells."""
    cells = load_all_cells()
    if cell_id not in cells:
        raise KeyError(f"unknown cell: {cell_id!r}; must be one of {VALID_CELLS_24}")
    return cells[cell_id]


def render_share_line(line: str, share_url: str) -> str:
    """Substitute [link] token in a share copy line with the actual share URL.

    Designed for backend share-card generation + frontend pre-rendered share text.
    Idempotent: if [link] is absent, returns line unchanged.
    """
    return line.replace("[link]", share_url)


def clear_cache() -> None:
    """Clear the cells cache (admin-script use, hot reload after content edits)."""
    _cells_cache.cache_clear()
