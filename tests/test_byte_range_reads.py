"""Byte-range reads on both sources (Phase 7, Step 7.1): head/tail/range, never the whole object."""

from unittest.mock import MagicMock, patch

from crystalia_collector.source.local import LocalSource


def test_local_read_range_returns_exact_bytes(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"0123456789")
    source = LocalSource()

    assert source.read_range(str(tmp_path / "f.bin"), 2, 4) == b"2345"


def test_local_read_head_returns_first_n_bytes(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"0123456789")
    source = LocalSource()

    assert source.read_head(str(tmp_path / "f.bin"), 3) == b"012"


def test_local_read_tail_returns_last_n_bytes(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"0123456789")
    source = LocalSource()

    assert source.read_tail(str(tmp_path / "f.bin"), 3) == b"789"


def test_local_read_head_shorter_than_n_returns_whole_file(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"abc")
    source = LocalSource()

    assert source.read_head(str(tmp_path / "f.bin"), 100) == b"abc"


def test_local_read_tail_shorter_than_n_returns_whole_file(tmp_path):
    (tmp_path / "f.bin").write_bytes(b"abc")
    source = LocalSource()

    assert source.read_tail(str(tmp_path / "f.bin"), 100) == b"abc"


@patch("crystalia_collector.source.s3.boto3")
def test_s3_read_tail_uses_ranged_get_with_suffix_range(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"tail bytes"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    result = S3Source().read_tail("s3://bucket/key.bin", 16384)

    mock_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.bin", Range="bytes=-16384")
    assert result == b"tail bytes"


@patch("crystalia_collector.source.s3.boto3")
def test_s3_read_head_uses_ranged_get(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"head bytes"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    result = S3Source().read_head("s3://bucket/key.bin", 16384)

    mock_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.bin", Range="bytes=0-16383")
    assert result == b"head bytes"


@patch("crystalia_collector.source.s3.boto3")
def test_s3_read_range_uses_ranged_get(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = [b"mid"]
    mock_client.get_object.return_value = {"Body": mock_body}

    from crystalia_collector.source.s3 import S3Source

    result = S3Source().read_range("s3://bucket/key.bin", 100, 3)

    mock_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.bin", Range="bytes=100-102")
    assert result == b"mid"
