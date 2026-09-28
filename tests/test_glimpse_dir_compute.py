from datetime import UTC, datetime

import pytest

from crystalia_collector.glimpse_dir_compute import build_dir_descriptor
from crystalia_collector.method.glimpse_dir import (
    GlimpseDir,
    GlimpseDirLight,
    GlimpseDirMeta,
    GlimpseDirSlim,
)
from crystalia_data_model.types.errors import IncompleteRollup
from crystalia_data_model.types.leaves import mint_filename
from crystalia_data_model.types.rollup import mint_glimpse_dir, mint_glimpse_dir_light, mint_glimpse_dir_slim
from crystalia_data_model.types.validate import ensure_valid

_NOW = datetime(2024, 6, 1, tzinfo=UTC)


def _fake_desc(value_suffix: str):
    """A real, valid leaf descriptor usable as a rollup child (any type works structurally)."""
    return mint_filename(value_suffix)


def test_glimpse_dir_empty_directory():
    top, children = build_dir_descriptor("results", _NOW, GlimpseDir(), [])

    count_child = next(c for c in children if c.hasType == "cryd:desc-type/count")
    assert count_child.value == "0"
    assert ensure_valid(top) is top


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


def test_all_dir_variants_mint_a_valid_top():
    for method in [GlimpseDir(), GlimpseDirSlim(), GlimpseDirLight(), GlimpseDirMeta()]:
        top, _ = build_dir_descriptor("dir", _NOW, method, [])
        assert ensure_valid(top) is top, f"{method.id} top failed ensure_valid"


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


# --- DM equivalence, IncompleteRollup, bottom-up order independence ---


def test_glimpse_dir_iri_equals_dm_rollup_dir_result():
    child_descs = [("a.txt", _fake_desc("aaa")), ("b.txt", _fake_desc("bbb"))]

    top, children = build_dir_descriptor("data", _NOW, GlimpseDir(), child_descs)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_dir(
        len(child_descs),
        child_descs,
        filename=by_type["cryd:desc-type/filename"],
        mtime=by_type["cryd:desc-type/mtime"],
        count=by_type["cryd:desc-type/count"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_dir_slim_iri_equals_dm_rollup_dir_result():
    child_descs = [("a.txt", _fake_desc("aaa")), ("b.txt", _fake_desc("bbb"))]

    top, children = build_dir_descriptor("data", _NOW, GlimpseDirSlim(), child_descs)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_dir_slim(
        len(child_descs),
        child_descs,
        filename=by_type["cryd:desc-type/filename"],
        mtime=by_type["cryd:desc-type/mtime"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_dir_light_iri_equals_dm_rollup_dir_result():
    child_descs = [("a.txt", _fake_desc("aaa")), ("b.txt", _fake_desc("bbb"))]

    top, children = build_dir_descriptor("data", _NOW, GlimpseDirLight(), child_descs)

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_dir_light(
        len(child_descs),
        child_descs,
        mtime=by_type["cryd:desc-type/mtime"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_glimpse_dir_meta_iri_equals_dm_mint():
    from crystalia_data_model.types.leaves import mint_glimpse_dir_meta

    top, children = build_dir_descriptor("data", _NOW, GlimpseDirMeta(), [])

    by_type = {c.hasType: c for c in children}
    expected = mint_glimpse_dir_meta(
        filename=by_type["cryd:desc-type/filename"],
        mtime=by_type["cryd:desc-type/mtime"],
        count=by_type["cryd:desc-type/count"],
    )
    assert top.id == expected.id
    assert top.value == expected.value


def test_expected_larger_than_collected_children_raises_incomplete_rollup():
    child_descs = [("a.txt", _fake_desc("aaa"))]

    with pytest.raises(IncompleteRollup):
        build_dir_descriptor("dir", _NOW, GlimpseDir(), child_descs, expected=2)


def test_nested_rollup_is_bottom_up_and_order_independent():
    leaf_a = _fake_desc("aaa")
    leaf_b = _fake_desc("bbb")

    # A subdirectory rolled up first, then used as a child of the parent — order
    # of (name, child) pairs handed to the parent must not affect the parent hash.
    subdir_top, _ = build_dir_descriptor("sub", _NOW, GlimpseDir(), [("a.txt", leaf_a)])

    parent_children_1 = [("b.txt", leaf_b), ("sub", subdir_top)]
    parent_children_2 = [("sub", subdir_top), ("b.txt", leaf_b)]

    top1, _ = build_dir_descriptor("parent", _NOW, GlimpseDir(), parent_children_1)
    top2, _ = build_dir_descriptor("parent", _NOW, GlimpseDir(), parent_children_2)

    assert top1.id == top2.id
    assert top1.value == top2.value
