import boto3
import botocore.exceptions
import pytest

from crystalia_collector.s3_iface import compute_s3_checksum, list_files_in_s3_prefix


def _has_aws_credentials() -> bool:
    try:
        boto3.client("sts").get_caller_identity()
    except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
        return False
    return True


requires_s3 = pytest.mark.skipif(
    not _has_aws_credentials(),
    reason="AWS credentials not available",
)


@requires_s3
def test_list_files_in_s3_prefix(s3_bucket, s3_prefix):
    files = list(list_files_in_s3_prefix(s3_bucket, s3_prefix))
    assert len(files) > 0
    assert all(file.key.startswith(s3_prefix) for file in files)


@requires_s3
def test_compute_md5_checksum(s3_bucket, s3_prefix):
    obj_key = s3_prefix + "202-samples-cohort/3202_samples_cohort_gg_chr6.vcf.gz"

    checksum = compute_s3_checksum(s3_bucket, obj_key, offset=0, length=1000)
    assert checksum == "0c7f02e17c947b8fca4be152af947a6f"  # pragma: allowlist secret
