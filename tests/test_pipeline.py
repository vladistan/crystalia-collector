from rdflib import RDF, Graph, URIRef
from rdflib.namespace import DCTERMS

from crystalia_collector.work import RunResult, run_pipeline

CRYS = "https://w3id.org/crystalia#"
CRYS_NS = "https://w3id.org/crystalia/"
ITEM = URIRef(f"{CRYS}Item")
DESCRIPTOR = URIRef(f"{CRYS}Descriptor")
HAS_DESCRIPTOR = URIRef(f"{CRYS_NS}hasDescriptor")
HAS_TYPE = URIRef(f"{CRYS_NS}hasType")


def test_run_pipeline_produces_valid_turtle(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "file1.txt").write_text("hello world")
    (data_dir / "file2.txt").write_text("goodbye world")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), ["md5-8gb"], output, workers=1, fmt="turtle")

    assert output.exists()
    from rdflib import Graph

    g = Graph()
    g.parse(output, format="turtle")
    assert len(g) > 0
    assert isinstance(result, RunResult)
    assert result.succeeded > 0
    assert result.failed == 0


def test_run_pipeline_deterministic_descriptors(tmp_path):
    """Descriptor content is deterministic; Item UUIDs differ between runs."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.txt").write_text("alpha")
    (data_dir / "b.txt").write_text("beta")

    out1 = tmp_path / "out1.ttl"
    out2 = tmp_path / "out2.ttl"
    run_pipeline(str(data_dir), ["md5-8gb"], out1, workers=1, fmt="turtle")
    run_pipeline(str(data_dir), ["md5-8gb"], out2, workers=2, fmt="turtle")

    g1, g2 = Graph(), Graph()
    g1.parse(out1, format="turtle")
    g2.parse(out2, format="turtle")

    # Same number of items and descriptors
    items1 = list(g1.subjects(RDF.type, ITEM))
    items2 = list(g2.subjects(RDF.type, ITEM))
    assert len(items1) == len(items2)
    assert len(list(g1.subjects(RDF.type, DESCRIPTOR))) == len(
        list(g2.subjects(RDF.type, DESCRIPTOR)),
    )

    # Descriptor values are identical across runs
    value_pred = URIRef(f"{CRYS_NS}value")
    vals1 = sorted(str(v) for _, _, v in g1.triples((None, value_pred, None)))
    vals2 = sorted(str(v) for _, _, v in g2.triples((None, value_pred, None)))
    assert vals1 == vals2


def test_run_pipeline_text_format(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test.txt").write_text("test content")

    output = tmp_path / "catalog.txt"
    result = run_pipeline(str(data_dir), ["md5-8gb"], output, workers=1, fmt="text")

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
    result = run_pipeline(str(data_dir), ["md5-8gb"], output, workers=2, fmt="turtle")

    assert result.total == result.succeeded + result.failed
    assert result.succeeded >= 1
    assert result.failed == 0


def test_run_pipeline_empty_directory(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), ["md5-8gb"], output, workers=1, fmt="turtle")

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
        ["md5-8gb"],
        output,
        workers=1,
        fmt="turtle",
        progress_callback=counts.append,
    )

    assert sum(counts) >= 2


def test_run_pipeline_md5_produces_descriptors(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "hello.txt").write_text("hello world")

    output = tmp_path / "catalog.ttl"
    run_pipeline(str(data_dir), ["md5-8gb"], output, workers=1, fmt="turtle")

    g = Graph()
    g.parse(output, format="turtle")

    items = list(g.subjects(RDF.type, ITEM))
    descs = list(g.subjects(RDF.type, DESCRIPTOR))
    assert len(items) == 1
    assert len(descs) >= 1

    # Every hasDescriptor reference should have a Descriptor with a value
    has_desc = URIRef(f"{CRYS_NS}hasDescriptor")
    value_pred = URIRef(f"{CRYS_NS}value")
    for item in items:
        for _, _, desc_id in g.triples((item, has_desc, None)):
            desc_uri = URIRef(
                str(desc_id).replace("cryd:", "https://crystalia.link/data/"),
            )
            assert (desc_uri, value_pred, None) in g


def test_run_pipeline_glimpse_produces_descriptor_tree(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test.txt").write_text("glimpse test content")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(
        str(data_dir),
        ["glimpse"],
        output,
        workers=1,
        fmt="turtle",
    )

    assert result.succeeded == 1

    g = Graph()
    g.parse(output, format="turtle")

    items = list(g.subjects(RDF.type, ITEM))
    descs = list(g.subjects(RDF.type, DESCRIPTOR))
    assert len(items) == 1
    # Glimpse: 1 top + 5 children (filename, size, md5, ctime, mtime)
    assert len(descs) == 6


def test_run_pipeline_glimpse_dir_produces_directory_items(tmp_path):
    data_dir = tmp_path / "data"
    subdir = data_dir / "subdir"
    subdir.mkdir(parents=True)
    (data_dir / "root.txt").write_text("root file")
    (subdir / "child.txt").write_text("child file")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(str(data_dir), ["glimpse-dir"], output, workers=1, fmt="turtle")

    assert result.succeeded == 2  # 2 files

    g = Graph()
    g.parse(output, format="turtle")

    items = list(g.subjects(RDF.type, ITEM))
    # 2 files + 2 dirs (data_dir + subdir)
    assert len(items) == 4

    # Both dirs have a glimpse-dir descriptor
    glimpse_dir_type = URIRef("https://crystalia.link/data/glimpse-dir")
    dir_desc_types = [
        str(o)
        for s in g.subjects(RDF.type, DESCRIPTOR)
        for o in g.objects(s, HAS_TYPE)
        if str(o) == str(glimpse_dir_type)
    ]
    assert len(dir_desc_types) == 2

    # Child file Item has isPartOf pointing to subdir Item
    child_items_with_parent = [s for s in g.subjects(RDF.type, ITEM) if (s, DCTERMS.isPartOf, None) in g]
    assert len(child_items_with_parent) == 2

    # Every isPartOf target is itself an Item
    for s in child_items_with_parent:
        for _, _, parent in g.triples((s, DCTERMS.isPartOf, None)):
            assert (parent, RDF.type, ITEM) in g


def test_run_pipeline_multi_method_merges_descriptors(tmp_path):
    data_dir = tmp_path / "data"
    subdir = data_dir / "sub"
    subdir.mkdir(parents=True)
    (subdir / "a.txt").write_text("alpha")
    (subdir / "b.txt").write_text("beta")

    output = tmp_path / "catalog.ttl"
    result = run_pipeline(
        str(data_dir),
        ["md5-8gb", "glimpse-dir"],
        output,
        workers=1,
        fmt="turtle",
    )

    assert result.failed == 0

    g = Graph()
    g.parse(output, format="turtle")

    items = list(g.subjects(RDF.type, ITEM))
    # 2 files + 2 dirs (data_dir + sub)
    assert len(items) == 4

    # File Items each have 2 descriptors (md5-8gb + glimpse)
    file_items = [s for s in items if (s, DCTERMS.isPartOf, None) in g]
    assert len(file_items) == 2
    for item in file_items:
        desc_ids = list(g.objects(item, HAS_DESCRIPTOR))
        assert len(desc_ids) == 2

    # Dir Items each have 1 descriptor (glimpse-dir)
    dir_items = [s for s in items if s not in file_items]
    assert len(dir_items) == 2
    for item in dir_items:
        desc_ids = list(g.objects(item, HAS_DESCRIPTOR))
        assert len(desc_ids) == 1
