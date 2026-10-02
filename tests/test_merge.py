"""Partitioned harvest merge (DM v2 plan, Phase 9)."""

from pathlib import Path

import pytest
from rdflib import RDF, Graph, Namespace
from typer.testing import CliRunner

from crystalia_collector.app import app
from crystalia_collector.merge import load_descriptors, load_sidecar, merge
from crystalia_collector.work import list_dir, load_listing_manifest, write_listing_manifest

CRYS = Namespace("https://w3id.org/crystalia/")

runner = CliRunner()


def _annotate(task_file: Path, output: Path) -> None:
    result = runner.invoke(app, ["annotate", str(task_file), "--output-file", str(output)])
    assert result.exit_code == 0, result.output


# --- Step 9.1: listing manifest + sidecar ---


def test_list_writes_listing_manifest_with_expected_counts(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"a")
    (src / "b.txt").write_bytes(b"b")
    task_dir = tmp_path / "tasks"

    list_dir(str(src), "md5", task_dir)

    manifest = load_listing_manifest(task_dir / "listing_manifest.json")
    assert manifest == {str(src): 2}


def test_annotate_writes_sidecar_alongside_output(tmp_path):
    f = tmp_path / "sub" / "a.txt"
    f.parent.mkdir()
    f.write_bytes(b"hello")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{f} 5 md5 0 0\n")
    output = tmp_path / "out.ttl"

    _annotate(task_file, output)

    sidecar = Path(f"{output}.sidecar")
    rows = load_sidecar(sidecar)
    assert rows == [(str(f.parent), f.name, rows[0][2])]


def test_annotate_output_has_no_harvest_record(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"data")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{f} 4 md5 0 0\n")
    output = tmp_path / "out.ttl"

    _annotate(task_file, output)

    g = Graph()
    g.parse(output, format="turtle")
    assert list(g.subjects(RDF.type, CRYS.HarvestRecord)) == []


# --- Step 9.2: merge command ---


def _write_partition(tmp_path: Path, name: str, files: dict[str, bytes]) -> Path:
    part_dir = tmp_path / name
    part_dir.mkdir()
    task_file = part_dir / "task.txt"
    lines = []
    for basename, data in files.items():
        p = part_dir / "data" / basename
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        lines.append(f"{p} {len(data)} md5 0 0\n")
    task_file.write_text("".join(lines))
    output = part_dir / "out.ttl"
    _annotate(task_file, output)
    return output


def test_merge_order_independent(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    (src / "b.txt").write_bytes(b"bbb")
    task_dir = tmp_path / "tasks"
    list_dir(str(src), "md5", task_dir)
    manifest = task_dir / "listing_manifest.json"

    part_a = _write_partition(tmp_path, "part-a", {"a.txt": b"aaa"})
    part_b = _write_partition(tmp_path, "part-b", {"b.txt": b"bbb"})
    # rewrite sidecars to point at the real src dir, not the partition's own copy
    for part, name, _data in [(part_a, "a.txt", b"aaa"), (part_b, "b.txt", b"bbb")]:
        sidecar = Path(f"{part}.sidecar")
        rows = load_sidecar(sidecar)
        desc_id = rows[0][2]
        sidecar.write_text(f"{src}\t{name}\t{desc_id}\n")
        write_listing_manifest(task_dir, {str(src): 2})

    out1 = tmp_path / "merged1.ttl"
    out2 = tmp_path / "merged2.ttl"
    merge(manifest, [part_a, part_b], out1, str(src), ["md5"])
    merge(manifest, [part_b, part_a], out2, str(src), ["md5"])

    g1, g2 = Graph(), Graph()
    g1.parse(out1, format="turtle")
    g2.parse(out2, format="turtle")
    descs1 = {str(s) for s in g1.subjects(CRYS.hasType, None)}
    descs2 = {str(s) for s in g2.subjects(CRYS.hasType, None)}
    assert descs1 == descs2


def test_merge_missing_child_raises_incomplete_rollup(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    (src / "b.txt").write_bytes(b"bbb")
    task_dir = tmp_path / "tasks"
    write_listing_manifest(task_dir, {str(src): 2})
    manifest = task_dir / "listing_manifest.json"

    part_a = _write_partition(tmp_path, "part-a", {"a.txt": b"aaa"})
    sidecar = Path(f"{part_a}.sidecar")
    rows = load_sidecar(sidecar)
    sidecar.write_text(f"{src}\ta.txt\t{rows[0][2]}\n")

    output = tmp_path / "merged.ttl"
    from crystalia_data_model.types.errors import IncompleteRollup

    with pytest.raises(IncompleteRollup):
        merge(manifest, [part_a], output, str(src), ["md5"])
    assert not output.exists()


def test_merge_output_has_one_harvest_record(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    task_dir = tmp_path / "tasks"
    write_listing_manifest(task_dir, {str(src): 1})
    manifest = task_dir / "listing_manifest.json"

    part_a = _write_partition(tmp_path, "part-a", {"a.txt": b"aaa"})
    sidecar = Path(f"{part_a}.sidecar")
    rows = load_sidecar(sidecar)
    sidecar.write_text(f"{src}\ta.txt\t{rows[0][2]}\n")

    output = tmp_path / "merged.ttl"
    merge(manifest, [part_a], output, str(src), ["md5"])

    g = Graph()
    g.parse(output, format="turtle")
    harvest_records = list(g.subjects(CRYS.usesMethod, None))
    assert len(harvest_records) == 1


def test_load_descriptors_reads_typed_subjects(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"aaa")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{f} 3 md5 0 0\n")
    output = tmp_path / "out.ttl"
    _annotate(task_file, output)

    descs = load_descriptors(output)
    assert len(descs) == 1
    (desc,) = descs.values()
    assert desc.hasType == "crys:dtype/md5"


# --- Step 9.3: merge equivalence ---


def test_cli_merge_help_lists_manifest_and_partitions():
    result = runner.invoke(app, ["merge", "--help"])
    assert result.exit_code == 0
    assert "listing-manifest" in result.output.replace("_", "-") or "LISTING_MANIFEST" in result.output
    assert "PARTITION_OUTPUT" in result.output or "partition-output" in result.output.replace("_", "-")
