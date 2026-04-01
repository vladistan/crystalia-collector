"""Source abstraction layer: FileObject model and Source protocol."""

from collections.abc import Iterator
from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class FileObject(BaseModel):
    """Immutable descriptor for a single file, source-agnostic."""

    model_config = ConfigDict(frozen=True)

    uri: str
    basename: str
    size: int
    mtime: datetime
    ctime: datetime | None = None
    etag: str | None = None


@runtime_checkable
class Source(Protocol):
    """Protocol for file-source backends (S3, local, etc.)."""

    def list_files(self, prefix: str) -> Iterator[FileObject]: ...

    def compute_checksum(self, uri: str, offset: int, length: int | None) -> str: ...


def detect_source(location: str) -> Source:
    if location.startswith("s3://"):
        # Lazy import: s3.py imports from this module (circular)
        from crystalia_collector.source.s3 import S3Source

        return S3Source()
    if location.startswith("/"):
        # Lazy import: local.py imports from this module (circular)
        from crystalia_collector.source.local import LocalSource

        return LocalSource()
    msg = f"relative paths not supported: {location}"
    raise ValueError(msg)
