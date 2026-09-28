"""Aggregates every lane's type rows. Frozen after Phase 2: lanes edit their own row module only."""

from __future__ import annotations

from crystalia_data_model.types.registry import TypeEntry
from crystalia_data_model.types.rows import bookend_zip, coverage, inferred, leaves

ROWS: tuple[TypeEntry, ...] = (*leaves.ROWS, *coverage.ROWS, *bookend_zip.ROWS, *inferred.ROWS)

__all__ = ["ROWS"]
