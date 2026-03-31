"""S3 file-source backend implementing the Source protocol."""

import hashlib
from collections.abc import Iterator
from datetime import datetime

import boto3

from crystalia_collector.source import FileObject


class S3Source:
    def __init__(self) -> None:
        self._client = boto3.client("s3")

    @staticmethod
    def parse_s3_uri(uri: str) -> tuple[str, str]:
        """Split 's3://bucket/key' into (bucket, key)."""
        without_scheme = uri.removeprefix("s3://")
        bucket, _, key = without_scheme.partition("/")
        return bucket, key

    def list_files(self, prefix: str) -> Iterator[FileObject]:
        bucket, key_prefix = self.parse_s3_uri(prefix)
        response = self._client.list_objects_v2(Bucket=bucket, Prefix=key_prefix)

        for obj in response.get("Contents", []):
            yield self._to_file_object(bucket, obj)
        while response.get("IsTruncated", False):
            response = self._client.list_objects_v2(
                Bucket=bucket,
                Prefix=key_prefix,
                ContinuationToken=response["NextContinuationToken"],
            )
            for obj in response.get("Contents", []):
                yield self._to_file_object(bucket, obj)

    def compute_checksum(self, uri: str, offset: int, length: int | None) -> str:
        bucket, key = self.parse_s3_uri(uri)
        hasher = hashlib.md5()

        range_str = f"bytes={offset}-{offset + length - 1}" if length else f"bytes={offset}-"
        response = self._client.get_object(Bucket=bucket, Key=key, Range=range_str)
        for chunk in response["Body"].iter_chunks(chunk_size=8192):
            hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def _to_file_object(bucket: str, obj: dict[str, str | int | datetime]) -> FileObject:
        key = str(obj["Key"])
        return FileObject(
            uri=f"s3://{bucket}/{key}",
            basename=key.rsplit("/", 1)[-1],
            size=int(obj["Size"]),  # type: ignore[arg-type]
            mtime=obj["LastModified"],  # type: ignore[arg-type]
            etag=str(obj["ETag"]),
        )
