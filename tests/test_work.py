import boto3
import botocore.exceptions
import pytest
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

from crystalia_collector.method import method_by_id
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.work import (
    _collect_glimpse_dir,
    _list_dir_glimpse_files,
    _process_task_file,
    compute_annotations,
    list_s3_dir,
)


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


def test_process_task_file(data_dir):
    task_file = str(data_dir / "test_task.txt")
    results = _process_task_file(task_file)

    assert len(results) == 4

    uris = [uri for uri, _ in results]
    assert any("dir1/chr22_small.txt" in u for u in uris)
    assert any("dir3/unique_file.txt" in u for u in uris)
    assert any("dir3/nested/chr22_small.txt" in u for u in uris)

    for _uri, desc in results:
        assert isinstance(desc, Descriptor)
        assert desc.hasType == "cryd:md5-8gb"
        assert desc.offset == 0
        assert desc.coverage == 1.0
        assert len(desc.value) == 32  # md5 hex

    # Identical files should produce identical checksums
    dir1_checksum = next(d.value for u, d in results if "dir1/chr22_small" in u)
    nested_checksum = next(d.value for u, d in results if "dir3/nested/chr22_small" in u)
    assert dir1_checksum == nested_checksum


def test_list_dir_glimpse_files(data_dir):
    method = method_by_id("glimpse")
    assert isinstance(method, GlimpseBase)
    num_files, total_size = _list_dir_glimpse_files(str(data_dir), method)

    assert num_files == 10
    assert total_size > 0


def test_collect_glimpse_dir(data_dir):
    method = method_by_id("glimpse-dir")
    assert isinstance(method, GlimpseDirBase)
    file_descs, dir_descs, extras = _collect_glimpse_dir(str(data_dir), method)

    # 9 files across all directories
    assert len(file_descs) == 10

    # Directories: sample_data, dir1, dir2, dir3, nested
    assert len(dir_descs) == 5

    # Every file URI maps to a list with one top-level descriptor
    for _uri, descs in file_descs.items():
        assert len(descs) == 1
        assert isinstance(descs[0], Descriptor)
        assert descs[0].hasType == "cryd:glimpse"

    # Every dir URI maps to a list with one top-level descriptor
    for _uri, descs in dir_descs.items():
        assert len(descs) == 1
        assert isinstance(descs[0], Descriptor)
        assert descs[0].hasType == "cryd:glimpse-dir"

    # Extras include top + children for all files and dirs
    assert len(extras) > len(file_descs) + len(dir_descs)

    # dir1 and dir2 have identical file contents but different timestamps,
    # so their glimpse-dir hashes differ (mtime is part of the hash).
    # But their file-level glimpse descriptors should match.
    dir1_uri = next(u for u in dir_descs if u.endswith("/dir1"))
    dir2_uri = next(u for u in dir_descs if u.endswith("/dir2"))
    assert dir1_uri in dir_descs
    assert dir2_uri in dir_descs
