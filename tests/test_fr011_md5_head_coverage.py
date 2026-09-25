"""FR-011: a content-addressed md5-head Descriptor carries no per-file coverage.

Two files sharing their first 2048 bytes but differing in size map to one
md5-head node (id = md5(type:value)). Per-file coverage on that node would be
multi-valued; it is omitted and consumers derive it as length / file-size.
"""

from pathlib import Path

import pytest
from rdflib import Graph, Namespace

from crystalia_collector.glimpse_compute import build_file_descriptor
from crystalia_collector.method.glimpse import Glimpse
from crystalia_collector.rdf import model_from_rdf
from crystalia_collector.source.local import LocalSource
from crystalia_collector.work import run_pipeline
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

CRYS = Namespace("https://w3id.org/crystalia/")
_MD5_HEAD = "cryd:desc-type/md5-head"
_FILE_SIZE = "cryd:desc-type/file-size"
_HEAD = bytes(range(256)) * 8  # 2048 bytes
_SIZES = {"a.bin": 3000, "b.bin": 7000}


@pytest.fixture
def collision_dir(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    for name, size in _SIZES.items():
        (data / name).write_bytes(_HEAD + b"\xab" * (size - len(_HEAD)))
    return data


def _nodes_of_type(g: Graph, type_uri: str) -> list:
    return sorted({s for s in g.subjects(CRYS.hasType, None) if str(next(g.objects(s, CRYS.hasType))) == type_uri})


def test_shared_md5_head_node_has_no_coverage_and_loads(collision_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "catalog.ttl"
    run_pipeline(str(collision_dir), ["glimpse"], out, workers=1, fmt="turtle")
    g = Graph()
    g.parse(out, format="turtle")

    heads = _nodes_of_type(g, _MD5_HEAD)
    assert len(heads) == 1
    head = heads[0]
    assert list(g.objects(head, CRYS.coverage)) == []
    assert [int(o) for o in g.objects(head, CRYS.length)] == [2048]

    desc = model_from_rdf(g, Descriptor, subject=str(head))
    assert isinstance(desc, Descriptor)
    assert desc.coverage is None
    assert desc.length == 2048


def test_consumer_derivation_matches_old_per_file_coverage(collision_dir: Path) -> None:
    source = LocalSource()
    head_ids = set()
    for file_obj in source.list_files(str(collision_dir)):
        top, children = build_file_descriptor(file_obj, Glimpse(), source)
        by_type = {c.hasType: c for c in children}
        head = by_type[_MD5_HEAD]
        head_ids.add(head.id)
        old_coverage = min(2048 / file_obj.size, 1.0)
        derived = head.length / int(by_type[_FILE_SIZE].value)
        assert derived == pytest.approx(old_coverage)
        # top-level coverage is per-file-identity (size is in its composite id): unchanged
        assert top.coverage == pytest.approx(old_coverage)
    assert len(head_ids) == 1
