"""Guard: no collector-local IRI construction survives the DM v2 migration.

`hashlib.md5(` is legitimate for content checksums (source/local.py, source/s3.py);
what must be gone is the pattern that fed a "type:value" string into it to mint an
IRI locally, bypassing the DM's canonical minting.
"""

import re
from pathlib import Path

_SRC = Path(__file__).parent.parent / "src" / "crystalia_collector"

_LOCAL_MINTING_NAMES = ("_content_id", "_descriptor_id", "_composite_v0", "_rollup_v0")

# The IRI-minting pattern this migration removed: hashlib.md5(f"{type}:{value}"...).
_TYPE_VALUE_HASH_PATTERN = re.compile(r'hashlib\.md5\(f["\'].*\{.*\}:\{.*\}')


def test_no_local_minting_helpers_defined():
    for path in _SRC.rglob("*.py"):
        source = path.read_text()
        for name in _LOCAL_MINTING_NAMES:
            assert f"def {name}(" not in source, f"{path}: local minting helper {name!r} still defined"


def test_no_type_value_hash_for_iri_construction():
    for path in _SRC.rglob("*.py"):
        source = path.read_text()
        assert not _TYPE_VALUE_HASH_PATTERN.search(source), f"{path}: type:value hashlib.md5 IRI construction found"
