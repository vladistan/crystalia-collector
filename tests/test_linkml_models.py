
import pytest
from linkml_runtime.loaders import yaml_loader
from crystalia.datamodel.crystalia import Item, Descriptor, Method, DescriptorRobustness, DescriptorType
from rdflib import Graph
from crystalia_collector.rdf import model_from_rdf, rdf_from_model


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
        robustness=DescriptorRobustness.EXTREMELY_HIGH,
    )

@pytest.fixture
def descriptor_type_sha256_full(method_sha256):
    return DescriptorType(
        id="cryd:sha256_whole_file",
        label="SHA256 full file checksum",
        usesMethod=method_sha256.id,
    )

@pytest.fixture
def descriptor_short_file_full_hash(descriptor_type_sha256_full):
    descriptor = Descriptor(
        id="cryd:desc/bob.txt/sha256_whole_file/1",
        hasType=descriptor_type_sha256_full.id,
        value="02342342aaa223",
        offset=0,
        coverage=1.0,
        length=4096,
    )

    return descriptor

def test_create_item(item):
    """Create a descriptor."""

    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"



def test_descriptor_model(item, descriptor_short_file_full_hash):

    item.hasDescriptor.append(descriptor_short_file_full_hash)
    descriptor_short_file_full_hash.hasDescriptor.append(descriptor_short_file_full_hash)

def test_create_descriptor_type(descriptor_type_sha256_full):

    dtype = descriptor_type_sha256_full
    assert dtype.label == "SHA256 full file checksum"
    assert dtype.id == "cryd:sha256_whole_file"


def test_rdf_from_model(item, descriptor_type_sha256_full, method_sha256, descriptor_short_file_full_hash):

    item.hasDescriptor.append(descriptor_short_file_full_hash)
    item_rdf = rdf_from_model(item, )
    dtype_rdf = rdf_from_model(descriptor_type_sha256_full)
    method_rdf = rdf_from_model(method_sha256)
    descriptor_rdf = rdf_from_model(descriptor_short_file_full_hash)

    g = item_rdf + dtype_rdf + method_rdf + descriptor_rdf

    g.serialize(destination="test.ttl", format="ttl")



def test_model_from_rdf(short_file_single_descriptor):


    rdf_graph = Graph()
    rdf_graph.parse(short_file_single_descriptor, format='turtle')

    # Use the function to get the data class instance
    item = model_from_rdf(rdf_graph, Item)

    # Perform assertions
    assert item.label == "Short file in the cohort"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"

    assert len(item.hasDescriptor) == 1


    descriptor = model_from_rdf(rdf_graph, Descriptor, subject=item.hasDescriptor[0])
    assert descriptor.hasType == "cryd:sha256_whole_file"


    desc_type = model_from_rdf(rdf_graph, DescriptorType, subject=str(descriptor.hasType))
    assert desc_type.label == "SHA256 full file checksum"
    assert desc_type.usesMethod == "cryd:sha256"

    method = model_from_rdf(rdf_graph, Method, subject=str(desc_type.usesMethod))
    assert method.label == "SHA256"
    assert method.robustness.code.text == DescriptorRobustness.EXTREMELY_HIGH.text
