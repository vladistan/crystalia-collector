import pytest
from pathlib import Path

from crystalia_collector.data.linkml.crystalia import Method, DescriptorRobustness


@pytest.fixture
def test_dir():
  return Path(__file__).parent


@pytest.fixture()
def data_dir(test_dir):
  return Path(test_dir) / "sample_data"


@pytest.fixture()
def work_dir(test_dir):
  return Path(test_dir) / "work_dir"


@pytest.fixture
def short_file_single_descriptor(data_dir):
  return data_dir / "short_file_single_descriptor.ttl"

@pytest.fixture
def s3_bucket():
    return "1000genomes-dragen-v4.0.3"


@pytest.fixture
def s3_prefix():
    return "data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3"


