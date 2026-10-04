"""Scan a prefix and build bookend/zip-manifest file descriptors, rolled up via bookend-dir."""

from collections import defaultdict

from crystalia_collector.bookend_compute import build_bookend_descriptor, build_zip_manifest_descriptor
from crystalia_collector.bookend_dir_compute import build_bookend_dir_descriptor
from crystalia_collector.scan_paths import ancestor_uris as _ancestor_uris
from crystalia_collector.scan_paths import dir_basename as _dir_basename
from crystalia_collector.scan_paths import parent_uri as _parent_uri
from crystalia_collector.source import FileObject, Source
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor
from crystalia_data_model.types.bookend import DirEntry

FileResult = tuple[FileObject, Descriptor, list[Descriptor], Descriptor | None]
DirResult = tuple[str, Descriptor, list[Descriptor]]


def scan_bookend_files(prefix: str, source: Source, exclude: list[str] | None = None) -> list[FileResult]:
    """Compute bookend (+ zip-manifest, when applicable) descriptors for all files under prefix."""
    results: list[FileResult] = []
    for file_obj in source.list_files(prefix, exclude):
        bookend_top, bookend_children = build_bookend_descriptor(file_obj, source)
        manifest = build_zip_manifest_descriptor(file_obj, source)
        results.append((file_obj, bookend_top, bookend_children, manifest))
    return results


def scan_bookend_dirs(
    prefix: str,
    source: Source,
    exclude: list[str] | None = None,
) -> tuple[list[FileResult], list[DirResult]]:
    """Compute bookend/zip-manifest file descriptors and bookend-dir rollups, bottom-up.

    Per D-3, each direct child of a directory contributes its zip-manifest (zip family with a
    readable Central Directory), else its own bookend-dir (a subdirectory), else its bookend.
    """
    file_results = scan_bookend_files(prefix, source, exclude)

    dir_file_children: dict[str, list[tuple[str, FileObject, Descriptor, Descriptor | None]]] = defaultdict(list)
    all_dir_uris: set[str] = set()

    for file_obj, bookend_top, _bookend_children, manifest in file_results:
        parent = _parent_uri(file_obj.uri)
        dir_file_children[parent].append((file_obj.basename, file_obj, bookend_top, manifest))
        all_dir_uris.add(parent)
        for ancestor in _ancestor_uris(file_obj.uri, prefix):
            all_dir_uris.add(ancestor)

    sorted_dirs = sorted(all_dir_uris, key=len, reverse=True)
    computed_dir_tops: dict[str, Descriptor] = {}
    dir_results: list[DirResult] = []

    for dir_uri in sorted_dirs:
        entries: list[DirEntry] = [
            DirEntry(name=basename, zip_manifest=manifest, bookend=bookend_top)
            for (basename, _file_obj, bookend_top, manifest) in dir_file_children.get(dir_uri, [])
        ]
        entries += [
            DirEntry(name=_dir_basename(child_uri), bookend_dir=child_top)
            for child_uri, child_top in computed_dir_tops.items()
            if _parent_uri(child_uri) == dir_uri
        ]
        entries.sort(key=lambda e: e.name)

        top = build_bookend_dir_descriptor(len(entries), entries)
        computed_dir_tops[dir_uri] = top
        dir_results.append((dir_uri, top, []))

    return file_results, dir_results
