"""Edge-case coverage for local listing and descriptor computation (Plan 02
Phase 6.1): empty directories, zero-byte files, unusual filenames, and
unreadable files."""

import os

import pytest

from crystalia_collector.source.local import LocalSource
from crystalia_collector.work import run_pipeline

_MD5_EMPTY = "d41d8cd98f00b204e9800998ecf8427e"


def test_list_files_empty_dir(tmp_path):
    assert list(LocalSource().list_files(str(tmp_path))) == []


def test_list_files_zero_byte_file(tmp_path):
    (tmp_path / "empty.bin").write_bytes(b"")
    file_list = list(LocalSource().list_files(str(tmp_path)))
    assert len(file_list) == 1
    assert file_list[0].size == 0


def test_checksum_zero_byte_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    assert LocalSource().compute_checksum(str(f), 0, None) == _MD5_EMPTY


def test_list_files_non_ascii_filename(tmp_path):
    # APFS enforces valid UTF-8 names, so exercise non-ASCII Unicode rather
    # than raw invalid bytes (which cannot be created on macOS).
    name = "café_文件_🔬.txt"
    (tmp_path / name).write_text("data")
    files = list(LocalSource().list_files(str(tmp_path)))
    assert len(files) == 1
    assert files[0].basename == name


def test_checksum_unreadable_file_raises(tmp_path):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root bypasses file permissions")
    f = tmp_path / "secret.bin"
    f.write_text("classified")
    f.chmod(0o000)
    try:
        with pytest.raises(PermissionError):
            LocalSource().compute_checksum(str(f), 0, None)
    finally:
        f.chmod(0o644)  # restore so tmp_path cleanup can remove it


def test_run_pipeline_empty_dir(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    out = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data), ["md5-8gb"], out, workers=1, fmt="turtle")
    assert result.succeeded == 0
    assert result.failed == 0
    assert out.exists()


def test_run_pipeline_zero_byte_file_glimpse(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "empty.txt").write_bytes(b"")
    out = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data), ["glimpse"], out, workers=1, fmt="turtle")
    assert result.succeeded == 1
    assert out.exists()
