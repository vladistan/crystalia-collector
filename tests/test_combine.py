import pytest

from crystalia_collector.work import combine_descriptors
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor, Item


@pytest.fixture
def sample_items():
    return [
        Item(id="crys:item-b", label="Item B", hasDescriptor=["crys:desc-2"]),
        Item(id="crys:item-a", label="Item A", hasDescriptor=["crys:desc-1"]),
    ]


def test_combine_descriptors_turtle_produces_valid_rdf(sample_items, tmp_path):
    output = tmp_path / "catalog.ttl"
    combine_descriptors(sample_items, output, "turtle")
    assert output.exists()
    from rdflib import Graph

    g = Graph()
    g.parse(output, format="turtle")
    assert len(g) > 0


def test_combine_descriptors_turtle_is_deterministic(sample_items, tmp_path):
    out1 = tmp_path / "out1.ttl"
    out2 = tmp_path / "out2.ttl"
    combine_descriptors(sample_items, out1, "turtle")
    combine_descriptors(sample_items, out2, "turtle")
    assert out1.read_text() == out2.read_text()


def test_combine_descriptors_turtle_sorts_items_by_id(tmp_path):
    items = [
        Item(id="crys:item-z", label="Item Z"),
        Item(id="crys:item-a", label="Item A"),
    ]
    output = tmp_path / "sorted.ttl"
    combine_descriptors(items, output, "turtle")
    content = output.read_text()
    pos_a = content.find("item-a")
    pos_z = content.find("item-z")
    assert pos_a >= 0
    assert pos_z >= 0
    assert pos_a < pos_z


def test_combine_descriptors_text_format(sample_items, tmp_path):
    output = tmp_path / "catalog.txt"
    combine_descriptors(sample_items, output, "text")
    lines = output.read_text().strip().split("\n")
    assert len(lines) == 2
    assert "item-a" in lines[0]
    assert "desc-1" in lines[0]
    assert "item-b" in lines[1]
    assert "desc-2" in lines[1]


def test_combine_descriptors_text_is_deterministic(sample_items, tmp_path):
    out1 = tmp_path / "out1.txt"
    out2 = tmp_path / "out2.txt"
    combine_descriptors(sample_items, out1, "text")
    combine_descriptors(sample_items, out2, "text")
    assert out1.read_text() == out2.read_text()


def test_combine_descriptors_empty_items_turtle(tmp_path):
    output = tmp_path / "empty.ttl"
    combine_descriptors([], output, "turtle")
    assert output.exists()


def test_combine_descriptors_empty_items_text(tmp_path):
    output = tmp_path / "empty.txt"
    combine_descriptors([], output, "text")
    assert output.exists()
    assert output.read_text() == ""


def test_combine_descriptors_with_descriptor_objects(tmp_path):
    desc = Descriptor(
        id="cryd:abc123",
        hasType="cryd:md5-8gb",
        value="abc123def456",  # pragma: allowlist secret
        offset=0,
        coverage=1.0,
        length=8589934592,
    )
    items = [Item(id="crys:test.txt", label="test.txt", hasDescriptor=["cryd:abc123"])]
    output = tmp_path / "catalog.ttl"
    combine_descriptors(items, output, "turtle", descriptors=[desc])

    from rdflib import Graph

    g = Graph()
    g.parse(output, format="turtle")

    # Should have both Item and Descriptor triples
    subjects = {str(s) for s in g.subjects()}
    assert any("test.txt" in s for s in subjects)
    assert any("abc123" in s for s in subjects)
