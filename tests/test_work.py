import boto3
import botocore.exceptions
import pytest

from crystalia_collector.method import method_by_id
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.work import (
    _TYPE_RELPATH,
    _build_directory_items,
    _build_file_items,
    _collect_glimpse_dir,
    _default_item_id,
    _list_dir_glimpse_files,
    _process_task_file,
    _relative_path,
    compute_annotations,
    list_s3_dir,
)
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.leaves import mint_md5


def test_default_item_id_uses_cryd_namespace():
    # cryd: is instance-data-only (DM v2.1.0 namespace split); crys: is reserved
    # for type/schema CURIEs (crys:dtype/<name>).
    assert _default_item_id().startswith("cryd:")


def test_relative_path_nested_root_and_fallback():
    assert _relative_path("/data/scan/dir1/.DS_Store", "/data/scan") == "dir1/.DS_Store"
    assert _relative_path("/data/scan/file.txt", "/data/scan") == "file.txt"
    # trailing slash on root is tolerated
    assert _relative_path("/data/scan/dir1/f", "/data/scan/") == "dir1/f"
    # uri not under root -> basename fallback
    assert _relative_path("/elsewhere/f", "/data/scan") == "f"


def test_build_file_items_emits_distinct_relpath_for_same_basename():
    # Two distinct files sharing a basename in different directories (the .DS_Store case)
    d1 = Descriptor(id="cryd:c1", hasType="cryd:md5-head", value="aaa")
    d2 = Descriptor(id="cryd:c2", hasType="cryd:md5-head", value="bbb")
    merged = {
        "/scan/dir1/.DS_Store": [d1],
        "/scan/dir2/.DS_Store": [d2],
    }

    items, relpaths = _build_file_items(merged, {}, "/scan", _default_item_id)

    # A relpath descriptor per file, each carrying the distinct relative path
    assert sorted(d.value for d in relpaths) == ["dir1/.DS_Store", "dir2/.DS_Store"]
    assert all(d.hasType == _TYPE_RELPATH for d in relpaths)
    # Distinct content-addressed IDs (paths differ -> IDs differ)
    assert len({d.id for d in relpaths}) == 2
    # Each Item references exactly one of the relpath descriptors
    relpath_ids = {d.id for d in relpaths}
    for item in items:
        assert len(set(item.hasDescriptor) & relpath_ids) == 1


def test_build_directory_items_nested_dirs_have_one_root():
    # A nested tree: /scan (root), /scan/sub, /scan/sub/deep.
    d_root = Descriptor(id="cryd:dr", hasType="crys:dtype/glimpse-dir", value="root")
    d_sub = Descriptor(id="cryd:ds", hasType="crys:dtype/glimpse-dir", value="sub")
    d_deep = Descriptor(id="cryd:dd", hasType="crys:dtype/glimpse-dir", value="deep")
    merged = {
        "/scan": [d_root],
        "/scan/sub": [d_sub],
        "/scan/sub/deep": [d_deep],
    }

    items, dir_item_ids, relpaths = _build_directory_items(merged, _default_item_id, "/scan")

    # Exactly one directory Item has no isPartOf: the scan root.
    roots = [item for item in items if item.isPartOf is None]
    assert len(roots) == 1
    root_item = roots[0]
    assert dir_item_ids["/scan"] == root_item.id

    # Each non-root dir's isPartOf points at its own parent's item_id, not the root's.
    sub_item = next(i for i in items if i.id == dir_item_ids["/scan/sub"])
    deep_item = next(i for i in items if i.id == dir_item_ids["/scan/sub/deep"])
    assert sub_item.isPartOf == dir_item_ids["/scan"]
    assert deep_item.isPartOf == dir_item_ids["/scan/sub"]

    # Every dir Item carries a relpath descriptor, same as file Items do.
    assert len(relpaths) == 3
    assert all(d.hasType == _TYPE_RELPATH for d in relpaths)
    relpath_ids = {d.id for d in relpaths}
    for item in items:
        assert len(set(item.hasDescriptor) & relpath_ids) == 1


def _has_aws_credentials() -> bool:
    try:
        boto3.client("sts").get_caller_identity()
    except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
        return False
    return True


requires_s3 = pytest.mark.skipif(
    not _has_aws_credentials(),
    reason="AWS credentials not available",
)


@requires_s3
def test_list_s3_dir(s3_bucket, s3_prefix, work_dir):
    n_files, total_size = list_s3_dir(
        f"{s3_bucket}/{s3_prefix}202-samples-cohort/3202_samples_cohort_gg_chr2",
        "md5-8gb",
        work_dir,
    )

    assert n_files == 8
    assert total_size == 328226892212


