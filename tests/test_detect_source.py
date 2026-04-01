import pytest

from crystalia_collector.source import detect_source
from crystalia_collector.source.local import LocalSource
from crystalia_collector.source.s3 import S3Source
from crystalia_collector.work import list_dir


def test_detect_source_returns_s3_source_for_s3_uri():
    source = detect_source("s3://my-bucket/some/prefix")
    assert isinstance(source, S3Source)


def test_detect_source_returns_local_source_for_absolute_path():
    source = detect_source("/abs/local/path")
    assert isinstance(source, LocalSource)


def test_detect_source_raises_for_relative_path():
    with pytest.raises(ValueError, match="relative paths not supported"):
        detect_source("relative/path")


def test_list_dir_local_creates_task_file_with_absolute_paths(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "file1.txt").write_bytes(b"hello world")

    task_dir = tmp_path / "tasks"
    num_files, total_size = list_dir(str(data_dir), "md5", task_dir)

    assert num_files == 1
    assert total_size == 11

    task_files = sorted(task_dir.iterdir())
    assert len(task_files) >= 1
    content = task_files[0].read_text()
    assert "s3://" not in content
    assert str((data_dir / "file1.txt").resolve()) in content


def test_list_dir_basenames_have_no_path_separators(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "report.csv").write_bytes(b"x,y\n1,2\n")

    task_dir = tmp_path / "tasks"
    list_dir(str(tmp_path), "md5", task_dir)

    content = sorted(task_dir.iterdir())[0].read_text().strip()
    uri = content.split()[0]
    basename = uri.rsplit("/", 1)[-1]
    assert basename == "report.csv"
    assert "/" not in basename
