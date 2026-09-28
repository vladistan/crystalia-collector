from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from crystalia_collector.glimpse_scanner import scan_files, scan_with_dirs
from crystalia_collector.method.glimpse import Glimpse, GlimpseContent, GlimpseMeta
from crystalia_collector.method.glimpse_dir import GlimpseDir, GlimpseDirContent
from crystalia_collector.source.local import LocalSource
from crystalia_data_model.types.validate import ensure_valid

_NOW = datetime(2024, 6, 1, tzinfo=UTC)


def test_scan_files_flat_directory(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"hello")
    (tmp_path / "b.txt").write_bytes(b"world")

    results = scan_files(str(tmp_path), LocalSource(), Glimpse())

    assert len(results) == 2
    assert {r[0].basename for r in results} == {"a.txt", "b.txt"}


def test_scan_files_empty_directory(tmp_path):
    assert scan_files(str(tmp_path), LocalSource(), Glimpse()) == []


def test_scan_files_all_descriptors_have_v0_prefix(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"content")

    results = scan_files(str(tmp_path), LocalSource(), Glimpse())

    assert all(ensure_valid(r[1]) is r[1] for r in results)


def test_scan_with_dirs_produces_dir_descriptor(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"content")

    _, dir_results = scan_with_dirs(str(tmp_path), LocalSource(), Glimpse(), GlimpseDir())

    assert len(dir_results) >= 1


def test_scan_with_dirs_nested(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (tmp_path / "top.txt").write_bytes(b"top")
    (subdir / "nested.txt").write_bytes(b"nested")

    file_results, dir_results = scan_with_dirs(
        str(tmp_path),
        LocalSource(),
        Glimpse(),
        GlimpseDir(),
    )

    assert len(file_results) == 2
    dir_uris = [r[0] for r in dir_results]
    assert str(subdir) in dir_uris
    assert str(tmp_path) in dir_uris


def test_scan_with_dirs_empty_directory(tmp_path):
    file_results, dir_results = scan_with_dirs(
        str(tmp_path),
        LocalSource(),
        Glimpse(),
        GlimpseDir(),
    )

    assert file_results == []
    assert dir_results == []


def test_scan_with_dirs_dir_descriptor_v0_prefix(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"content")

    _, dir_results = scan_with_dirs(str(tmp_path), LocalSource(), Glimpse(), GlimpseDir())

    assert all(ensure_valid(r[1]) is r[1] for r in dir_results)


@patch("crystalia_collector.source.s3.boto3")
def test_scan_files_s3(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "prefix/a.txt", "Size": 100, "LastModified": _NOW, "ETag": "e1"},
            {"Key": "prefix/b.txt", "Size": 200, "LastModified": _NOW, "ETag": "e2"},
        ],
        "IsTruncated": False,
    }
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"data"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    results = scan_files("s3://bucket/prefix/", S3Source(), Glimpse())

    assert len(results) == 2
    assert all(ensure_valid(r[1]) is r[1] for r in results)


# --- declared child-method relation (Phase 6, Step 6.1) ---


def test_dir_method_declaring_child_method_receives_its_top_descriptors_as_rollup_children(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")

    dir_method = GlimpseDirContent()
    assert dir_method.paired_file_method_id == GlimpseContent().id

    file_results, dir_results = scan_with_dirs(str(tmp_path), LocalSource(), GlimpseContent(), dir_method)

    file_top_ids = {top.id for (_, top, _) in file_results}
    dir_top = next(r[1] for r in dir_results if r[0] == str(tmp_path))
    # glimpse-dir-content has no own-field children; the rollup is over the file tops directly
    assert set(dir_top.hasDescriptor) == file_top_ids


def test_legacy_glimpse_dir_pairing_unchanged_by_content_addition(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")

    assert GlimpseDir().paired_file_method_id == Glimpse().id

    _, dir_results = scan_with_dirs(str(tmp_path), LocalSource(), Glimpse(), GlimpseDir())

    assert all(ensure_valid(r[1]) is r[1] for r in dir_results)


@patch("crystalia_collector.source.s3.boto3")
def test_scan_files_s3_meta_no_s3_calls_for_checksum(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "prefix/file.txt", "Size": 500, "LastModified": _NOW, "ETag": "etag"},
        ],
        "IsTruncated": False,
    }

    from crystalia_collector.source.s3 import S3Source

    scan_files("s3://bucket/prefix/", S3Source(), GlimpseMeta())

    mock_client.get_object.assert_not_called()
