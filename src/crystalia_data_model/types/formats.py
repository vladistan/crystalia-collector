"""Format registry: rows, loader rules and detection (FR-014; plan 06 Lane C, steps 5.2/5.3).

The row *shape* (:class:`FormatEntry`) and the simple ``lookup`` seam were laid down in the
foundation (Ph2 step 2.4) against an empty :mod:`crystalia_data_model.types.format_rows`. Lane C
owns the whole file from here: the loader that turns rows into a validated registry
(``RegistryLoadError`` on a missing detection ``spec_ref``; OPAQUE demotion of a ``strong_rule``
lacking a verified ``rule_spec_ref``, logged once and exposed via ``unverified_rules()``), and
``detect_format`` for the v2 format set (zip family incl. npz, gzip, JPEG, PNG, GIF).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum
from functools import cache

from crystalia_data_model.types.errors import RegistryLoadError

logger = logging.getLogger("crystalia_data_model")


class Family(StrEnum):
    HEAD = "head"
    TAIL = "tail"
    BLOCK = "block"
    OPAQUE = "opaque"


@dataclass(frozen=True, slots=True)
class FormatEntry:
    """One format row.

    ``spec_ref``       verified reference for the detection (magic) rule — mandatory;
    ``rule_spec_ref``  separately verified reference for the strong / region rule, else the row is OPAQUE;
    ``strong_rule``    name of the rule deciding STRONG for this family (``None`` = never strong);
    ``region_rule``    name of the rule giving object-relative region coverage (``None`` = literal).
    """

    id: str
    family: Family
    magic: bytes
    spec_ref: str
    rule_spec_ref: str | None = None
    strong_rule: str | None = None
    region_rule: str | None = None


@dataclass(frozen=True, slots=True)
class Detection:
    """What ``detect_format`` found: a format id (or ``None`` = unrecognized), the rule that
    applied (if any) and, on a zip-family failure mode, a stable ``reason`` code.
    """

    format_id: str | None
    family: Family
    summary_region: tuple[int, int] | None
    rule_applied: str | None
    reason: str | None


class FormatRegistry:
    """A validated, demotion-applied set of format rows (loader rules, AC-16)."""

    def __init__(self, rows: Iterable[FormatEntry]) -> None:
        by_id: dict[str, FormatEntry] = {}
        demoted: list[str] = []
        for row in rows:
            if not isinstance(row, FormatEntry):
                raise RegistryLoadError(f"format row is not a FormatEntry: {row!r}")
            if not row.spec_ref:
                raise RegistryLoadError(f"format row {row.id!r} has no detection spec_ref")
            if row.id in by_id:
                raise RegistryLoadError(f"duplicate format row: {row.id!r}")
            if row.strong_rule is not None and not row.rule_spec_ref:
                row = replace(row, strong_rule=None)
                demoted.append(row.id)
            by_id[row.id] = row
        if demoted:
            logger.info(
                "format registry: demoted to OPAQUE (unverified strong rule): %s", ", ".join(sorted(demoted))
            )
        self._by_id: dict[str, FormatEntry] = by_id
        self._unverified: tuple[str, ...] = tuple(sorted(demoted))

    def lookup(self, format_id: str) -> FormatEntry | None:
        return self._by_id.get(format_id)

    def unverified_rules(self) -> tuple[str, ...]:
        return self._unverified


def load_formats(rows: Iterable[FormatEntry]) -> FormatRegistry:
    return FormatRegistry(rows)


@cache
def default_format_registry() -> FormatRegistry:
    from crystalia_data_model.types import format_rows

    return load_formats(format_rows.ROWS)


@cache
def _table() -> dict[str, FormatEntry]:
    from crystalia_data_model.types import format_rows

    return {row.id: row for row in format_rows.ROWS}


def lookup(format_id: str) -> FormatEntry | None:
    """The (possibly demoted) row for a format id, or ``None`` when the format is unknown."""
    return default_format_registry().lookup(format_id)


def unverified_rules() -> tuple[str, ...]:
    """Format ids whose ``strong_rule`` was demoted to OPAQUE for want of a verified ``rule_spec_ref``."""
    return default_format_registry().unverified_rules()


# --------------------------------------------------------------------------- detection (step 5.3)

_GZIP_MAGIC = b"\x1f\x8b"
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_GIF_MAGICS = (b"GIF87a", b"GIF89a")
_ZIP_LOCAL_SIG = b"PK\x03\x04"
_ZIP_EOCD_SIG = b"PK\x05\x06"
_ZIP_EOCD64_LOCATOR_SIG = b"PK\x06\x07"

_ZIP64_SENTINEL = 0xFFFFFFFF
_EOCD_MIN_LEN = 22
_MAX_COMMENT_LEN = 0xFFFF


@dataclass(frozen=True, slots=True)
class _Eocd:
    cd_offset: int
    cd_size: int
    zip64: bool


def _locate_eocd(tail: bytes) -> _Eocd | None:
    """Scan ``tail`` backward for a well-formed End Of Central Directory record.

    A candidate is accepted only when its declared comment length exactly accounts for every
    remaining byte of ``tail`` (APPNOTE §4.3.16); this rejects an EOCD signature that merely
    happens to appear inside an earlier member's data or comment.
    """
    n = len(tail)
    search_from = n
    while True:
        idx = tail.rfind(_ZIP_EOCD_SIG, 0, search_from)
        if idx == -1 or idx + _EOCD_MIN_LEN > n:
            return None
        comment_len = int.from_bytes(tail[idx + 20 : idx + 22], "little")
        if idx + _EOCD_MIN_LEN + comment_len == n:
            cd_size = int.from_bytes(tail[idx + 12 : idx + 16], "little")
            cd_offset = int.from_bytes(tail[idx + 16 : idx + 20], "little")
            zip64 = cd_size == _ZIP64_SENTINEL or cd_offset == _ZIP64_SENTINEL
            if not zip64 and idx >= 20 and tail[idx - 20 : idx - 16] == _ZIP_EOCD64_LOCATOR_SIG:
                zip64 = True
            return _Eocd(cd_offset, cd_size, zip64)
        search_from = idx


def _parse_central_directory_names(cd_bytes: bytes) -> list[str]:
    from crystalia_data_model.types.zipdesc import parse_central_directory

    return [m.name for m in parse_central_directory(cd_bytes)]


def _detect_zip(head: bytes, tail: bytes | None, size: int) -> Detection:
    if tail is None:
        if size <= len(head):
            tail, tail_start = head, 0
        else:
            return Detection("zip", Family.TAIL, None, None, "bad_eocd")
    else:
        tail_start = max(0, size - len(tail))
    eocd = _locate_eocd(tail)
    if eocd is None:
        return Detection("zip", Family.TAIL, None, None, "bad_eocd")
    region = (eocd.cd_offset, eocd.cd_size)
    if eocd.zip64:
        return Detection("zip", Family.TAIL, region, None, "zip64_unverified")
    cd_start_in_tail = eocd.cd_offset - tail_start
    if cd_start_in_tail < 0 or cd_start_in_tail + eocd.cd_size > len(tail):
        return Detection("zip", Family.TAIL, region, None, "cd_outside_tail")
    cd_bytes = tail[cd_start_in_tail : cd_start_in_tail + eocd.cd_size]
    names = _parse_central_directory_names(cd_bytes)
    format_id = "npz" if names and all(n.endswith(".npy") for n in names) else "zip"
    return Detection(format_id, Family.TAIL, region, "cd_in_tail", None)


def detect_format(head: bytes, tail: bytes | None, size: int) -> Detection:
    """Detect the v2 format set from a captured head (+ optional tail) of a ``size``-byte object.

    Never raises: malformed or truncated data degrades to a ``Detection`` with ``format_id=None``
    (unrecognized) or a zip-family ``reason`` code, never an exception.
    """
    if head.startswith(_GZIP_MAGIC):
        return Detection("gzip", Family.OPAQUE, None, None, None)
    if head.startswith(_PNG_MAGIC):
        return Detection("png", Family.OPAQUE, None, None, None)
    if head.startswith(_JPEG_MAGIC):
        return Detection("jpeg", Family.OPAQUE, None, None, None)
    if head.startswith(_GIF_MAGICS):
        return Detection("gif", Family.OPAQUE, None, None, None)
    if head.startswith(_ZIP_LOCAL_SIG) or head.startswith(_ZIP_EOCD_SIG) or (tail is not None and _ZIP_EOCD_SIG in tail):
        return _detect_zip(head, tail, size)
    return Detection(None, Family.OPAQUE, None, None, "unknown")


__all__ = [
    "Detection",
    "Family",
    "FormatEntry",
    "FormatRegistry",
    "default_format_registry",
    "detect_format",
    "load_formats",
    "lookup",
    "unverified_rules",
]
