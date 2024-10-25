
import pytest
from linkml_runtime.loaders import yaml_loader
from crystalia.datamodel.crystalia import Item, Descriptor, Method, DescriptorRobustness, DescriptorType
from crystalia_collector.rdf import rdf_from_model


@pytest.fixture
def item():
    return Item(
        id="s3://1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202-samples-cohort/a.txt",
        isPartOf="https://registry.opendata.aws/ilmn-dragen-1kgp",
        label="bob.txt",
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
        id="https://example.com/sha256",
        label="SHA256 full file checksum",
        usesMethod=method_sha256.id,
    )

def test_create_item(item):
    """Create a descriptor."""

    assert item.label == "bob.txt"
    assert item.isPartOf == "https://registry.opendata.aws/ilmn-dragen-1kgp"


def test_create_descriptor(item):
    descriptor = Descriptor(
        id="https://example.com/bob.txt", 
        hasType="https://example.com/bob.txt",
        value="0223",
        offset=0,
        coverage=1.0,
        length=4,
    )

    item.hasDescriptor.append(descriptor)

def test_create_descriptor_type(descriptor_type_sha256_full):

    dtype = descriptor_type_sha256_full
    assert dtype.label == "SHA256 full file checksum"
    assert dtype.id == "https://example.com/sha256"


def test_rdf_from_model(item, descriptor_type_sha256_full):
    item_rdf = rdf_from_model(item, )
 
    dtype_rdf = rdf_from_model(descriptor_type_sha256_full)

    g = item_rdf + dtype_rdf

    g.serialize(destination="test.ttl", format="ttl")
