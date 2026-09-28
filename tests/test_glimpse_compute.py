import hashlib
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from crystalia_collector.glimpse_compute import build_file_descriptor
from crystalia_collector.method.glimpse import Glimpse, GlimpseLight, GlimpseMeta, GlimpseSlim
from crystalia_collector.source import FileObject
from crystalia_collector.source.local import LocalSource
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.errors import InvalidDescriptor
from crystalia_data_model.types.leaves import (
    mint_glimpse,
    mint_glimpse_light,
    mint_glimpse_meta,
    mint_glimpse_slim,
    mint_md5_region,
)
from crystalia_data_model.types.validate import ensure_valid

_NOW = datetime(2024, 6, 1, tzinfo=UTC)


# --- DM-minted IRI equivalence ---


def test_glimpse_top_iri_equals_dm_mint(tmp_path):
    data = b"hello"
    (tmp_path / "file.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse(
        filename=by_type["cryd:desc-type/filename"],
        file_size=by_type["cryd:desc-type/file-size"],
        head=by_type["cryd:desc-type/md5-region"],
        ctime=by_type["cryd:desc-type/ctime"],
        mtime=by_type["cryd:desc-type/mtime"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_child_leaves_equal_dm_leaf_mint(tmp_path):
    data = b"x" * 100
    (tmp_path / "small.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    _, children = build_file_descriptor(file_obj, Glimpse(), source)

    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-region")
    expected = mint_md5_region(0, 100, hashlib.md5(data).hexdigest())
    assert md5_child.id == expected.id
    assert md5_child.value == expected.value


def test_glimpse_slim_top_iri_equals_dm_mint(tmp_path):
    data = b"slim"
    (tmp_path / "file.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, GlimpseSlim(), source)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_slim(
        filename=by_type["cryd:desc-type/filename"],
        file_size=by_type["cryd:desc-type/file-size"],
        mtime=by_type["cryd:desc-type/mtime"],
        head=by_type["cryd:desc-type/md5-region"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_light_top_iri_equals_dm_mint(tmp_path):
    data = b"light"
    (tmp_path / "file.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, GlimpseLight(), source)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_light(
        file_size=by_type["cryd:desc-type/file-size"],
        head=by_type["cryd:desc-type/md5-region"],
        mtime=by_type["cryd:desc-type/mtime"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_meta_top_iri_equals_dm_mint(tmp_path):
    data = b"meta"
    (tmp_path / "file.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, GlimpseMeta(), source)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_meta(
        filename=by_type["cryd:desc-type/filename"],
        file_size=by_type["cryd:desc-type/file-size"],
        mtime=by_type["cryd:desc-type/mtime"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_variants_reject_wrong_role_head_with_resolve():
    """Every glimpse* variant's head role must resolve to md5-region, not md5."""
    from crystalia_data_model.types.leaves import mint_ctime, mint_file_size, mint_filename, mint_md5, mint_mtime

    filename = mint_filename("bad.txt")
    file_size = mint_file_size(10)
    ctime = mint_ctime("2024-01-01T00:00:00")
    mtime = mint_mtime("2024-01-01T00:00:00")
    wrong_head = mint_md5("deadbeef", length=10)

    for top, all_children in (
        (
            mint_glimpse(filename=filename, file_size=file_size, head=wrong_head, ctime=ctime, mtime=mtime),
            [filename, file_size, ctime, mtime, wrong_head],
        ),
        (
            mint_glimpse_slim(filename=filename, file_size=file_size, mtime=mtime, head=wrong_head),
            [filename, file_size, mtime, wrong_head],
        ),
        (
            mint_glimpse_light(file_size=file_size, head=wrong_head, mtime=mtime),
            [file_size, mtime, wrong_head],
        ),
    ):
        by_id = {str(d.id): d for d in [top, *all_children]}
        with pytest.raises(InvalidDescriptor):
            ensure_valid(top, resolve=by_id.__getitem__)


# --- head leaf shape (md5-region: offset/length are part of its identity) ---


def test_glimpse_zero_byte_file(tmp_path):
    (tmp_path / "empty.txt").write_bytes(b"")
    source = LocalSource()
    file_obj = next(f for f in source.list_files(str(tmp_path)) if f.basename == "empty.txt")

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    assert top.offset is None
    assert top.hasType == "cryd:desc-type/glimpse"
    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-region")
    assert md5_child.value == "d41d8cd98f00b204e9800998ecf8427e"  # pragma: allowlist secret
    assert md5_child.length == 0
    assert md5_child.offset == 0


def test_glimpse_small_file_full_coverage(tmp_path):
    data = b"x" * 100  # 100 bytes < 2048
    (tmp_path / "small.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-region")
    assert md5_child.length == 100
    assert md5_child.offset == 0
    assert md5_child.value == hashlib.md5(data).hexdigest()


def test_glimpse_large_file_partial_coverage(tmp_path):
    data = b"x" * 4096  # 4 KB > 2048
    (tmp_path / "large.txt").write_bytes(data)
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    top, children = build_file_descriptor(file_obj, Glimpse(), source)

    md5_child = next(c for c in children if c.hasType == "cryd:desc-type/md5-region")
    assert md5_child.length == 2048
    assert md5_child.offset == 0
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

    assert not any(c.hasType == "cryd:desc-type/md5-region" for c in children)


def test_glimpse_light_has_no_filename_child(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    _, children = build_file_descriptor(file_obj, GlimpseLight(), source)

    assert not any(c.hasType == "cryd:desc-type/filename" for c in children)


def test_all_variants_mint_a_valid_top(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"hello")
    source = LocalSource()
    file_obj = list(source.list_files(str(tmp_path)))[0]

    for method in [Glimpse(), GlimpseSlim(), GlimpseLight(), GlimpseMeta()]:
        top, _ = build_file_descriptor(file_obj, method, source)
        assert ensure_valid(top) is top, f"{method.id} top failed ensure_valid"


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


# --- single write point: ensure_valid rejects a hand-built wrong-IRI descriptor ---


def test_ensure_valid_rejects_wrong_iri_descriptor():
    bad = Descriptor(id="cryd:00000000000000000000000000000000", hasType="cryd:desc-type/filename", value="x")
    with pytest.raises(InvalidDescriptor):
        ensure_valid(bad)


def test_combine_descriptors_rejects_wrong_iri_descriptor(tmp_path):
    from crystalia_collector.work import combine_descriptors
    from crystalia_data_model.datamodel.linkml_crystalia import Item

    bad = Descriptor(id="cryd:00000000000000000000000000000000", hasType="cryd:desc-type/filename", value="x")
    item = Item(id="crys:test", label="test", hasDescriptor=[bad.id])
    with pytest.raises(InvalidDescriptor):
        combine_descriptors([item], tmp_path / "out.ttl", "turtle", descriptors=[bad])


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
    assert ensure_valid(top) is top


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


def test_glimpse_compute_has_no_local_iri_minting():
    """glimpse_compute.py mints only via the DM; no collector-local hashlib-based IRI helper remains."""
    import inspect

    import crystalia_collector.glimpse_compute as mod

    source = inspect.getsource(mod)
    assert "_content_id" not in source
    assert "_composite_v0" not in source
    assert "_descriptor_id" not in source
