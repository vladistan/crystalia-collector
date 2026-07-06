"""Scan a prefix and build Glimpse descriptors for all files and directories."""

import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from crystalia_collector.glimpse_compute import build_file_descriptor
from crystalia_collector.glimpse_dir_compute import build_dir_descriptor
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.source import FileObject, Source
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor

# Alias: (basename, top-level descriptor) pair used for rollup inputs
ChildEntry = tuple[str, Descriptor]


def _parent_uri(uri: str) -> str:
    """Return the parent directory URI (local or S3), without trailing slash."""
    if uri.startswith("s3://"):
        return uri.rsplit("/", 1)[0]
    return str(Path(uri).parent)


def _dir_basename(dir_uri: str) -> str:
    """Return just the directory name, stripped of path prefix."""
    if dir_uri.startswith("s3://"):
        return dir_uri.rstrip("/").rsplit("/", 1)[-1]
    return Path(dir_uri).name or dir_uri


def _dir_mtime(dir_uri: str, fallback_children: list[FileObject]) -> datetime:
    """Mtime for a directory: real stat on local, max-child-mtime on S3."""
    if dir_uri.startswith("s3://"):
        if not fallback_children:
            return datetime.fromtimestamp(0, UTC)
        return max(fo.mtime for fo in fallback_children)
    return datetime.fromtimestamp(os.stat(dir_uri).st_mtime, UTC)


def _ancestor_uris(uri: str, root_prefix: str) -> list[str]:
    """Return all ancestor directory URIs from uri up to (not including) root_prefix."""
    ancestors: list[str] = []
    current = uri
    while True:
        parent = _parent_uri(current)
        if parent == current or len(parent) < len(root_prefix):
            break
        if parent not in ancestors:
            ancestors.append(parent)
        current = parent
    return ancestors


def scan_files(
    prefix: str,
    source: Source,
    file_method: GlimpseBase,
) -> list[tuple[FileObject, Descriptor, list[Descriptor]]]:
    """Compute Glimpse file descriptors for all files under prefix."""
    results: list[tuple[FileObject, Descriptor, list[Descriptor]]] = []
    for file_obj in source.list_files(prefix):
        top, children = build_file_descriptor(file_obj, file_method, source)
        results.append((file_obj, top, children))
    return results


def scan_with_dirs(
    prefix: str,
    source: Source,
    file_method: GlimpseBase,
    dir_method: GlimpseDirBase,
) -> tuple[
    list[tuple[FileObject, Descriptor, list[Descriptor]]],
    list[tuple[str, Descriptor, list[Descriptor]]],
]:
    """Compute Glimpse file and directory descriptors for all items under prefix.

    Directories are processed bottom-up so that parent rollups include child
    directory descriptors. Returns:
        file_results: (file_obj, top_descriptor, child_descriptors) per file
        dir_results:  (dir_uri, top_descriptor, child_metadata_descriptors), leaf-first
    """
    # Step 1: compute all file descriptors
    file_results: list[tuple[FileObject, Descriptor, list[Descriptor]]] = []
    for file_obj in source.list_files(prefix):
        top, children = build_file_descriptor(file_obj, file_method, source)
        file_results.append((file_obj, top, children))

    # Step 2: collect direct children (files) grouped by parent directory URI
    # basename is stripped of path prefix per design spec
    dir_file_children: dict[str, list[tuple[str, Descriptor, FileObject]]] = defaultdict(list)
    all_dir_uris: set[str] = set()

    for file_obj, file_top, _ in file_results:
        parent = _parent_uri(file_obj.uri)
        dir_file_children[parent].append((file_obj.basename, file_top, file_obj))
        all_dir_uris.add(parent)
        for ancestor in _ancestor_uris(file_obj.uri, prefix):
            all_dir_uris.add(ancestor)

    # Step 3: process directories deepest-first (longer URI = deeper in tree)
    sorted_dirs = sorted(all_dir_uris, key=len, reverse=True)

    # Holds already-computed dir top descriptors for use in parent rollups
    computed_dir_tops: dict[str, Descriptor] = {}

    dir_results: list[tuple[str, Descriptor, list[Descriptor]]] = []

    for dir_uri in sorted_dirs:
        base = _dir_basename(dir_uri)

        # Direct file children of this directory
        file_entries: list[ChildEntry] = [
            (basename, file_top) for (basename, file_top, _) in dir_file_children.get(dir_uri, [])
        ]

        # Direct subdirectory children (already computed, leaf-first ordering ensures this)
        subdir_entries: list[ChildEntry] = [
            (_dir_basename(child_uri), child_top)
            for child_uri, child_top in computed_dir_tops.items()
            if _parent_uri(child_uri) == dir_uri
        ]

        # Merge and sort all direct children by basename
        all_children: list[ChildEntry] = sorted(
            file_entries + subdir_entries,
            key=lambda x: x[0],
        )

        fallback_file_objs = [fo for (_, _, fo) in dir_file_children.get(dir_uri, [])]
        mtime = _dir_mtime(dir_uri, fallback_file_objs)

        top, dir_children = build_dir_descriptor(
            dir_basename=base,
            dir_mtime=mtime,
            method=dir_method,
            child_descriptors=all_children,
        )
        computed_dir_tops[dir_uri] = top
        dir_results.append((dir_uri, top, dir_children))

    return file_results, dir_results
