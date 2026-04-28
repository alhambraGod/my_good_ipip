"""Cell content loader — reads 24 JSON files from content/data/cells/, validates against schema."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from content.models import CellContent
from services.scoring.archetype import VALID_CELLS_24

_HERE = Path(__file__).resolve().parent
_CELLS_DIR = _HERE / "data" / "cells"


@lru_cache(maxsize=1)
def load_all_cells() -> dict[str, CellContent]:
    """Load all 24 cell JSON files into {cell_id: CellContent}.

    Raises:
      FileNotFoundError if any of the 24 expected files is missing.
      pydantic.ValidationError if any file fails the CellContent schema.
    """
    cells: dict[str, CellContent] = {}
    for cell_id in VALID_CELLS_24:
        path = _CELLS_DIR / f"{cell_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing cell content file: {path}")
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        cells[cell_id] = CellContent.model_validate(raw)
    return cells


def get_cell_content(cell_id: str) -> CellContent:
    """Look up content for a single cell. Raises KeyError if not in 24 valid cells."""
    cells = load_all_cells()
    if cell_id not in cells:
        raise KeyError(f"unknown cell: {cell_id!r}; must be one of {VALID_CELLS_24}")
    return cells[cell_id]
