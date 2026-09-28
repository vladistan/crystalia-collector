"""Lane A behaviour: fact leaves, ``md5``, ``md5-region`` and the content/legacy glimpses.

Thin helpers over :mod:`crystalia_data_model.types.canonical`; no type-specific encoding logic
lives here — the registry rows (``types/rows/leaves.py``) and the canonical encoder own that.
"""

from __future__ import annotations

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import mint_composite, mint_leaf, mint_positional
from crystalia_data_model.types.registry import Registry

ChildRef = "Descriptor | str"


def region_length(block: int, size: int, offset: int) -> int:
    """Chunk length for a region starting at ``offset`` in an object of ``size`` bytes (AC-07)."""
    return min(block, size - offset)


# --------------------------------------------------------------------------- fact leaves


def mint_filename(value: str, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("filename", value, registry=registry)


def mint_relpath(value: str, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("relpath", value, registry=registry)


def mint_file_size(value: int, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("file-size", str(value), registry=registry)


def mint_count(value: int, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("count", str(value), registry=registry)


def mint_format(value: str, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("format", value, registry=registry)


def mint_mtime(value: str, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("mtime", value, registry=registry)


def mint_ctime(value: str, *, registry: Registry | None = None) -> Descriptor:
    return mint_leaf("ctime", value, registry=registry)


# --------------------------------------------------------------------------- hash / positional


def mint_md5(value: str, *, length: int | None = None, registry: Registry | None = None) -> Descriptor:
    """Whole-object md5; ``length`` = bytes hashed, always required (FR-005)."""
    return mint_leaf("md5", value, length=length, registry=registry)


def mint_md5_region(offset: int, length: int, value: str, *, registry: Registry | None = None) -> Descriptor:
    """``md5`` of bytes ``[offset, offset+length)``; same bytes at another offset is another IRI (AC-07)."""
    return mint_positional("md5-region", offset, length, value, registry=registry)


# --------------------------------------------------------------------------- content glimpse (mtime-free)


def mint_glimpse_content(
    *, file_size: Descriptor | str, head: Descriptor | str, registry: Registry | None = None
) -> Descriptor:
    """{file-size, md5-region head 2 KB}: comparison-grade, LOW, no filename/ctime/mtime (AC-09)."""
    return mint_composite("glimpse-content", {"file-size": file_size, "head": head}, registry=registry)


# --------------------------------------------------------------------------- legacy glimpses (authority-grade)


def mint_glimpse(
    *,
    filename: Descriptor | str,
    file_size: Descriptor | str,
    head: Descriptor | str,
    ctime: Descriptor | str,
    mtime: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return mint_composite(
        "glimpse",
        {"filename": filename, "file-size": file_size, "head": head, "ctime": ctime, "mtime": mtime},
        registry=registry,
    )


def mint_glimpse_slim(
    *,
    filename: Descriptor | str,
    file_size: Descriptor | str,
    mtime: Descriptor | str,
    head: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return mint_composite(
        "glimpse-slim",
        {"filename": filename, "file-size": file_size, "mtime": mtime, "head": head},
        registry=registry,
    )


def mint_glimpse_light(
    *,
    file_size: Descriptor | str,
    head: Descriptor | str,
    mtime: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return mint_composite(
        "glimpse-light", {"file-size": file_size, "head": head, "mtime": mtime}, registry=registry
    )


def mint_glimpse_meta(
    *,
    filename: Descriptor | str,
    file_size: Descriptor | str,
    mtime: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return mint_composite(
        "glimpse-meta", {"filename": filename, "file-size": file_size, "mtime": mtime}, registry=registry
    )


def mint_glimpse_dir_meta(
    *,
    filename: Descriptor | str,
    mtime: Descriptor | str,
    count: Descriptor | str,
    registry: Registry | None = None,
) -> Descriptor:
    return mint_composite(
        "glimpse-dir-meta", {"filename": filename, "mtime": mtime, "count": count}, registry=registry
    )


__all__ = [
    "mint_count",
    "mint_ctime",
    "mint_file_size",
    "mint_filename",
    "mint_format",
    "mint_glimpse",
    "mint_glimpse_content",
    "mint_glimpse_dir_meta",
    "mint_glimpse_light",
    "mint_glimpse_meta",
    "mint_glimpse_slim",
    "mint_md5",
    "mint_md5_region",
    "mint_mtime",
    "mint_relpath",
    "region_length",
]
