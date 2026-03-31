import hashlib
from datetime import UTC
from unittest.mock import patch

from crystalia_collector.source import FileObject
from crystalia_collector.source.local import LocalSource


def test_list_files_yields_file_objects(tmp_path):
    (tmp_path / "file1.txt").write_bytes(b"hello")
    (tmp_path / "file2.txt").write_bytes(b"world")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert len(files) == 2
    assert all(isinstance(f, FileObject) for f in files)
    assert {f.basename for f in files} == {"file1.txt", "file2.txt"}


def test_list_files_empty_directory_yields_nothing(tmp_path):
    assert list(LocalSource().list_files(str(tmp_path))) == []


def test_list_files_uri_is_absolute_path(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"data")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert files[0].uri == str((tmp_path / "file.txt").resolve())


def test_list_files_correct_size(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"12345")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert files[0].size == 5


def test_list_files_captures_utc_timestamps(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"data")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert files[0].mtime is not None
    assert files[0].mtime.tzinfo is UTC
    assert files[0].ctime is not None
    assert files[0].ctime.tzinfo is UTC


def test_list_files_etag_is_none(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"data")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert files[0].etag is None


def test_list_files_recursive(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (tmp_path / "top.txt").write_bytes(b"top")
    (subdir / "nested.txt").write_bytes(b"nested")

    files = list(LocalSource().list_files(str(tmp_path)))

    assert {f.basename for f in files} == {"top.txt", "nested.txt"}


def test_list_files_skips_on_permission_error(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"data")

    with patch("crystalia_collector.source.local.os.stat", side_effect=PermissionError):
        files = list(LocalSource().list_files(str(tmp_path)))

    assert files == []


def test_compute_checksum_full_file(tmp_path):
    data = b"hello world"
    path = tmp_path / "file.txt"
    path.write_bytes(data)

    result = LocalSource().compute_checksum(str(path), 0, None)

    assert result == hashlib.md5(data).hexdigest()


def test_compute_checksum_partial_read(tmp_path):
    data = b"hello world"
    path = tmp_path / "file.txt"
    path.write_bytes(data)

    result = LocalSource().compute_checksum(str(path), 0, 8)

    assert result == hashlib.md5(data[:8]).hexdigest()


def test_compute_checksum_with_offset(tmp_path):
    data = b"hello world"
    path = tmp_path / "file.txt"
    path.write_bytes(data)

    result = LocalSource().compute_checksum(str(path), 6, 5)

    assert result == hashlib.md5(data[6:11]).hexdigest()


def test_compute_checksum_zero_byte_file(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")

    result = LocalSource().compute_checksum(str(path), 0, None)

    assert result == "d41d8cd98f00b204e9800998ecf8427e"  # pragma: allowlist secret