@requires_s3
def test_annotate(data_dir, work_dir):
    task_file = data_dir / "chr22_small.txt"
    output_file = work_dir / "out.rdf"

    compute_annotations(output_file, task_file)


def test_process_task_file(data_dir, tmp_path):
    # Build the task file at runtime from real sample files so absolute paths
    # are correct on any machine (the old static fixture hardcoded /home/vlad).
    files = [
        data_dir / "dir1" / "chr22_small.txt",
        data_dir / "dir1" / "short_file_single_descriptor.ttl",
        data_dir / "dir3" / "unique_file.txt",
        data_dir / "dir3" / "nested" / "chr22_small.txt",
    ]
    task_file = tmp_path / "task.txt"
    task_file.write_text(
        "".join(f"{f} {f.stat().st_size} md5-8gb 8589934592 0\n" for f in files),
    )
    results = _process_task_file(str(task_file))

    assert len(results) == 4

    uris = [uri for uri, _ in results]
    assert any("dir1/chr22_small.txt" in u for u in uris)
    assert any("dir3/unique_file.txt" in u for u in uris)
    assert any("dir3/nested/chr22_small.txt" in u for u in uris)

    for _uri, desc in results:
        assert isinstance(desc, Descriptor)
        assert desc.hasType == "crys:dtype/md5-region"
        assert desc.offset == 0
        assert len(desc.value) == 32  # md5 hex

    # Identical files should produce identical checksums
    dir1_checksum = next(d.value for u, d in results if "dir1/chr22_small" in u)
    nested_checksum = next(d.value for u, d in results if "dir3/nested/chr22_small" in u)
    assert dir1_checksum == nested_checksum


def test_process_task_file_whole_file_md5_via_dm(data_dir, tmp_path):
    f = data_dir / "dir1" / "chr22_small.txt"
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{f} {f.stat().st_size} md5 0 0\n")

    ((uri, desc),) = _process_task_file(str(task_file))

    assert desc.hasType == "crys:dtype/md5"
    assert desc.offset is None
    assert desc.length == f.stat().st_size
    expected = mint_md5(desc.value, length=f.stat().st_size)
    assert desc.id == expected.id


def test_process_task_file_filename_with_spaces(tmp_path):
    # Real-world filenames (invoices, exports) routinely contain spaces, e.g.
    # "Project_ BCG-Micro (BM)_2019-06-01_2019-06-30.xlsx". A naive
    # line.split() misaligns the trailing numeric fields.
    src = tmp_path / "Project_ BCG-Micro (BM)_2019-06-01_2019-06-30.xlsx"
    src.write_bytes(b"content")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{src} {src.stat().st_size} md5 0 0\n")

    ((uri, desc),) = _process_task_file(str(task_file))

    assert uri == str(src)
    assert desc.hasType == "crys:dtype/md5"
    assert desc.length == src.stat().st_size


def test_list_dir_glimpse_files(data_dir):
    method = method_by_id("glimpse")
    assert isinstance(method, GlimpseBase)
    num_files, total_size = _list_dir_glimpse_files(str(data_dir), method)

    assert num_files == 9
    assert total_size > 0


def test_collect_glimpse_dir(data_dir):
    method = method_by_id("glimpse-dir")
    assert isinstance(method, GlimpseDirBase)
    file_descs, dir_descs, extras = _collect_glimpse_dir(str(data_dir), method)

    # 9 files across all directories
    assert len(file_descs) == 9

    # Directories: sample_data, dir1, dir2, dir3, nested
    assert len(dir_descs) == 5

    # Every file URI maps to a list with one top-level descriptor
    for _uri, descs in file_descs.items():
        assert len(descs) == 1
        assert isinstance(descs[0], Descriptor)
        assert descs[0].hasType == "crys:dtype/glimpse"

    # Every dir URI maps to a list with one top-level descriptor
    for _uri, descs in dir_descs.items():
        assert len(descs) == 1
        assert isinstance(descs[0], Descriptor)
        assert descs[0].hasType == "crys:dtype/glimpse-dir"

    # Extras include top + children for all files and dirs
    assert len(extras) > len(file_descs) + len(dir_descs)

    # dir1 and dir2 have identical file contents but different timestamps,
    # so their glimpse-dir hashes differ (mtime is part of the hash).
    # But their file-level glimpse descriptors should match.
    dir1_uri = next(u for u in dir_descs if u.endswith("/dir1"))
    dir2_uri = next(u for u in dir_descs if u.endswith("/dir2"))
    assert dir1_uri in dir_descs
    assert dir2_uri in dir_descs
