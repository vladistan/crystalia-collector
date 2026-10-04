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
    def list_files(self, prefix: str, exclude: list[str] | None = None) -> Iterator[FileObject]:
        root = Path(prefix)
        resolved_root = root.resolve()
        excluded_dirs = [Path(e).resolve() for e in exclude] if exclude else []
        for path in root.rglob("*"):
            try:
                if not path.is_file():
                    continue
                resolved = path.resolve()
                if not resolved.is_relative_to(resolved_root):
                    # A symlink inside the tree (e.g. a venv's bin/python) can resolve
                    # to a target outside the scan root entirely. Following it would
                    # pull unrelated files into the harvest and -- since the resolved
                    # path shares no ancestor with root -- make some arbitrary ancestor
                    # directory look like a second scan root.
                    log.warning("local_source_symlink_escapes_root", path=str(path), resolved=str(resolved))
                    continue
                if any(resolved.is_relative_to(ex) for ex in excluded_dirs):
                    continue
                stat = os.stat(path)
            except PermissionError:
                log.warning("local_source_permission_error", path=str(path))
                continue
            yield FileObject(
                uri=str(resolved),
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

    def read_range(self, uri: str, offset: int, length: int) -> bytes:
        with open(uri, "rb") as f:
            f.seek(offset)
            return f.read(length)

    def read_head(self, uri: str, n: int) -> bytes:
        return self.read_range(uri, 0, n)

    def read_tail(self, uri: str, n: int) -> bytes:
        size = os.stat(uri).st_size
        start = max(0, size - n)
        return self.read_range(uri, start, size - start)
