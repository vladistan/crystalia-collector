import hashlib
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from crystalia_collector.glimpse_compute import build_file_descriptor
from crystalia_collector.method.glimpse import Glimpse, GlimpseLight, GlimpseMeta, GlimpseSlim
from crystalia_collector.source import FileObject
from crystalia_collector.source.local import LocalSource

_NOW = datetime(2024, 6, 1, tzinfo=UTC)


# --- local file variant tests ---


def test_glimpse_zero_byte_file(tmp_path):
    (tmp_path / "empty.txt").write_bytes(b"")
    source = LocalSource()
    file_obj = next(f for f in source.list_files(str(tmp_path)) if f.basename == "empty.txt")

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    assert top.value.startswith("v0:")
    assert top.coverage == 1.0
    assert top.offset == 0
    assert top.hasType == "cryd:glimpse"
    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-head")
    assert md5_child.value == "d41d8cd98f00b204e9800998ecf8427e"  # pragma: allowlist secret
    assert md5_child.coverage == 1.0


def test_glimpse_small_file_full_coverage(tmp_path):
    data = b"x" * 100  # 100 bytes < 2048
    (tmp_path / "small.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-head")
    assert md5_child.coverage == 1.0
    assert md5_child.value == hashlib.md5(data).hexdigest()


def test_glimpse_large_file_partial_coverage(tmp_path):
    data = b"x" * 4096  # 4 KB > 2048
    (tmp_path / "large.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-head")
    assert md5_child.coverage == pytest.approx(2048 / 4096)
    assert top.coverage == pytest.approx(2048 / 4096)
    assert md5_child.value == hashlib.md5(data[:2048]).hexdigest()


def test_glimpse_filename_is_basename_only(tmp_path):
    subdir = tmp_path / "deep" / "nested"
    subdir.mkdir(parents=True)
    (subdir / "output.csv").write_bytes(b"data")
    source = LocalSource()
    file_obj = next(f for f in source.list_files(str(tmp_path)) if f.basename == "output.csv")

    _, children = build_file_descriptor(file_obj, Glimpse(), source)

    fname_child = next(c for c in children if c.hasType == "cryd:desc-type/filename")
    assert fname_child.value == "output.csv"
    assert "/" not in fname_child.value


def test_glimpse_meta_has_no_md5_child(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    _, children = build_file_descriptor(file_obj, GlimpseMeta(), source)

    assert not any(c.hasType == "cryd:desc-type/md5-head" for c in children)


def test_glimpse_light_has_no_filename_child(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    _, children = build_file_descriptor(file_obj, GlimpseLight(), source)

    assert not any(c.hasType == "cryd:desc-type/filename" for c in children)


def test_all_variants_top_value_starts_with_v0(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    for method in [Glimpse(), GlimpseSlim(), GlimpseLight(), GlimpseMeta()]:
        top, _ = build_file_descriptor(file_obj, method, source)
        assert top.value.startswith("v0:"), f"{method.id} top value missing v0: prefix"


def test_composite_hash_is_deterministic(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello world")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top1, _ = build_file_descriptor(file_obj, Glimpse(), source)
    top2, _ = build_file_descriptor(file_obj, Glimpse(), source)

    assert top1.value == top2.value
    assert top1.id == top2.id


def test_composite_hash_differs_for_different_content(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"content A")
    (tmp_path / "b.txt").write_bytes(b"content B")
    source = LocalSource()
    files = {f.basename: f for f in source.list_files(str(tmp_path))}

    top_a, _ = build_file_descriptor(files["a.txt"], Glimpse(), source)
    top_b, _ = build_file_descriptor(files["b.txt"], Glimpse(), source)

    assert top_a.value != top_b.value


def test_child_count_matches_variant_fields(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    for method, expected_count in [
        (Glimpse(), 5),  # filename, size, md5, ctime, mtime
        (GlimpseSlim(), 4),  # filename, size, mtime, md5
        (GlimpseLight(), 3),  # size, md5, mtime
        (GlimpseMeta(), 3),  # filename, size, mtime
    ]:
        _, children = build_file_descriptor(file_obj, method, source)
        assert len(children) == expected_count, f"{method.id} expected {expected_count} children"


def test_top_descriptor_references_all_child_ids(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    assert set(top.hasDescriptor) == {c.id for c in children}


# --- S3 tests ---


@patch("crystalia_collector.source.s3.boto3")
def test_glimpse_s3_sends_correct_byte_range(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"first 2k"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    file_obj = FileObject(
        uri="s3://bucket/data/output.csv",
        basename="output.csv",
        size=10000,
        mtime=_NOW,
    )

    top, _ = build_file_descriptor(file_obj, Glimpse(), S3Source())

    mock_client.get_object.assert_called_once_with(
        Bucket="bucket",
        Key="data/output.csv",
        Range="bytes=0-2047",
    )
    assert top.value.startswith("v0:")


@patch("crystalia_collector.source.s3.boto3")
def test_glimpse_meta_s3_no_checksum_call(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    from crystalia_collector.source.s3 import S3Source

    file_obj = FileObject(
        uri="s3://bucket/data/output.csv",
        basename="output.csv",
        size=5000,
        mtime=_NOW,
    )

    build_file_descriptor(file_obj, GlimpseMeta(), S3Source())

    mock_client.get_object.assert_not_called()


@patch("crystalia_collector.source.s3.boto3")
def test_glimpse_s3_ctime_absent_uses_empty_string(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"data"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    file_obj = FileObject(
        uri="s3://bucket/data/file.txt",
        basename="file.txt",
        size=100,
        mtime=_NOW,
        ctime=None,
    )

    _, children = build_file_descriptor(file_obj, Glimpse(), S3Source())

    ctime_child = next(c for c in children if c.hasType == "cryd:desc-type/ctime")
    assert ctime_child.value == ""
