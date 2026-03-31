import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import boto3


@dataclass
class S3Object:
    key: str
    last_modified: datetime
    etag: str
    size: int


def s3_object_from_dict(obj: dict[str, Any]) -> S3Object:
    return S3Object(
        key=obj["Key"],
        last_modified=obj["LastModified"],
        etag=obj["ETag"],
        size=obj["Size"],
    )


def list_files_in_s3_prefix(bucket_name: str, prefix: str) -> Iterator[S3Object]:
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    for obj in response["Contents"]:
        yield s3_object_from_dict(obj)
    while response["IsTruncated"]:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            ContinuationToken=response["NextContinuationToken"],
        )
        for obj in response["Contents"]:
            yield s3_object_from_dict(obj)


def compute_s3_checksum(
    bucket_name: str,
    object_key: str,
    offset: int = 0,
    length: int | None = None,
) -> str:
    s3 = boto3.client("s3")
    hasher = hashlib.md5()

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key,
        Range=f"bytes={offset}-{offset + length - 1}" if length else f"bytes={offset}-",
    )
    for chunk in response["Body"].iter_chunks(chunk_size=8192):
        hasher.update(chunk)

    return hasher.hexdigest()
