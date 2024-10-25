
import pytest
from linkml_runtime.loaders import yaml_loader
from crystalia.datamodel.crystalia import Item, Descriptor, Method, DescriptorRobustness, DescriptorType

@pytest.fixture
def item():
    return Item(
        id="ds001:file/bob.txt", 
        isPartOf="ds001:dataset1",
        label="bob.txt",
    )

@pytest.fixture
def method_sha256():
    return Method(
        id="cryd:sha256",
        label="SHA256",
        robustness=DescriptorRobustness.EXTREMELY_HIGH,
    )


def test_create_item(item):
    """Create a descriptor."""

    assert item.label == "bob.txt"
    assert item.isPartOf == "ds001:dataset1"


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

def test_create_descriptor_type(method_sha256):

    dtype = DescriptorType(
        id="https://example.com/sha256",
        label="SHA256 full file checksum",
        usesMethod=method_sha256.id,
    )

    assert dtype.label == "SHA256 full file checksum"
    assert dtype.id == "https://example.com/sha256"


