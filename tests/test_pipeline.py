from crystalia_collector.work import RunResult, run_pipeline


def test_run_pipeline_produces_valid_turtle(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "file1.txt").write_text("hello world")
    (data_dir / "file2.txt").write_text("goodbye world")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), "md5-8gb", output, workers=1, fmt="turtle")

    assert output.exists()
    from rdflib import Graph

    g = Graph()
    g.parse(output, format="turtle")
    assert len(g) > 0
    assert isinstance(result, RunResult)
    assert result.succeeded > 0
    assert result.failed == 0


def test_run_pipeline_deterministic(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.txt").write_text("alpha")
    (data_dir / "b.txt").write_text("beta")

    out1 = tmp_path / "out1.ttl"
    out2 = tmp_path / "out2.ttl"
    run_pipeline(str(data_dir), "md5-8gb", out1, workers=1, fmt="turtle")
    run_pipeline(str(data_dir), "md5-8gb", out2, workers=2, fmt="turtle")
    assert out1.read_text() == out2.read_text()


def test_run_pipeline_text_format(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test.txt").write_text("test content")

    output = tmp_path / "catalog.txt"
    result = run_pipeline(str(data_dir), "md5-8gb", output, workers=1, fmt="text")

    assert output.exists()
    content = output.read_text()
    assert len(content) > 0
    assert result.succeeded > 0


def test_run_pipeline_result_counts(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "one.txt").write_text("one")
    (data_dir / "two.txt").write_text("two")
    (data_dir / "three.txt").write_text("three")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), "md5-8gb", output, workers=2, fmt="turtle")

    assert result.total == result.succeeded + result.failed
    assert result.succeeded >= 1
    assert result.failed == 0


def test_run_pipeline_empty_directory(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), "md5-8gb", output, workers=1, fmt="turtle")

    assert result.total == 0
    assert result.succeeded == 0
    assert result.failed == 0
    assert output.exists()


def test_run_pipeline_progress_callback(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.txt").write_text("alpha")
    (data_dir / "b.txt").write_text("beta")

    counts = []
    output = tmp_path / "catalog.ttl"
    run_pipeline(
        str(data_dir),
        "md5-8gb",
        output,
        workers=1,
        fmt="turtle",
        progress_callback=counts.append,
    )

    assert sum(counts) >= 2
