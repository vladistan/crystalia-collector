"""Lane C rows: bookends, folder bookends, ``zip-cd`` and ``zip-manifest``."""

from __future__ import annotations

from crystalia_data_model.types.registry import (
    Grade,
    Robustness,
    TypeEntry,
    field_composite,
    hash_leaf,
    plain_leaf,
    rollup,
)

_PENDING = "robustness: SPARC default, pending spec check"
_BOOKEND_ROLES = (("head", "md5-region"), ("tail", "md5-region"), ("format", "format"), ("file-size", "file-size"))

ROWS: tuple[TypeEntry, ...] = (
    field_composite(
        "bookend-strong",
        _BOOKEND_ROLES,
        Grade.COMPARISON,
        Robustness.MODERATE,
        strong=True,
        doc=f"16 KB head + 16 KB tail judged STRONG by a verified format rule (or size <= 32 KB); {_PENDING}",
    ),
    field_composite(
        "bookend-weak",
        _BOOKEND_ROLES,
        Grade.COMPARISON,
        Robustness.LOW,
        doc=f"16 KB head + 16 KB tail judged WEAK; {_PENDING}",
    ),
    rollup(
        "bookend-dir-strong",
        Grade.COMPARISON,
        Robustness.MODERATE,
        strong=True,
        doc=f"folder bookend, every child strong; {_PENDING}",
    ),
    rollup(
        "bookend-dir-weak", Grade.COMPARISON, Robustness.LOW, doc=f"folder bookend, at least one weak child; {_PENDING}"
    ),
    hash_leaf(
        "zip-cd",
        Grade.AUTHORITY,
        Robustness.MODERATE,
        doc=f"md5 of the raw zip central directory; length = CD bytes; {_PENDING}",
    ),
    plain_leaf(
        "zip-manifest",
        Grade.COMPARISON,
        Robustness.MODERATE,
        strong=True,
        doc=f"md5 of sorted (NFC member name, CRC-32, uncompressed size); no length; {_PENDING}",
    ),
)

__all__ = ["ROWS"]
