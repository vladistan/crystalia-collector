"""Lane A rows: fact leaves, ``md5``, ``md5-region``, content glimpses and legacy ``glimpse*`` / ``glimpse-dir*``.

Legacy role orders mirror the collector's v1 composites (filename, size, md5-head, ctime, mtime ...)
so that the v2 encoding keeps the same field semantics under the new, unambiguous byte layout.
Robustness values are SPARC defaults pending spec check.
"""

from __future__ import annotations

from crystalia_data_model.types.registry import (
    Grade,
    Robustness,
    TypeEntry,
    fact_leaf,
    field_composite,
    hash_leaf,
    positional,
    rollup,
)

_PENDING = "robustness: SPARC default, pending spec check"

_FACTS: tuple[TypeEntry, ...] = (
    fact_leaf("filename", Grade.LOCATION, doc=f"the object's base name; {_PENDING}"),
    fact_leaf("relpath", Grade.LOCATION, doc=f"path relative to the harvest root; {_PENDING}"),
    fact_leaf("file-size", Grade.COMPARISON, doc=f"size in bytes; {_PENDING}"),
    fact_leaf("count", Grade.COMPARISON, doc=f"number of entries in a directory; {_PENDING}"),
    fact_leaf("format", Grade.COMPARISON, doc=f"detected format id; {_PENDING}"),
    fact_leaf("mtime", Grade.AUTHORITY, doc=f"modification time (ISO 8601); authority/recency only; {_PENDING}"),
    fact_leaf("ctime", Grade.AUTHORITY, doc=f"change time (ISO 8601), empty on S3; authority/recency only; {_PENDING}"),
)

_HASHES: tuple[TypeEntry, ...] = (
    hash_leaf(
        "md5", Grade.COMPARISON, Robustness.VERY_HIGH, doc=f"whole-object md5; length = bytes hashed; {_PENDING}"
    ),
    positional(
        "md5-region", Grade.COMPARISON, Robustness.VERY_HIGH, doc=f"md5 of bytes [offset, offset+length); {_PENDING}"
    ),
)

_HEAD = ("head", "md5-region")

_GLIMPSES: tuple[TypeEntry, ...] = (
    field_composite(
        "glimpse-content",
        (("file-size", "file-size"), _HEAD),
        Grade.COMPARISON,
        Robustness.LOW,
        doc=f"mtime-free file comparator: file-size + md5-region head 2 KB; {_PENDING}",
    ),
    field_composite(
        "glimpse",
        (("filename", "filename"), ("file-size", "file-size"), _HEAD, ("ctime", "ctime"), ("mtime", "mtime")),
        Grade.AUTHORITY,
        Robustness.LOW,
        doc=f"legacy v1 glimpse (authority-grade: carries name and times); {_PENDING}",
    ),
    field_composite(
        "glimpse-slim",
        (("filename", "filename"), ("file-size", "file-size"), ("mtime", "mtime"), _HEAD),
        Grade.AUTHORITY,
        Robustness.LOW,
        doc=f"legacy v1 slim glimpse; {_PENDING}",
    ),
    field_composite(
        "glimpse-light",
        (("file-size", "file-size"), _HEAD, ("mtime", "mtime")),
        Grade.AUTHORITY,
        Robustness.VERY_LOW,
        doc=f"legacy v1 light glimpse; {_PENDING}",
    ),
    field_composite(
        "glimpse-meta",
        (("filename", "filename"), ("file-size", "file-size"), ("mtime", "mtime")),
        Grade.AUTHORITY,
        Robustness.VERY_LOW,
        doc=f"legacy v1 meta glimpse (no hash); {_PENDING}",
    ),
    field_composite(
        "glimpse-dir-meta",
        (("filename", "filename"), ("mtime", "mtime"), ("count", "count")),
        Grade.AUTHORITY,
        Robustness.VERY_LOW,
        doc=f"legacy v1 directory meta (own fields only, no rollup); {_PENDING}",
    ),
)

_ROLLUPS: tuple[TypeEntry, ...] = (
    rollup(
        "glimpse-dir-content",
        Grade.COMPARISON,
        Robustness.LOW,
        doc=f"mtime-free folder rollup over glimpse-content children; {_PENDING}",
    ),
    rollup(
        "glimpse-dir",
        Grade.AUTHORITY,
        Robustness.LOW,
        roles=(("filename", "filename"), ("mtime", "mtime"), ("count", "count")),
        doc=f"legacy v1 directory glimpse: own filename/mtime/count then the named rollup; {_PENDING}",
    ),
    rollup(
        "glimpse-dir-slim",
        Grade.AUTHORITY,
        Robustness.LOW,
        roles=(("filename", "filename"), ("mtime", "mtime")),
        doc=f"legacy v1 slim directory glimpse; {_PENDING}",
    ),
    rollup(
        "glimpse-dir-light",
        Grade.AUTHORITY,
        Robustness.VERY_LOW,
        roles=(("mtime", "mtime"),),
        doc=f"legacy v1 light directory glimpse; {_PENDING}",
    ),
)

ROWS: tuple[TypeEntry, ...] = (*_FACTS, *_HASHES, *_GLIMPSES, *_ROLLUPS)

__all__ = ["ROWS"]
