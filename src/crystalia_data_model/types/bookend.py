"""Bookend judgement + minting: fixed 16 KB head + 16 KB tail (FR-015; step 5.4; D-1).

The judgement is shared by the collector (which type to store) and inference (Phase 6's
bookend/md5-chunked agreement rule read it too): STRONG when every byte is covered outright
(``size <= 32 KB``) or the captured blocks pin every byte a verified format rule needs (zip with
its whole Central Directory inside the 16 KB tail); WEAK otherwise, with the failure reason
carried through unchanged from :func:`crystalia_data_model.types.formats.detect_format`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import mint_composite, mint_leaf, mint_positional
from crystalia_data_model.types.formats import Detection, Family, lookup
from crystalia_data_model.types.registry import Registry, default_registry
from crystalia_data_model.types.rollup import rollup_dir

BLOCK = 16384
STRONG_BY_SIZE = 2 * BLOCK


@dataclass(frozen=True, slots=True)
class Verdict:
    """``judge_bookend``'s result: whether the bookend is strong, and why not when it isn't."""

    strong: bool
    reason: str | None


def judge_bookend(size: int, detection: Detection) -> Verdict:
    """D-1: size <= 32 KB is always STRONG; otherwise STRONG only for a verified, wholly-captured
    rule (e.g. zip with its Central Directory inside the tail); every other case is WEAK with the
    detector's own reason code, or ``"opaque"`` when the format carries no strong rule at all.
    """
    if size <= STRONG_BY_SIZE:
        return Verdict(True, None)
    if detection.reason is not None:
        return Verdict(False, detection.reason)
    if detection.rule_applied is None or detection.format_id is None:
        return Verdict(False, "opaque")
    entry = lookup(detection.format_id)
    if entry is None or entry.family not in (Family.HEAD, Family.TAIL) or entry.strong_rule is None:
        return Verdict(False, "opaque")
    return Verdict(True, None)


def mint_bookend(
    head: str,
    tail: str,
    format_id: str,
    size: int,
    detection: Detection,
    *,
    registry: Registry | None = None,
) -> Descriptor:
    """Mint the head/tail region descriptors, the format + file-size fact leaves, and the resulting
    ``bookend-strong`` or ``bookend-weak`` field composite (D-1). ``head``/``tail`` are the md5 hex
    digests of the captured blocks (a file <= 16 KB has ``head == tail``: one region IRI, repeated
    by role — a known, RDF-collapsed deviation the caller's ``resolve=`` contract must honour).
    """
    reg = registry or default_registry()
    head_len = min(BLOCK, size)
    tail_start = max(0, size - BLOCK)
    tail_len = size - tail_start
    head_d = mint_positional("md5-region", 0, head_len, head, registry=reg)
    tail_d = mint_positional("md5-region", tail_start, tail_len, tail, registry=reg)
    size_d = mint_leaf("file-size", str(size), registry=reg)
    format_d = mint_leaf("format", format_id, registry=reg)
    verdict = judge_bookend(size, detection)
    type_name = "bookend-strong" if verdict.strong else "bookend-weak"
    return mint_composite(
        type_name,
        {"head": head_d, "tail": tail_d, "format": format_d, "file-size": size_d},
        registry=reg,
    )


# --------------------------------------------------------------------------- bookend-dir (Phase 7)


@dataclass(frozen=True, slots=True)
class DirEntry:
    """One named child of a directory, carrying every D-3 candidate descriptor a harvester may have
    minted for it. ``choose()`` applies D-3 in fixed priority: a zip with a readable Central
    Directory contributes its ``zip-manifest``; a subdirectory contributes its own ``bookend-dir-*``
    (recursive); anything else contributes its ``bookend-strong``/``bookend-weak``.
    """

    name: str
    zip_manifest: Descriptor | None = None
    bookend_dir: Descriptor | None = None
    bookend: Descriptor | None = None

    def choose(self) -> Descriptor:
        for candidate in (self.zip_manifest, self.bookend_dir, self.bookend):
            if candidate is not None:
                return candidate
        raise ValueError(f"{self.name}: no D-3 candidate descriptor supplied (zip_manifest/bookend_dir/bookend)")


def mint_bookend_dir(
    expected: int,
    entries: Iterable[DirEntry],
    *,
    registry: Registry | None = None,
) -> Descriptor:
    """``bookend-dir-strong`` iff every child (chosen per D-3) is strong, else ``bookend-dir-weak``
    (D-4); missing children raise :class:`crystalia_data_model.types.errors.IncompleteRollup` via
    :func:`crystalia_data_model.types.rollup.rollup_dir` (no ``total`` stored, coverage 1.0 by type).
    """
    reg = registry or default_registry()
    named = [(entry.name, entry.choose()) for entry in entries]
    all_strong = all(reg.is_strong(child) for _, child in named)
    variant = "bookend-dir-strong" if all_strong else "bookend-dir-weak"
    return rollup_dir(variant, expected, named, registry=reg)


__all__ = [
    "BLOCK",
    "STRONG_BY_SIZE",
    "DirEntry",
    "Verdict",
    "judge_bookend",
    "mint_bookend",
    "mint_bookend_dir",
]
