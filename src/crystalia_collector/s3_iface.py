"""Thin facade over source.s3 — preserves the legacy public API.

Callers should continue importing S3Object, list_files_in_s3_prefix, and
compute_s3_checksum from this module.  The real logic now lives in
crystalia_collector.source.s3.S3Source.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from crystalia_collector.source.s3 import S3Source


@dataclass
class S3Object:
    key: str
    last_modified: datetime
    etag: str
    size: int


def list_files_in_s3_prefix(bucket_name: str, prefix: str) -> Iterator[S3Object]:
    source = S3Source()
    for file_obj in source.list_files(f"s3://{bucket_name}/{prefix}"):
        yield S3Object(
            key=file_obj.uri.removeprefix(f"s3://{bucket_name}/"),
            last_modified=file_obj.mtime,
            etag=file_obj.etag or "",
            size=file_obj.size,
        )


def compute_s3_checksum(
    bucket_name: str,
    object_key: str,
    offset: int = 0,
    length: int | None = None,
) -> str:
    source = S3Source()
    return source.compute_checksum(f"s3://{bucket_name}/{object_key}", offset, length)
