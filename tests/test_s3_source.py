"""Tests for S3Source and the s3_iface facade compatibility layer."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

from crystalia_collector.source import FileObject
from crystalia_collector.source.s3 import S3Source

_NOW = datetime(2024, 1, 1, tzinfo=UTC)


def _s3_response(objects: list[dict[str, str | int | datetime]], is_truncated: bool = False, next_token: str | None = None) -> dict[str, Any]:
    response = {"Contents": objects, "IsTruncated": is_truncated}
    if next_token:
        response["NextContinuationToken"] = next_token
    return response


def test_parse_s3_uri_bucket_and_key():
    assert S3Source.parse_s3_uri("s3://my-bucket/some/prefix") == ("my-bucket", "some/prefix")


def test_parse_s3_uri_bucket_only():
    assert S3Source.parse_s3_uri("s3://my-bucket/") == ("my-bucket", "")


@patch("crystalia_collector.source.s3.boto3")
def test_list_files_yields_file_objects(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.return_value = _s3_response(
        [
            {"Key": "prefix/file1.txt", "Size": 100, "LastModified": _NOW, "ETag": "etag1"},
            {"Key": "prefix/file2.txt", "Size": 200, "LastModified": _NOW, "ETag": "etag2"},
        ],
    )

    files = list(S3Source().list_files("s3://bucket/prefix/"))

    assert len(files) == 2
    assert all(isinstance(f, FileObject) for f in files)
    assert files[0].uri == "s3://bucket/prefix/file1.txt"
    assert files[0].basename == "file1.txt"
    assert files[0].size == 100
    assert files[0].mtime == _NOW
    assert files[0].etag == "etag1"
    assert files[0].ctime is None


@patch("crystalia_collector.source.s3.boto3")
def test_list_files_handles_pagination(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.side_effect = [
        _s3_response(
            [{"Key": "p/a.txt", "Size": 1, "LastModified": _NOW, "ETag": "e1"}],
            is_truncated=True,
            next_token="token-1",
        ),
        _s3_response(
            [{"Key": "p/b.txt", "Size": 2, "LastModified": _NOW, "ETag": "e2"}],
        ),
    ]

    files = list(S3Source().list_files("s3://bkt/p/"))

    assert len(files) == 2
    assert files[0].basename == "a.txt"
    assert files[1].basename == "b.txt"


@patch("crystalia_collector.source.s3.boto3")
def test_list_files_empty_prefix(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.return_value = {"Contents": [], "IsTruncated": False}

    files = list(S3Source().list_files("s3://bucket/"))

    assert files == []


@patch("crystalia_collector.source.s3.boto3")
def test_compute_checksum_with_length(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"hello"]
    mock_client.get_object.return_value = {"Body": mock_body}

    result = S3Source().compute_checksum("s3://bucket/key.txt", 0, 1024)

    assert isinstance(result, str)
    assert len(result) == 32
    mock_client.get_object.assert_called_once_with(
        Bucket="bucket",
        Key="key.txt",
        Range="bytes=0-1023",
    )


@patch("crystalia_collector.source.s3.boto3")
def test_compute_checksum_no_length(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"data"]
    mock_client.get_object.return_value = {"Body": mock_body}

    S3Source().compute_checksum("s3://bucket/key.txt", 100, None)

    mock_client.get_object.assert_called_once_with(
        Bucket="bucket",
        Key="key.txt",
        Range="bytes=100-",
    )


@patch("crystalia_collector.source.s3.boto3")
def test_facade_list_files_in_s3_prefix(mock_boto3):
    # Imported here to test the facade's re-export surface from the caller's perspective
    from crystalia_collector.s3_iface import S3Object, list_files_in_s3_prefix

    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_objects_v2.return_value = _s3_response(
        [
            {"Key": "prefix/file.txt", "Size": 100, "LastModified": _NOW, "ETag": "etag1"},
        ],
    )

    files = list(list_files_in_s3_prefix("bucket", "prefix/"))

    assert len(files) == 1
    assert isinstance(files[0], S3Object)
    assert files[0].key == "prefix/file.txt"
    assert files[0].size == 100
    assert files[0].last_modified == _NOW
    assert files[0].etag == "etag1"


@patch("crystalia_collector.source.s3.boto3")
def test_facade_compute_s3_checksum(mock_boto3):
    # Imported here to test the facade's re-export surface from the caller's perspective
    from crystalia_collector.s3_iface import compute_s3_checksum

    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"test"]
    mock_client.get_object.return_value = {"Body": mock_body}

    result = compute_s3_checksum("bucket", "key.txt", 0, 1024)

    assert isinstance(result, str)
    assert len(result) == 32
