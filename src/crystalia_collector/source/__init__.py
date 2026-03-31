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
