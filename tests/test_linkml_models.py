import pytest
from rdflib import Graph

from crystalia_collector.rdf import model_from_rdf, rdf_from_model
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor, Item, Method


@pytest.fixture
def item():
    return Item(
        id="s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202-samples-cohort/a.txt",
        isPartOf="https://registry.opendata.aws/ilmn-dragen-1kgp",
        label="Short file in the cohort",
    )


@pytest.fixture
def method_sha256():
    return Method(
        id="cryd:sha256",
        label="SHA256",
    )


@pytest.fixture
def descriptor_short_file_full_hash(method_sha256):
    descriptor = Descriptor(
        id="cryd:desc/bob.txt/sha256_whole_file/1",
        hasType="cryd:sha256_whole_file",
        value="02342342aaa223",
        length=4096,
    )

    return descriptor


def test_create_item(item):
    """Create a descriptor."""

    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"


def test_descriptor_model(item, descriptor_short_file_full_hash):
    item.hasDescriptor = [descriptor_short_file_full_hash.id]
    descriptor_short_file_full_hash.hasDescriptor = [descriptor_short_file_full_hash.id]


def test_rdf_from_model(
    item,
    method_sha256,
    descriptor_short_file_full_hash,
):
    item.hasDescriptor = [descriptor_short_file_full_hash.id]
    item_rdf = rdf_from_model(item)
    method_rdf = rdf_from_model(method_sha256)
    descriptor_rdf = rdf_from_model(descriptor_short_file_full_hash)

    g = item_rdf + method_rdf + descriptor_rdf

    g.serialize(destination="test.ttl", format="ttl")


def test_model_from_rdf(short_file_single_descriptor):
    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format="turtle")

    item_uri = "s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202/samples-cohort/a.txt"

    # Use the function to get the data class instance
    item = model_from_rdf(rdf_graph, Item, subject=item_uri)

    # Perform assertions
    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"

    assert len(item.hasDescriptor) == 1

    descriptor = model_from_rdf(rdf_graph, Descriptor, subject=item.hasDescriptor[0])
    assert descriptor.hasType == "cryd:sha256_whole_file"

    method = model_from_rdf(rdf_graph, Method, subject="cryd:sha256")
    assert method.label == "SHA256"


def test_model_from_rdf_without_subject_resolves_item_by_type(test_dir):
    """Regression: loading without an explicit subject must resolve the Item by
    rdf:type rather than falling back to an arbitrary (wrong) subject.

    The fixture declares Method, DescriptorType and Descriptor before the Item,
    all using the slash-convention crys: type URIs. Without the class_uri fix the
    loader searches for a hash-separated type URI absent from the graph, fails to
    match, and falls back to the first arbitrary subject -- mis-validating a
    Method/Descriptor as an Item (wrong label or a missing-field ValidationError).
    This is the no-explicit-subject path that the `combine` command exercises.
    """
    rdf_graph = Graph()
    rdf_graph.parse(test_dir / "rdf_data" / "multi_subject_no_root.ttl", format="turtle")

    item = model_from_rdf(rdf_graph, Item)

    assert isinstance(item, Item)
    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"
    assert str(item.id).endswith("samples-cohort/a.txt")
