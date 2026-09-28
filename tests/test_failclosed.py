"""Fail-closed harvests with exact chunk regions (DM v2 plan, Phase 5)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from crystalia_collector.app import app
from crystalia_collector.work import (
    HarvestIncompleteError,
    _assemble_region_composite,
    _process_task_file,
    _validate_partials_dir,
    run_pipeline,
    write_partials_manifest,
)
from crystalia_data_model.types.leaves import mint_md5_region

runner = CliRunner()


# --- Step 5.1: positional chunk regions ---


def _write_task_file(tmp_path: Path, uri: Path, size: int, block_size: int) -> Path:
    task_file = tmp_path / "task.txt"
    offsets = list(range(0, size, block_size)) or [0]
    lines = "".join(f"{uri} {size} md5-8gb {block_size} {off}\n" for off in offsets)
    task_file.write_text(lines)
    return task_file


def test_chunk_regions_have_correct_offsets_and_lengths(tmp_path):
    block = 1024
    size = int(block * 2.5)
    f = tmp_path / "f.bin"
    f.write_bytes(b"x" * size)

    task_file = _write_task_file(tmp_path, f, size, block)
    results = _process_task_file(str(task_file))

    parts = sorted((d for _uri, d in results), key=lambda d: int(d.offset))
    assert len(parts) == 3
    assert [int(p.offset) for p in parts] == [0, block, 2 * block]
    assert [int(p.length) for p in parts] == [block, block, block // 2]


def test_region_composite_total_and_iri_matches_dm(tmp_path):
    block = 1024
    size = int(block * 2.5)
    f = tmp_path / "f.bin"
    f.write_bytes(b"x" * size)

    task_file = _write_task_file(tmp_path, f, size, block)
    results = _process_task_file(str(task_file))
    parts = [d for _uri, d in results]

    composite = _assemble_region_composite(str(f), parts)
    assert composite.total == 3

    from crystalia_data_model.types.coverage import mint_md5_chunked

    expected = mint_md5_chunked(3, sorted(parts, key=lambda d: int(d.offset)))
    assert composite.id == expected.id
    assert composite.value == expected.value


def test_subblock_file_produces_single_true_length_part(tmp_path):
    block = 4096
    size = 100
    f = tmp_path / "small.bin"
    f.write_bytes(b"y" * size)

    task_file = _write_task_file(tmp_path, f, size, block)
    results = _process_task_file(str(task_file))

    assert len(results) == 1
    _uri, desc = results[0]
    assert int(desc.offset) == 0
    assert int(desc.length) == size


def test_assemble_region_composite_raises_on_gap():
    part_a = mint_md5_region(0, 100, "a" * 32)
    part_b = mint_md5_region(200, 100, "b" * 32)  # gap: expected offset 100

    with pytest.raises(HarvestIncompleteError):
        _assemble_region_composite("uri", [part_a, part_b])


# --- Step 5.2: fail-closed run ---


def test_run_pipeline_raises_and_leaves_no_output_on_task_failure(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    victim = src / "b.txt"
    victim.write_bytes(b"bbb")

    # List first (as the checkpoint does), then delete the listed entry before hashing.
    output = tmp_path / "out.ttl"

    import crystalia_collector.work as work_mod

    real_list_dir = work_mod.list_dir

    def list_then_delete(prefix, method_id, task_dir):
        result = real_list_dir(prefix, method_id, task_dir)
        victim.unlink()
        return result

    with patch.object(work_mod, "list_dir", side_effect=list_then_delete), pytest.raises(HarvestIncompleteError):
        run_pipeline(str(src), ["md5"], output, workers=1, fmt="turtle")

    assert not output.exists()
    assert not (tmp_path / "out.ttl.tmp").exists()


def test_run_pipeline_atomic_success_leaves_no_tmp_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    output = tmp_path / "out.ttl"

    run_pipeline(str(src), ["md5"], output, workers=1, fmt="turtle")

    assert output.exists()
    assert not (tmp_path / "out.ttl.tmp").exists()


def test_cli_run_rejects_fail_fast_flag(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")

    result = runner.invoke(app, ["run", str(src), "--fail-fast"])

    assert result.exit_code != 0
    assert "no such option" in result.output.lower()


# --- Step 5.3: partials manifest ---


def test_partials_dir_rejects_s3_uri(tmp_path):
    with pytest.raises(ValueError, match="S3"):
        _validate_partials_dir(Path("s3://bucket/partials"), tmp_path / "out.ttl")


def test_partials_dir_rejects_equal_to_output(tmp_path):
    same = tmp_path / "shared"
    with pytest.raises(ValueError, match="may not equal or contain"):
        _validate_partials_dir(same, same)


def test_partials_dir_rejects_containing_output(tmp_path):
    partials = tmp_path / "partials"
    output = partials / "out.ttl"
    with pytest.raises(ValueError, match="may not equal or contain"):
        _validate_partials_dir(partials, output)


def test_write_partials_manifest_lists_unhashed_and_completed(tmp_path):
    partials_dir = tmp_path / "partials"
    output = tmp_path / "out.ttl"
    part = mint_md5_region(0, 10, "a" * 32)

    manifest_path = write_partials_manifest(partials_dir, output, ["missing.txt 10 md5 0 0"], [part])

    content = manifest_path.read_text()
    assert "missing.txt 10 md5 0 0" in content
    assert part.id in content
    assert not output.exists()


def test_cli_annotate_writes_partials_manifest_on_failure(tmp_path):
    victim = tmp_path / "gone.txt"
    victim.write_bytes(b"data")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{victim} 4 md5 0 0\n")
    victim.unlink()

    output = tmp_path / "out.txt"
    partials_dir = tmp_path / "partials"

    result = runner.invoke(
        app,
        ["annotate", str(task_file), "--output-file", str(output), "--partials-dir", str(partials_dir)],
    )

    assert result.exit_code != 0
    assert not output.exists()
    manifest = partials_dir / "partials_manifest.txt"
    assert manifest.exists()
    assert str(victim) in manifest.read_text()


def test_cli_annotate_succeeds_without_partials(tmp_path):
    f = tmp_path / "ok.txt"
    f.write_bytes(b"data")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{f} 4 md5 0 0\n")
    output = tmp_path / "out.txt"

    result = runner.invoke(app, ["annotate", str(task_file), "--output-file", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert str(f) in output.read_text()


# --- Step 5.4: abort on internal inconsistency ---


def test_run_captures_sentry_and_exits_nonzero_on_harvest_error(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"aaa")
    output = tmp_path / "out.ttl"

    with (
        patch("crystalia_collector.app.run_pipeline", side_effect=HarvestIncompleteError("boom")),
        patch("crystalia_collector.app.sentry_sdk.capture_exception") as mock_capture,
    ):
        result = runner.invoke(app, ["run", str(src), "-o", str(output)])

    assert result.exit_code != 0
    mock_capture.assert_called_once()


def test_annotate_captures_sentry_on_failure(tmp_path):
    victim = tmp_path / "gone.txt"
    victim.write_bytes(b"data")
    task_file = tmp_path / "task.txt"
    task_file.write_text(f"{victim} 4 md5 0 0\n")
    victim.unlink()
    output = tmp_path / "out.txt"

    with patch("crystalia_collector.app.sentry_sdk.capture_exception") as mock_capture:
        result = runner.invoke(app, ["annotate", str(task_file), "--output-file", str(output)])

    assert result.exit_code != 0
    mock_capture.assert_called_once()
