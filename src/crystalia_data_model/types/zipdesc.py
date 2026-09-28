"""Zip central-directory parsing + ``zip-cd`` / ``zip-manifest`` descriptors (FR-014, FR-016; step 5.5).

Minted only when the caller has already located and read the EOCD + whole Central Directory
(``detect_format`` / ``formats._detect_zip`` locate the region; this module parses and mints from
the raw bytes). ``zip-cd`` is a plain hash leaf over the raw CD bytes (authority-grade: timestamps
inside member headers make it move under a re-zip). ``zip-manifest`` hashes only the sorted,
NFC-normalized (member name, CRC-32, uncompressed size) triples, so re-zipping/recompressing
identical content reproduces the same IRI (comparison-grade, no ``length``).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.canonical import digest, mint_leaf, nfc
from crystalia_data_model.types.registry import Registry, default_registry

_CD_SIG = b"PK\x01\x02"
_CD_HEADER_LEN = 46


@dataclass(frozen=True, slots=True)
class ZipMember:
    """One Central Directory file header entry (APPNOTE §4.3.12)."""

    name: str
    crc32: int
    uncompressed_size: int


def parse_central_directory(cd_bytes: bytes) -> list[ZipMember]:
    """Every member header in ``cd_bytes``; stops at the first non-signature byte (truncated CD)."""
    members: list[ZipMember] = []
    pos = 0
    while pos + _CD_HEADER_LEN <= len(cd_bytes) and cd_bytes[pos : pos + 4] == _CD_SIG:
        crc32 = int.from_bytes(cd_bytes[pos + 16 : pos + 20], "little")
        usize = int.from_bytes(cd_bytes[pos + 24 : pos + 28], "little")
        nlen = int.from_bytes(cd_bytes[pos + 28 : pos + 30], "little")
        elen = int.from_bytes(cd_bytes[pos + 30 : pos + 32], "little")
        clen = int.from_bytes(cd_bytes[pos + 32 : pos + 34], "little")
        name_start = pos + _CD_HEADER_LEN
        name = cd_bytes[name_start : name_start + nlen].decode("utf-8", "surrogateescape")
        members.append(ZipMember(name, crc32, usize))
        pos = name_start + nlen + elen + clen
    return members


def _manifest_line(name: str, crc32: int, usize: int) -> bytes:
    n = nfc(name).encode()
    return f"name={len(n)}:".encode() + n + f" crc32={crc32} size={usize}\n".encode()


def _manifest_bytes(members: Iterable[tuple[str, int, int]]) -> bytes:
    sorted_members = sorted(
        ((nfc(name), crc32, usize) for name, crc32, usize in members), key=lambda m: (m[0].encode(), m[1], m[2])
    )
    return b"".join(_manifest_line(*m) for m in sorted_members)


def mint_zip_cd(cd_bytes: bytes, *, registry: Registry | None = None) -> Descriptor:
    """``zip-cd``: a plain hash leaf over the raw Central Directory bytes (R2: blind to bytes
    outside the archive; a file-size fact leaf on the Item covers that separately)."""
    reg = registry or default_registry()
    return mint_leaf("zip-cd", digest(cd_bytes), length=len(cd_bytes), registry=reg)


def mint_zip_manifest(members: Iterable[tuple[str, int, int] | ZipMember], *, registry: Registry | None = None) -> Descriptor:
    """``zip-manifest``: comparison-grade fingerprint of (NFC member name, CRC-32, uncompressed size)."""
    reg = registry or default_registry()
    triples = [(m.name, m.crc32, m.uncompressed_size) if isinstance(m, ZipMember) else m for m in members]
    return mint_leaf("zip-manifest", digest(_manifest_bytes(triples)), registry=reg)


__all__ = ["ZipMember", "mint_zip_cd", "mint_zip_manifest", "parse_central_directory"]
