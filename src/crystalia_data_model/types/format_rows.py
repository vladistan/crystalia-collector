"""Format registry rows (Lane C; step 5.1/5.2). Every row's ``spec_ref`` is verified in
``tests/fixtures/formats/SPEC-REFS.md``; a row's ``strong_rule`` is verified there too, or the
loader (:mod:`crystalia_data_model.types.formats`) demotes it to OPAQUE at load time (AC-16).
"""

from __future__ import annotations

from crystalia_data_model.types.formats import Family, FormatEntry

_APPNOTE = "PKWARE APPNOTE.TXT .ZIP File Format Specification v6.3.10 §4.3.6/§4.3.12/§4.3.16"

ROWS: tuple[FormatEntry, ...] = (
    FormatEntry(
        id="zip",
        family=Family.TAIL,
        magic=b"PK\x03\x04",
        spec_ref=_APPNOTE,
        rule_spec_ref=_APPNOTE,
        strong_rule="cd_in_tail",
        region_rule="cd_region",
    ),
    FormatEntry(
        id="npz",
        family=Family.TAIL,
        magic=b"PK\x03\x04",
        spec_ref=_APPNOTE + " + numpy.lib.format (.npz member convention)",
        rule_spec_ref=_APPNOTE,
        strong_rule="cd_in_tail",
        region_rule="cd_region",
    ),
    FormatEntry(
        id="gzip",
        family=Family.OPAQUE,
        magic=b"\x1f\x8b",
        spec_ref="RFC 1952 GZIP file format specification v4.3 §2.3",
    ),
    FormatEntry(
        id="jpeg",
        family=Family.OPAQUE,
        magic=b"\xff\xd8\xff",
        spec_ref="ITU-T T.81 | ISO/IEC 10918-1 (JPEG) Annex B.1.1.3 (SOI marker)",
    ),
    FormatEntry(
        id="png",
        family=Family.OPAQUE,
        magic=b"\x89PNG\r\n\x1a\n",
        spec_ref="ISO/IEC 15948:2004 (PNG) §5.2 (file signature)",
    ),
    FormatEntry(
        id="gif",
        family=Family.OPAQUE,
        magic=b"GIF89a",
        spec_ref="CompuServe GIF89a Specification (1990) §17 (Header block)",
    ),
)

__all__ = ["ROWS"]
