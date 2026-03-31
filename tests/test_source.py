"""Tests for the source abstraction layer — FileObject and Source Protocol.

Step 2.1 (TDD): Tests written before implementation.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from crystalia_collector.source import FileObject, Source

_NOW = datetime(2024, 1, 1, tzinfo=UTC)


def test_file_object_required_fields_stored():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    assert f.uri == "/abs/path/file.txt"
    assert f.basename == "file.txt"
    assert f.size == 1024
    assert f.mtime == _NOW


def test_file_object_ctime_defaults_to_none():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    assert f.ctime is None


def test_file_object_etag_defaults_to_none():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    assert f.etag is None


def test_file_object_ctime_can_be_provided():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW, ctime=_NOW)
    assert f.ctime == _NOW


def test_file_object_etag_can_be_provided():
    f = FileObject(
        uri="s3://bucket/key",
        basename="key",
        size=2048,
        mtime=_NOW,
        etag="098f6bcd4621d373cade4e832627b4f6",  # pragma: allowlist secret
    )
    assert f.etag is not None


def test_file_object_s3_uri_with_no_optional_fields():
    f = FileObject(uri="s3://bucket/prefix/file.txt", basename="file.txt", size=2048, mtime=_NOW)
    assert f.uri.startswith("s3://")
    assert f.ctime is None
    assert f.etag is None


def test_file_object_s3_uri_with_both_optional_fields():
    f = FileObject(
        uri="s3://bucket/prefix/file.txt",
        basename="file.txt",
        size=2048,
        mtime=_NOW,
        ctime=_NOW,
        etag="abc123",
    )
    assert f.ctime == _NOW
    assert f.etag == "abc123"


def test_file_object_uri_is_frozen():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    with pytest.raises(ValidationError):
        f.uri = "/other/path"


def test_file_object_basename_is_frozen():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    with pytest.raises(ValidationError):
        f.basename = "other.txt"


def test_file_object_size_is_frozen():
    f = FileObject(uri="/abs/path/file.txt", basename="file.txt", size=1024, mtime=_NOW)
    with pytest.raises(ValidationError):
        f.size = 9999


def test_source_protocol_conforming_class_satisfies_isinstance():
    class GoodSource:
        def list_files(self, prefix: str) -> Iterator[FileObject]:
            return iter([])

        def compute_checksum(self, uri: str, offset: int, length: int | None) -> str:
            return ""

    assert isinstance(GoodSource(), Source)


def test_source_protocol_missing_list_files_fails_isinstance():
    class NoListFiles:
        def compute_checksum(self, uri: str, offset: int, length: int | None) -> str:
            return ""

    assert not isinstance(NoListFiles(), Source)


def test_source_protocol_missing_compute_checksum_fails_isinstance():
    class NoChecksum:
        def list_files(self, prefix: str) -> Iterator[FileObject]:
            return iter([])

    assert not isinstance(NoChecksum(), Source)


def test_source_protocol_empty_class_fails_isinstance():
    class Empty:
        pass

    assert not isinstance(Empty(), Source)
