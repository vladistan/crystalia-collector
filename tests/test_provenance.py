"""Harvest provenance: content-addressed Method nodes and per-harvest records (DM v2 plan, Phase 8)."""

import contextlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from rdflib import RDF, Graph, URIRef

from crystalia_collector.method import _METHODS
from crystalia_collector.work import HarvestIncompleteError, run_pipeline

SNAPSHOT_PATH = Path(__file__).parent / "method_params_snapshot.json"
CRYS_NS = "https://w3id.org/crystalia/"
HARVEST_RECORD = URIRef(f"{CRYS_NS}HarvestRecord")
_PINNED_TIMESTAMP = 1704067200.0  # 2024-01-01T00:00:00Z


class _PinnedStat:
    """Wraps a real os.stat_result, pinning only mtime/ctime; everything else passes through."""

    def __init__(self, real: os.stat_result) -> None:
        self._real = real
        self.st_mtime = _PINNED_TIMESTAMP
        self.st_ctime = _PINNED_TIMESTAMP

    def __getattr__(self, name: str):
        return getattr(self._real, name)


@pytest.fixture(autouse=True)
def _pin_filesystem_times(monkeypatch):
    real_stat = os.stat

    def pinned_stat(path, *args, **kwargs):  # noqa: ANN001 - matches os.stat's signature
        return _PinnedStat(real_stat(path, *args, **kwargs))

    monkeypatch.setattr(os, "stat", pinned_stat)


def _tree(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.txt").write_text("alpha")
    (data_dir / "b.txt").write_text("beta")
    return data_dir


# --- Step 8.1: content-addressed Method nodes ---


def test_same_method_across_harvests_mints_the_same_method_iri(tmp_path):
    tree = _tree(tmp_path)
    out1, out2 = tmp_path / "out1.ttl", tmp_path / "out2.ttl"
    run_pipeline(str(tree), ["glimpse"], out1, workers=1, fmt="turtle")
    run_pipeline(str(tree), ["glimpse"], out2, workers=1, fmt="turtle")

    g1, g2 = Graph(), Graph()
    g1.parse(out1, format="turtle")
    g2.parse(out2, format="turtle")
    methods1 = {str(s) for s in g1.subjects(RDF.type, URIRef(f"{CRYS_NS}Method"))}
    methods2 = {str(s) for s in g2.subjects(RDF.type, URIRef(f"{CRYS_NS}Method"))}

    assert methods1 == methods2
    assert len(methods1) == 1


def test_method_params_snapshot_matches_registered_methods():
    """Each registered method's canonical parameters must match the checked-in snapshot.

    Changing a method's parameters without renaming it (registry key) changes what
    this test computes but not what is checked in, so the diff fails here first.
    """
    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    current = {method_id: cls().parameters() for method_id, cls in _METHODS.items()}
    assert current == snapshot


# --- Step 8.2: per-harvest record ---


def test_harvest_record_carries_run_metadata(tmp_path):
    tree = _tree(tmp_path)
    out = tmp_path / "out.ttl"
    run_pipeline(str(tree), ["glimpse", "md5"], out, workers=1, fmt="turtle")

    g = Graph()
    g.parse(out, format="turtle")
    records = list(g.subjects(RDF.type, HARVEST_RECORD))
    assert len(records) == 1

    record = records[0]
    props = {str(p).removeprefix(CRYS_NS): str(o) for p, o in g.predicate_objects(record)}
    assert props["sourceRoot"] == str(tree)
    assert "startedAt" in props
    assert "endedAt" in props
    assert "collectorVersion" in props
    uses_method = {str(o) for o in g.objects(record, URIRef(f"{CRYS_NS}usesMethod"))}
    has_root = {str(o) for o in g.objects(record, URIRef(f"{CRYS_NS}hasRoot"))}
    assert len(uses_method) == 2
    assert len(has_root) > 0


def test_failed_run_emits_no_harvest_record_anywhere(tmp_path):
    tree = _tree(tmp_path)
    out = tmp_path / "out.ttl"
    with (
        patch("crystalia_collector.work._process_task_file", side_effect=RuntimeError("boom")),
        contextlib.suppress(HarvestIncompleteError),
    ):
        run_pipeline(str(tree), ["md5-8gb"], out, workers=1, fmt="turtle")

    assert not out.exists()


def test_recorded_harvest_record_ttl_byte_identical(tmp_path):
    tree = _tree(tmp_path)
    out = tmp_path / "out.ttl"
    fixed_clock = datetime(2024, 1, 1, tzinfo=UTC)
    counter = iter(range(1, 100))

    def next_item_id() -> str:
        return f"crys:recorded-item-{next(counter):04d}"

    run_pipeline(
        str(tree),
        ["glimpse", "md5"],
        out,
        workers=1,
        fmt="turtle",
        item_id_factory=next_item_id,
        clock=lambda: fixed_clock,
        harvest_id_factory=lambda: "cryd:harvest/00000000-0000-0000-0000-000000000000",
        source_root="/recorded/fixture/provenance-tree",
    )

    recorded = Path(__file__).parent / "recorded" / "harvest-record.ttl"
    assert out.read_bytes() == recorded.read_bytes()
