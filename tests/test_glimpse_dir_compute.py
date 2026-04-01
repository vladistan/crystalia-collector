from datetime import UTC, datetime

from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

from crystalia_collector.glimpse_dir_compute import build_dir_descriptor
from crystalia_collector.method.glimpse_dir import (
    GlimpseDir,
    GlimpseDirLight,
    GlimpseDirMeta,
    GlimpseDirSlim,
)

_NOW = datetime(2024, 6, 1, tzinfo=UTC)


def _fake_desc(value_suffix: str) -> Descriptor:
    return Descriptor(
        id=f"cryd:{value_suffix}",
        hasType="cryd:glimpse",
        value=f"v0:{value_suffix}",
        offset=0,
        coverage=1.0,
    )


def test_glimpse_dir_empty_directory():
    top, children = build_dir_descriptor("results", _NOW, GlimpseDir(), [])

    count_child = next(c for c in children if c.hasType == "cryd:desc-type/count")
    assert count_child.value == "0"
    assert top.value.startswith("v0:")


def test_glimpse_dir_count_reflects_children():
    child_descs = [
        ("a.txt", _fake_desc("aaa")),
        ("b.txt", _fake_desc("bbb")),
        ("c.txt", _fake_desc("ccc")),
    ]

    top, children = build_dir_descriptor("data", _NOW, GlimpseDir(), child_descs)

    count_child = next(c for c in children if c.hasType == "cryd:desc-type/count")
    assert count_child.value == "3"


def test_glimpse_dir_rollup_is_deterministic():
    child_descs = [("a.txt", _fake_desc("aaa")), ("b.txt", _fake_desc("bbb"))]

    top1, _ = build_dir_descriptor("results", _NOW, GlimpseDir(), child_descs)
    top2, _ = build_dir_descriptor("results", _NOW, GlimpseDir(), child_descs)

    assert top1.value == top2.value
    assert top1.id == top2.id


def test_glimpse_dir_rollup_changes_with_different_child_content():
    children_a = [("a.txt", _fake_desc("aaa"))]
    children_b = [("a.txt", _fake_desc("bbb"))]

    top_a, _ = build_dir_descriptor("dir", _NOW, GlimpseDir(), children_a)
    top_b, _ = build_dir_descriptor("dir", _NOW, GlimpseDir(), children_b)

    assert top_a.value != top_b.value


def test_glimpse_dir_meta_ignores_child_content():
    # glimpse-dir-meta has no rollup — same dir/mtime/count means same hash
    children_a = [("a.txt", _fake_desc("aaa"))]
    children_b = [("b.txt", _fake_desc("bbb"))]

    top_a, _ = build_dir_descriptor("dir", _NOW, GlimpseDirMeta(), children_a)
    top_b, _ = build_dir_descriptor("dir", _NOW, GlimpseDirMeta(), children_b)

    # Both have 1 child, same name, same mtime — meta hash must be equal
    assert top_a.value == top_b.value


def test_all_dir_variants_top_value_starts_with_v0():
    for method in [GlimpseDir(), GlimpseDirSlim(), GlimpseDirLight(), GlimpseDirMeta()]:
        top, _ = build_dir_descriptor("dir", _NOW, method, [])
        assert top.value.startswith("v0:"), f"{method.id} missing v0: prefix"


def test_glimpse_dir_light_has_only_mtime_child():
    top, children = build_dir_descriptor("dir", _NOW, GlimpseDirLight(), [])

    assert len(children) == 1
    assert children[0].hasType == "cryd:desc-type/mtime"


def test_glimpse_dir_filename_is_basename_only():
    top, children = build_dir_descriptor("results", _NOW, GlimpseDir(), [])

    fname_child = next(c for c in children if c.hasType == "cryd:desc-type/filename")
    assert fname_child.value == "results"
    assert "/" not in fname_child.value


def test_glimpse_dir_top_references_child_ids():
    top, children = build_dir_descriptor("dir", _NOW, GlimpseDir(), [])

    assert set(top.hasDescriptor) == {c.id for c in children}


def test_glimpse_dir_slim_no_count_child():
    top, children = build_dir_descriptor("dir", _NOW, GlimpseDirSlim(), [])

    assert not any(c.hasType == "cryd:desc-type/count" for c in children)
