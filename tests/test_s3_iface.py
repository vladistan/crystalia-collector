import pytest

from crystalia_collector.s3_iface import list_files_in_s3_prefix, compute_s3_checksum




def test_list_files_in_s3_prefix(s3_bucket, s3_prefix):
    files = list(list_files_in_s3_prefix(s3_bucket, s3_prefix))
    assert len(files) > 0
    assert all(file.key.startswith(s3_prefix) for file in files)

def test_compute_md5_checksum(s3_bucket, s3_prefix):

  obj_key = s3_prefix + '202-samples-cohort/3202_samples_cohort_gg_chr6.vcf.gz'

  checksum = compute_s3_checksum(s3_bucket, obj_key, offset=0, length=1000)
  assert checksum == '0c7f02e17c947b8fca4be152af947a6f'
