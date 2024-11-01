import pytest
from pathlib import Path


from crystalia.datamodel.crystalia import Method, DescriptorRobustness


@pytest.fixture
def test_dir():
    return Path(__file__).parent


@pytest.fixture()
def data_dir(test_dir):
    return Path(test_dir) / "sample_data"


@pytest.fixture
def short_file_single_descriptor(data_dir):
    return data_dir / "short_file_single_descriptor.ttl"


@pytest.fixture
def method_sha256():
    return Method(
        id="cryd:sha256",
        label="SHA256",
        robustness=DescriptorRobustness.EXTREMELY_HIGH,
    )
