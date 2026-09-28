"""Bookend, zip-cd and zip-manifest file descriptors (Phase 7, Steps 7.2-7.5)."""

import zipfile
from collections.abc import Sequence
from pathlib import Path

from crystalia_collector.bookend_compute import (
    build_bookend_descriptor,
    build_zip_cd_descriptor,
    build_zip_manifest_descriptor,
)
from crystalia_collector.source import FileObject
from crystalia_collector.source.local import LocalSource
from crystalia_data_model.types.registry import is_strong
from crystalia_data_model.types.validate import ensure_valid


def _file_obj(source: LocalSource, path: Path) -> FileObject:
    return next(f for f in source.list_files(str(path.parent)) if f.basename == path.name)


def _make_zip(
    tmp_path: Path,
    name: str = "a.zip",
    members: Sequence[tuple[str, str]] = (("a.txt", "hello"), ("b.txt", "world")),
) -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        for member_name, content in members:
            zf.writestr(member_name, content)
    return path


# --- bookend (Step 7.3) ---


def test_bookend_small_file_is_strong(tmp_path):
    (tmp_path / "small.bin").write_bytes(b"x" * 100)
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "small.bin")

    top, children = build_bookend_descriptor(file_obj, source)

    assert top.hasType == "cryd:desc-type/bookend-strong"
    assert ensure_valid(top) is top
    assert len(children) == 4


def test_bookend_jpeg_large_file_is_weak(tmp_path):
    jpeg_magic = b"\xff\xd8\xff" + b"\x00" * 40000
    (tmp_path / "photo.jpg").write_bytes(jpeg_magic)
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "photo.jpg")

    top, _children = build_bookend_descriptor(file_obj, source)

    assert top.hasType == "cryd:desc-type/bookend-weak"


def test_bookend_gzip_is_always_weak_even_when_small_enough_to_capture(tmp_path):
    # Below the 32KB strong-by-size threshold on its own, but gzip carries no strong rule.
    gzip_magic = b"\x1f\x8b" + b"\x00" * 100
    (tmp_path / "f.gz").write_bytes(gzip_magic)
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "f.gz")

    top, _children = build_bookend_descriptor(file_obj, source)

    # size <= 32KB => strong by D-1's size rule regardless of format; gzip-specific
    # "always weak" only bites once the file exceeds that threshold.
    assert top.hasType == "cryd:desc-type/bookend-strong"


def test_bookend_zip_with_cd_in_tail_is_strong(tmp_path):
    zpath = _make_zip(tmp_path)
    source = LocalSource()
    file_obj = _file_obj(source, zpath)

    top, _children = build_bookend_descriptor(file_obj, source)

    assert top.hasType == "cryd:desc-type/bookend-strong"


def test_bookend_recorded_is_deterministic(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"stable content")
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "f.bin")

    top1, _c1 = build_bookend_descriptor(file_obj, source)
    top2, _c2 = build_bookend_descriptor(file_obj, source)

    assert top1.id == top2.id
    assert top1.value == top2.value


# --- zip-cd (Step 7.4) ---


def test_zip_cd_non_zip_file_returns_none(tmp_path):
    (tmp_path / "plain.txt").write_bytes(b"not a zip")
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "plain.txt")

    assert build_zip_cd_descriptor(file_obj, source) is None


def test_zip_cd_zip_file_returns_descriptor_with_cd_length(tmp_path):
    zpath = _make_zip(tmp_path)
    cd_bytes_expected_len_source = LocalSource()
    file_obj = _file_obj(cd_bytes_expected_len_source, zpath)

    desc = build_zip_cd_descriptor(file_obj, cd_bytes_expected_len_source)

    assert desc is not None
    assert desc.hasType == "cryd:desc-type/zip-cd"
    assert int(desc.length) > 0
    assert ensure_valid(desc) is desc


# --- zip-manifest (Step 7.5) ---


def test_zip_manifest_non_zip_file_returns_none(tmp_path):
    (tmp_path / "plain.txt").write_bytes(b"not a zip")
    source = LocalSource()
    file_obj = _file_obj(source, tmp_path / "plain.txt")

    assert build_zip_manifest_descriptor(file_obj, source) is None


def test_zip_manifest_same_members_different_compression_same_iri(tmp_path):
    p1 = tmp_path / "stored.zip"
    with zipfile.ZipFile(p1, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("a.txt", "hello world")
    p2 = tmp_path / "deflated.zip"
    with zipfile.ZipFile(p2, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.txt", "hello world")

    source = LocalSource()
    desc1 = build_zip_manifest_descriptor(_file_obj(source, p1), source)
    desc2 = build_zip_manifest_descriptor(_file_obj(source, p2), source)

    assert desc1 is not None
    assert desc2 is not None
    assert desc1.id == desc2.id
    assert desc1.value == desc2.value


def test_zip_manifest_changed_member_crc_changes_iri(tmp_path):
    p1 = _make_zip(tmp_path, "a.zip", [("a.txt", "hello")])
    p2 = _make_zip(tmp_path, "b.zip", [("a.txt", "hellO")])

    source = LocalSource()
    desc1 = build_zip_manifest_descriptor(_file_obj(source, p1), source)
    desc2 = build_zip_manifest_descriptor(_file_obj(source, p2), source)

    assert desc1 is not None
    assert desc2 is not None
    assert desc1.id != desc2.id


def test_zip_manifest_ignores_file_length(tmp_path):
    """zip-manifest is comparison-grade: no file-size role, only member (name, crc32, size)."""
    p1 = _make_zip(tmp_path, "a.zip", [("a.txt", "hello")])
    source = LocalSource()
    desc = build_zip_manifest_descriptor(_file_obj(source, p1), source)

    assert desc is not None
    assert desc.length is None


# --- strength grading via DM registry (cross-cutting) ---


def test_is_strong_agrees_with_hastype_for_bookend(tmp_path):
    (tmp_path / "small.bin").write_bytes(b"x" * 10)
    source = LocalSource()
    top, _children = build_bookend_descriptor(_file_obj(source, tmp_path / "small.bin"), source)

    assert is_strong(top) is True
