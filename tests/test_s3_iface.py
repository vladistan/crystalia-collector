
import pytest
from crystalia_collector.s3_iface import list_files_in_s3_prefix

@pytest.fixture
def s3_bucket():
    return "1000genomes-dragen-v4.0.3"

@pytest.fixture
def s3_prefix():
    return "data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3"

def test_list_files_in_s3_prefix(s3_bucket, s3_prefix):
    files = list(list_files_in_s3_prefix(s3_bucket, s3_prefix))
    assert len(files) > 0
    assert all(file.key.startswith(s3_prefix) for file in files)
