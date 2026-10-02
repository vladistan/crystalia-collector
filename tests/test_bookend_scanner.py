"""bookend-dir rollup (Phase 7, Step 7.6): mixed dir, strong iff every child strong."""

import zipfile

from crystalia_collector.bookend_scanner import scan_bookend_dirs
from crystalia_collector.source.local import LocalSource
from crystalia_data_model.types.registry import is_strong
from crystalia_data_model.types.validate import ensure_valid


def test_all_small_files_dir_is_strong(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x" * 10)
    (tmp_path / "b.txt").write_bytes(b"y" * 10)
    source = LocalSource()

    _, dir_results = scan_bookend_dirs(str(tmp_path), source)

    top = next(r[1] for r in dir_results if r[0] == str(tmp_path))
    assert top.hasType == "crys:dtype/bookend-dir-strong"
    assert is_strong(top) is True
    assert ensure_valid(top) is top


def test_one_weak_child_makes_dir_weak(tmp_path):
    (tmp_path / "small.txt").write_bytes(b"x" * 10)
    jpeg_magic = b"\xff\xd8\xff" + b"\x00" * 40000
    (tmp_path / "big.jpg").write_bytes(jpeg_magic)
    source = LocalSource()

    _, dir_results = scan_bookend_dirs(str(tmp_path), source)

    top = next(r[1] for r in dir_results if r[0] == str(tmp_path))
    assert top.hasType == "crys:dtype/bookend-dir-weak"


def test_zip_child_contributes_zip_manifest_not_bookend(tmp_path):
    with zipfile.ZipFile(tmp_path / "a.zip", "w") as zf:
        zf.writestr("m.txt", "hello")
    source = LocalSource()

    file_results, dir_results = scan_bookend_dirs(str(tmp_path), source)

    _, _bookend_top, _bookend_children, manifest = next(r for r in file_results if r[0].basename == "a.zip")
    assert manifest is not None

    dir_top = next(r[1] for r in dir_results if r[0] == str(tmp_path))
    assert manifest.id in dir_top.hasDescriptor


def test_empty_directory_tree_yields_no_dir_descriptor(tmp_path):
    (tmp_path / "sub").mkdir()
    source = LocalSource()

    file_results, dir_results = scan_bookend_dirs(str(tmp_path), source)

    # Directories are discovered via the files inside them (bottom-up scan design,
    # shared with glimpse_scanner) — a file-less directory is never visited.
    assert file_results == []
    assert dir_results == []


def test_nested_subdir_rollup_contributes_bookend_dir(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "f.txt").write_bytes(b"x" * 10)
    source = LocalSource()

    file_results, dir_results = scan_bookend_dirs(str(tmp_path), source)

    sub_top = next(r[1] for r in dir_results if r[0] == str(sub))
    parent_top = next(r[1] for r in dir_results if r[0] == str(tmp_path))
    assert sub_top.id in parent_top.hasDescriptor
