"""Lane B rows: ``md5-chunked``, ``asserted`` and the S3 ETag subtypes (model-only in v2)."""

from __future__ import annotations

from crystalia_data_model.types.registry import (
    Grade,
    Robustness,
    TypeEntry,
    asserted_type,
    plain_leaf,
    region_composite,
)

_PENDING = "robustness: SPARC default, pending spec check"

ROWS: tuple[TypeEntry, ...] = (
    region_composite(
        "md5-chunked",
        Grade.COMPARISON,
        Robustness.VERY_HIGH,
        part="md5-region",
        doc=f"md5-region parts by offset with total expected; strong only when every part is present; {_PENDING}",
    ),
    asserted_type(doc="coverage asserted by an opaque producer; the producer descriptor is the single child"),
    plain_leaf(
        "etag-single",
        Grade.COMPARISON,
        Robustness.VERY_HIGH,
        strong=True,
        doc=f"S3 ETag of a single-part upload (md5 of the object); not emitted in v2; {_PENDING}",
    ),
    plain_leaf(
        "etag-multipart",
        Grade.COMPARISON,
        Robustness.MODERATE,
        strong=True,
        doc=f"S3 ETag of a multipart upload; comparable only at equal part size (carrier decided by Lane B); not emitted in v2; {_PENDING}",
    ),
    plain_leaf(
        "etag-sse",
        Grade.COMPARISON,
        Robustness.LOW,
        doc=f"S3 ETag under SSE; only self-comparable; not emitted in v2; {_PENDING}",
    ),
)

__all__ = ["ROWS"]
