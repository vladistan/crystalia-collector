"""Local filesystem backend implementing the Source protocol."""

import hashlib
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import structlog

from crystalia_collector.source import FileObject

log = structlog.get_logger()

_CHUNK_SIZE = 8192


class LocalSource:
    def list_files(self, prefix: str) -> Iterator[FileObject]:
        root = Path(prefix)
        for path in root.rglob("*"):
            try:
                if not path.is_file():
                    continue
                stat = os.stat(path)
            except PermissionError:
                log.warning("local_source_permission_error", path=str(path))
                continue
            yield FileObject(
                uri=str(path.resolve()),
                basename=path.name,
                size=stat.st_size,
                mtime=datetime.fromtimestamp(stat.st_mtime, UTC),
                ctime=datetime.fromtimestamp(stat.st_ctime, UTC),
            )

    def compute_checksum(self, uri: str, offset: int, length: int | None) -> str:
        hasher = hashlib.md5()
        remaining = length
        with open(uri, "rb") as f:
            f.seek(offset)
            while True:
                to_read = min(_CHUNK_SIZE, remaining) if remaining is not None else _CHUNK_SIZE
                chunk = f.read(to_read)
                if not chunk:
                    break
                hasher.update(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
        return hasher.hexdigest()
