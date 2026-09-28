"""Merge equivalence: run vs. list -> split -> annotate -> merge (DM v2 plan, Phase 9 Step 9.3)."""

from collections.abc import Callable
from pathlib import Path

from rdflib import RDF, Graph, Namespace
from typer.testing import CliRunner

from crystalia_collector.app import app
from crystalia_collector.merge import merge
from crystalia_collector.work import list_dir, run_pipeline

CRYS = Namespace("https://w3id.org/crystalia/")

runner = CliRunner()


def _pinned_item_id_factory() -> Callable[[], str]:
    counter = iter(range(1, 100_000))

    def factory() -> str:
        return f"crys:pinned-item-{next(counter):04d}"

    return factory


def _fixture_tree(root: Path) -> None:
    root.mkdir()
    (root / "a.txt").write_bytes(b"aaa content")
    (root / "b.txt").write_bytes(b"bbb content")
    (root / "c.txt").write_bytes(b"ccc content")


def _descriptor_and_item_triples(ttl_path: Path) -> set[tuple[str, str, str]]:
    """Triples whose subject is a Descriptor or Item -- excludes HarvestRecord's own random id."""
    g = Graph()
    g.parse(ttl_path, format="turtle")
    descriptor_subjects = {str(s) for s in g.subjects(RDF.type, CRYS.Descriptor)}
    item_subjects = {str(s) for s in g.subjects(RDF.type, CRYS.Item)}
    subjects = descriptor_subjects | item_subjects
    return {(str(s), str(p), str(o)) for s, p, o in g if str(s) in subjects}


def test_partitioned_merge_equals_single_run(tmp_path):
    single_src = tmp_path / "single"
    _fixture_tree(single_src)
    single_out = tmp_path / "single.ttl"
    run_pipeline(
        str(single_src),
        ["md5"],
        single_out,
        workers=1,
        fmt="turtle",
        item_id_factory=_pinned_item_id_factory(),
    )

    partitioned_src = tmp_path / "partitioned"
    _fixture_tree(partitioned_src)
    task_dir = tmp_path / "tasks"
    list_dir(str(partitioned_src), "md5", task_dir)
    manifest = task_dir / "listing_manifest.json"

    partition_outputs = []
    for i, task_file in enumerate(sorted(task_dir.glob("task_*"))):
        output = tmp_path / f"partition-{i}.ttl"
        result = runner.invoke(app, ["annotate", str(task_file), "--output-file", str(output)])
        assert result.exit_code == 0, result.output
        partition_outputs.append(output)

    merged_out = tmp_path / "merged.ttl"
    merge(
        manifest,
        partition_outputs,
        merged_out,
        str(partitioned_src),
        ["md5"],
        item_id_factory=_pinned_item_id_factory(),
    )

    single_triples = _descriptor_and_item_triples(single_out)
    merged_triples = _descriptor_and_item_triples(merged_out)
    assert single_triples == merged_triples
