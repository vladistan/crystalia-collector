import contextlib
import getpass
import json
import os
import socket
import tempfile
import uuid
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import sentry_sdk
import structlog

from crystalia_collector import __version__
from crystalia_collector.method import method_by_id
from crystalia_collector.method.bookend import BookendBase, BookendDirBase
from crystalia_collector.method.generic import GenericMethod
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.monitoring import init_monitoring, trace_context
from crystalia_collector.s3_iface import S3Object, compute_s3_checksum, list_files_in_s3_prefix
from crystalia_collector.source import FileObject, detect_source
from crystalia_collector.util import human_readable_size, process_file, stream_offsets, write_task_file
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor, HarvestRecord, Item, Method
from crystalia_data_model.types.coverage import mint_md5_chunked
from crystalia_data_model.types.leaves import mint_md5, mint_md5_region, mint_relpath
from crystalia_data_model.types.provenance import mint_method, record_harvest
from crystalia_data_model.types.registry import default_registry
from crystalia_data_model.types.validate import ensure_valid

_dm_registry = default_registry()

log = structlog.get_logger()


class HarvestIncompleteError(Exception):
    """A harvest ended without every expected byte or file hashed (fail-closed, Ph5)."""


# Descriptor type for a file's path relative to the scan root. This is location
# metadata and is deliberately NOT folded into any content-composite hash, so
# content descriptor IDs stay stable and identical files in different directories
# still share content IDs.
_TYPE_RELPATH = "crys:dtype/relpath"


@dataclass
class RunResult:
    total: int
    succeeded: int
    failed: int


def _mint_from_task_line(line: str) -> tuple[str, Descriptor]:
    # The URI is field 0 and may contain spaces (real filenames routinely do); the
    # trailing 4 fields (size, method id, block size, offset) never do, so split
    # from the right to keep the URI intact regardless of its content.
    uri, size_str, _method_id, block_size_str, offset_str = line.strip().rsplit(maxsplit=4)
    file_size = int(size_str)
    block_size = int(block_size_str)
    offset = int(offset_str)
    true_length = min(block_size, file_size - offset) if block_size > 0 else file_size
    with sentry_sdk.start_span(op="file.read", name=uri):
        source = detect_source(uri)
        checksum = source.compute_checksum(uri, offset, true_length if block_size > 0 else None)
        descriptor = (
            mint_md5_region(offset, true_length, checksum) if block_size > 0 else mint_md5(checksum, length=file_size)
        )
    return uri, descriptor


def _process_task_file(task_file_path: str) -> list[tuple[str, Descriptor]]:
    results: list[tuple[str, Descriptor]] = []
    with open(task_file_path) as f:
        for line in f:
            if not line.strip():
                continue
            results.append(_mint_from_task_line(line))
    return results


def _process_task_file_traced(
    task_file_path: str,
    dsn: str | None,
    headers: dict[str, str] | None,
) -> list[tuple[str, Descriptor]]:
    """Run `_process_task_file` in a worker, joined to the parent's trace."""
    if not headers:
        return _process_task_file(task_file_path)
    if not sentry_sdk.get_client().is_active():
        init_monitoring(dsn=dsn)
    transaction = sentry_sdk.continue_trace(headers, op="task_file.worker", name=Path(task_file_path).name)
    try:
        with sentry_sdk.start_transaction(transaction):
            return _process_task_file(task_file_path)
    finally:
        sentry_sdk.flush()


def _process_task_file_tolerant(task_file_path: str) -> tuple[list[tuple[str, Descriptor]], list[str]]:
    """Per-line fault-tolerant task-file processing for ``annotate`` (Ph5).

    One bad line does not lose the rest. Returns (results, raw failed lines) so a
    failure can be reported as a re-feedable patch-up manifest.
    """
    results: list[tuple[str, Descriptor]] = []
    failed_lines: list[str] = []
    with open(task_file_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                results.append(_mint_from_task_line(line))
            except Exception as exc:
                log.error("task_line_failed", line=line.strip(), error=str(exc))
                failed_lines.append(line.rstrip("\n"))
    return results, failed_lines


def write_sidecar(sidecar_path: Path, entries: list[tuple[str, Descriptor]]) -> Path:
    """Write a (dir, name, child IRI) sidecar per annotated entry (Ph9 Step 9.1).

    RDF carries no rollup (name, child) pairs (DM consumer contract, known deviation
    1), so `merge` reads this to reconstruct directory membership.
    """
    with open(sidecar_path, "w") as f:
        for uri, desc in entries:
            p = Path(uri)
            f.write(f"{p.parent}\t{p.name}\t{desc.id}\n")
    return sidecar_path


def _assemble_region_composite(uri: str, parts: list[Descriptor]) -> Descriptor:
    """Assemble ordered chunk parts into one region composite (Ph5 Step 5.1).

    Requires the parts to cover offsets ``0..size`` exactly once; a gap or
    overlap is a broken harvest, not a publishable descriptor state.
    """
    ordered = sorted(parts, key=lambda d: int(d.offset))
    expected_offset = 0
    for part in ordered:
        if int(part.offset) != expected_offset:
            msg = f"{uri}: chunk region gap/overlap at offset {part.offset}, expected {expected_offset}"
            raise HarvestIncompleteError(msg)
        expected_offset += int(part.length)
    return mint_md5_chunked(len(ordered), ordered)


def write_partials_manifest(
    partials_dir: Path,
    output_path: Path,
    unhashed_lines: list[str],
    completed: list[Descriptor],
) -> Path:
    """Write a patch-up manifest for MY-NF-PIPELINE-01 (Ph5 Step 5.3).

    ``unhashed_lines`` are task-file lines directly re-feedable to ``annotate``.
    ``completed`` are the descriptors already minted before the harvest failed.
    Never relayed, uploaded, or written to the central output.
    """
    _validate_partials_dir(partials_dir, output_path)
    partials_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = partials_dir / "partials_manifest.txt"
    with open(manifest_path, "w") as f:
        f.write(f"# unhashed: {len(unhashed_lines)}\n")
        for line in unhashed_lines:
            f.write(f"{line}\n")
        f.write(f"# completed: {len(completed)}\n")
        for desc in completed:
            f.write(f"{desc.id}\t{desc.hasType}\t{desc.value}\n")
    return manifest_path


def _validate_partials_dir(partials_dir: Path, output_path: Path) -> None:
    if str(partials_dir).startswith("s3:"):
        msg = "--partials-dir does not support S3 URIs"
        raise ValueError(msg)
    resolved_partials = Path(partials_dir).resolve()
    resolved_output = Path(output_path).resolve()
    if resolved_partials == resolved_output or resolved_output.is_relative_to(resolved_partials):
        msg = f"--partials-dir ({partials_dir}) may not equal or contain the output path ({output_path})"
        raise ValueError(msg)


_LISTING_MANIFEST_NAME = "listing_manifest.json"


def write_listing_manifest(task_dir: Path, dir_counts: dict[str, int]) -> Path:
    """Write, per directory, the expected entry count from a `list` pass (Ph9 Step 9.1).

    `merge` reads this to detect a partition harvest short of what the listing found.
    """
    task_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = task_dir / _LISTING_MANIFEST_NAME
    manifest_path.write_text(json.dumps(dir_counts, sort_keys=True, indent=2))
    return manifest_path


def load_listing_manifest(manifest_path: Path) -> dict[str, int]:
    data: dict[str, int] = json.loads(manifest_path.read_text())
    return data


def list_s3_dir(prefix: str, method_id: str, task_dir: Path | None) -> tuple[int, int]:
    bucket, prefix = prefix.split("/", 1)

    total_size, num_files, task_num = 0, 0, 1
    small_files: list[S3Object] = []
    method = method_by_id(method_id)
    dir_counts: dict[str, int] = defaultdict(int)

    for file in list_files_in_s3_prefix(bucket, prefix):
        size_str = human_readable_size(file.size)
        log.info(
            "s3_object_found",
            bucket=bucket,
            key=file.key,
            size=size_str,
            last_modified=file.last_modified.strftime("%Y-%m-%d"),
            etag=file.etag,
        )
        total_size += file.size
        num_files += 1
        dir_counts[f"s3://{bucket}/{str(Path(file.key).parent)}"] += 1

        if task_dir:
            task_num = process_file(
                bucket,
                file,
                method,
                task_dir,
                task_num,
                small_files,
            )

    if task_dir:
        write_task_file(task_dir, task_num, method, bucket, small_files)
        write_listing_manifest(task_dir, dict(dir_counts))

    return num_files, total_size


def list_dir(
    prefix: str,
    method_id: str,
    task_dir: Path | None,
    exclude: list[str] | None = None,
) -> tuple[int, int]:
    method = method_by_id(method_id)

    if isinstance(method, GlimpseDirBase):
        return _list_dir_glimpse_dirs(prefix, method, task_dir, exclude)
    if isinstance(method, GlimpseBase):
        return _list_dir_glimpse_files(prefix, method, exclude)
    if isinstance(method, BookendDirBase):
        return _list_dir_bookend_dirs(prefix, method, exclude)
    if isinstance(method, BookendBase):
        return _list_dir_bookend_files(prefix, method, exclude)

    source = detect_source(prefix)
    total_size, num_files, task_num = 0, 0, 1
    small_files: list[FileObject] = []
    dir_counts: dict[str, int] = defaultdict(int)

    for file_obj in source.list_files(prefix, exclude):
        log.info(
            "file_found",
            uri=file_obj.uri,
            basename=file_obj.basename,
            size=human_readable_size(file_obj.size),
        )
        total_size += file_obj.size
        num_files += 1
        dir_counts[str(Path(file_obj.uri).parent)] += 1

        if task_dir:
            task_num = _process_file_object(file_obj, method, task_dir, task_num, small_files)

    if task_dir and small_files:
        _write_task_entries(task_dir, task_num, method, small_files)

    if task_dir:
        write_listing_manifest(task_dir, dict(dir_counts))

    return num_files, total_size


def _list_dir_glimpse_files(
    prefix: str,
    method: GlimpseBase,
    exclude: list[str] | None = None,
) -> tuple[int, int]:
    """Scan files with a Glimpse file method and log descriptor summaries."""
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_files

    source = detect_source(prefix)
    results = scan_files(prefix, source, method, exclude)
    total_size = 0
    for file_obj, top, _ in results:
        log.info(
            "glimpse_file",
            uri=file_obj.uri,
            basename=file_obj.basename,
            method=method.id,
            descriptor_id=top.id,
            value=top.value,
        )
        total_size += file_obj.size
    return len(results), total_size


def _list_dir_glimpse_dirs(
    prefix: str,
    method: GlimpseDirBase,
    task_dir: Path | None,
    exclude: list[str] | None = None,
) -> tuple[int, int]:
    """Scan files and directories with a Glimpse dir method and log directory descriptors."""
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_with_dirs

    file_method_raw = method_by_id(method.paired_file_method_id)
    if not isinstance(file_method_raw, GlimpseBase):
        msg = f"Paired file method {method.paired_file_method_id!r} is not a GlimpseBase"
        raise ValueError(msg)

    source = detect_source(prefix)
    file_results, dir_results = scan_with_dirs(prefix, source, file_method_raw, method, exclude)

    total_size = sum(r[0].size for r in file_results)

    for dir_uri, top, _ in dir_results:
        log.info(
            "glimpse_dir",
            uri=dir_uri,
            method=method.id,
            descriptor_id=top.id,
            value=top.value,
        )

    return len(file_results), total_size


def _build_bookend_family_descriptor(
    file_obj: FileObject,
    source: object,
    method: BookendBase,
) -> tuple[Descriptor, list[Descriptor]] | None:
    # local import: defers the bookend/zip stack until a bookend-family method runs
    from crystalia_collector.bookend_compute import (
        build_bookend_descriptor,
        build_zip_cd_descriptor,
        build_zip_manifest_descriptor,
    )

    if method.id == "zip-cd":
        desc = build_zip_cd_descriptor(file_obj, source)  # type: ignore[arg-type]
        return (desc, []) if desc is not None else None
    if method.id == "zip-manifest":
        desc = build_zip_manifest_descriptor(file_obj, source)  # type: ignore[arg-type]
        return (desc, []) if desc is not None else None
    return build_bookend_descriptor(file_obj, source)  # type: ignore[arg-type]


def _list_dir_bookend_files(
    prefix: str,
    method: BookendBase,
    exclude: list[str] | None = None,
) -> tuple[int, int]:
    """Scan files with a bookend-family file method and log descriptor summaries."""
    source = detect_source(prefix)
    total_size, num_files = 0, 0
    for file_obj in source.list_files(prefix, exclude):
        result = _build_bookend_family_descriptor(file_obj, source, method)
        if result is not None:
            top, _children = result
            log.info(
                "bookend_file",
                uri=file_obj.uri,
                basename=file_obj.basename,
                method=method.id,
                descriptor_id=top.id,
                value=top.value,
            )
        total_size += file_obj.size
        num_files += 1
    return num_files, total_size


def _list_dir_bookend_dirs(
    prefix: str,
    method: BookendDirBase,
    exclude: list[str] | None = None,
) -> tuple[int, int]:
    """Scan files and directories with the bookend-dir method and log directory descriptors."""
    # local import: defers the bookend scanning stack until bookend-dir runs
    from crystalia_collector.bookend_scanner import scan_bookend_dirs

    source = detect_source(prefix)
    file_results, dir_results = scan_bookend_dirs(prefix, source, exclude)

    total_size = sum(r[0].size for r in file_results)

    for dir_uri, top, _ in dir_results:
        log.info(
            "bookend_dir",
            uri=dir_uri,
            method=method.id,
            descriptor_id=top.id,
            value=top.value,
        )

    return len(file_results), total_size


def _process_file_object(
    file_obj: FileObject,
    method: GenericMethod,
    task_dir: Path,
    task_num: int,
    small_files: list[FileObject],
) -> int:
    if file_obj.size < (2**24) or file_obj.size < method.block_size / 2:
        small_files.append(file_obj)
    elif not method.needs_offsets:
        _write_task_entries(task_dir, task_num, method, file_obj)
        task_num += 1
    else:
        for offset in stream_offsets(method.block_size, file_obj.size):
            _write_task_entries(task_dir, task_num, method, file_obj, offset)
            task_num += 1
    return task_num


def _write_task_entries(
    task_dir: Path,
    task_num: int,
    method: GenericMethod,
    content: FileObject | list[FileObject],
    offset: int = 0,
) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    with open(f"{task_dir}/task_{task_num}", "w") as f:

        def write_obj(obj: FileObject) -> None:
            f.write(f"{obj.uri} {obj.size} {method.id} {method.block_size} {offset}\n")

        if isinstance(content, list):
            for obj in content:
                write_obj(obj)
        else:
            write_obj(content)


def combine_descriptors(
    items: list[Item],
    output_path: Path,
    fmt: str,
    descriptors: list[Descriptor] | None = None,
    harvest_record: HarvestRecord | None = None,
    methods: list[Method] | None = None,
) -> None:
    # local imports: defer the heavy RDF stack (rdflib + linkml_runtime) until
    # turtle output is actually requested, keeping CLI startup fast.
    from rdflib import Graph

    from crystalia_collector.rdf import rdf_from_model

    sorted_items = sorted(items, key=lambda item: str(item.id))
    log.info("combining_descriptors", num_items=len(items), output=str(output_path), fmt=fmt)

    if fmt == "turtle":
        combined = Graph()
        for item in sorted_items:
            g = rdf_from_model(item)
            for prefix, ns in g.namespaces():
                combined.bind(prefix, ns)
            for triple in g:
                combined.add(triple)
        if descriptors:
            by_id = {str(d.id): d for d in descriptors}

            def resolve(iri: str) -> Descriptor:
                return by_id[iri]

            for desc in descriptors:
                # Only types the DM registry knows are checked here; methods not yet
                # migrated to DM minting (md5-chunk, relpath) mint their own IRIs (Ph1 note).
                if desc.hasType in _dm_registry:
                    ensure_valid(desc, resolve=resolve)
                g = rdf_from_model(desc)
                for prefix, ns in g.namespaces():
                    combined.bind(prefix, ns)
                for triple in g:
                    combined.add(triple)
        for method in methods or []:
            g = rdf_from_model(method)
            for prefix, ns in g.namespaces():
                combined.bind(prefix, ns)
            for triple in g:
                combined.add(triple)
        if harvest_record is not None:
            g = rdf_from_model(harvest_record)
            for prefix, ns in g.namespaces():
                combined.bind(prefix, ns)
            for triple in g:
                combined.add(triple)
        output_path.write_text(combined.serialize(format="turtle"))
    elif fmt == "text":
        with open(output_path, "w") as f:
            for item in sorted_items:
                for desc_id in item.hasDescriptor:
                    f.write(f"{item.id}  {desc_id}\n")
    else:
        msg = f"Unsupported format: {fmt}"
        raise ValueError(msg)

    log.info("combine_complete", num_items=len(sorted_items), output=str(output_path))


def _run_md5_pipeline(
    prefix: str,
    method_id: str,
    workers: int,
    progress_callback: Callable[[int], None] | None,
    exclude: list[str] | None = None,
) -> tuple[dict[str, Descriptor], list[Descriptor], list[str], int, int, list[str]]:
    method = method_by_id(method_id)
    with tempfile.TemporaryDirectory() as temp_dir:
        task_dir_path = Path(temp_dir)
        num_files, _total_size = list_dir(prefix, method_id, task_dir_path, exclude)

        task_files = sorted(task_dir_path.glob("task_*"))
        log.info("tasks_generated", num_tasks=len(task_files), num_files=num_files)

        all_results: list[tuple[str, Descriptor]] = []
        succeeded = 0
        failed = 0
        failed_lines: list[str] = []

        if task_files:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                dsn = sentry_sdk.get_client().dsn
                spans = {}
                futures = {}
                for tf in task_files:
                    span = sentry_sdk.start_span(op="task_file", name=tf.name)
                    future = executor.submit(_process_task_file_traced, str(tf), dsn, trace_context(span))
                    futures[future] = tf
                    spans[future] = span
                for future in as_completed(futures):
                    span = spans[future]
                    try:
                        results = future.result()
                        all_results.extend(results)
                        succeeded += len(results)
                        if progress_callback:
                            progress_callback(len(results))
                    except Exception as exc:
                        span.set_status("internal_error")
                        failed += 1
                        tf_path = futures[future]
                        with contextlib.suppress(OSError):
                            failed_lines.extend(line.rstrip("\n") for line in tf_path.read_text().splitlines())
                        log.error("task_failed", task_file=str(tf_path), error=str(exc))
                    finally:
                        span.finish()

        by_uri: dict[str, list[Descriptor]] = defaultdict(list)
        for uri, descriptor in all_results:
            by_uri[uri].append(descriptor)

        top_by_uri: dict[str, Descriptor] = {}
        extra_descriptors: list[Descriptor] = []
        if method.needs_offsets:
            for uri, parts in by_uri.items():
                composite = _assemble_region_composite(uri, parts)
                top_by_uri[uri] = composite
                extra_descriptors.append(composite)
                extra_descriptors.extend(parts)
        else:
            for uri, parts in by_uri.items():
                (part,) = parts
                top_by_uri[uri] = part
                extra_descriptors.append(part)

        return top_by_uri, extra_descriptors, list(by_uri), succeeded, failed, failed_lines


def _collect_glimpse(
    prefix: str,
    method: GlimpseBase,
    exclude: list[str] | None = None,
) -> tuple[dict[str, list[Descriptor]], list[Descriptor]]:
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_files

    source = detect_source(prefix)
    results = scan_files(prefix, source, method, exclude)

    by_uri: dict[str, list[Descriptor]] = {}
    extra_descriptors: list[Descriptor] = []
    for file_obj, top, children in results:
        by_uri[file_obj.uri] = [top]
        extra_descriptors.append(top)
        extra_descriptors.extend(children)
    return by_uri, extra_descriptors


def _collect_glimpse_dir(
    prefix: str,
    method: GlimpseDirBase,
    exclude: list[str] | None = None,
) -> tuple[dict[str, list[Descriptor]], dict[str, list[Descriptor]], list[Descriptor]]:
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_with_dirs

    file_method_raw = method_by_id(method.paired_file_method_id)
    if not isinstance(file_method_raw, GlimpseBase):
        msg = f"Paired file method {method.paired_file_method_id!r} is not a GlimpseBase"
        raise ValueError(msg)

    source = detect_source(prefix)
    file_results, dir_results = scan_with_dirs(prefix, source, file_method_raw, method, exclude)

    file_descs: dict[str, list[Descriptor]] = {}
    dir_descs: dict[str, list[Descriptor]] = {}
    extra_descriptors: list[Descriptor] = []

    for file_obj, top, children in file_results:
        file_descs[file_obj.uri] = [top]
        extra_descriptors.append(top)
        extra_descriptors.extend(children)

    for dir_uri, top, children in dir_results:
        dir_descs[dir_uri] = [top]
        extra_descriptors.append(top)
        extra_descriptors.extend(children)

    return file_descs, dir_descs, extra_descriptors


def _collect_bookend(
    prefix: str,
    method: BookendBase,
    exclude: list[str] | None = None,
) -> tuple[dict[str, list[Descriptor]], list[Descriptor]]:
    source = detect_source(prefix)
    by_uri: dict[str, list[Descriptor]] = {}
    extra_descriptors: list[Descriptor] = []
    for file_obj in source.list_files(prefix, exclude):
        result = _build_bookend_family_descriptor(file_obj, source, method)
        if result is not None:
            top, children = result
            by_uri[file_obj.uri] = [top]
            extra_descriptors.append(top)
            extra_descriptors.extend(children)
    return by_uri, extra_descriptors


def _collect_bookend_dir(
    prefix: str,
    method: BookendDirBase,
    exclude: list[str] | None = None,
) -> tuple[dict[str, list[Descriptor]], dict[str, list[Descriptor]], list[Descriptor]]:
    # local import: defers the bookend scanning stack until bookend-dir runs
    from crystalia_collector.bookend_scanner import scan_bookend_dirs

    source = detect_source(prefix)
    file_results, dir_results = scan_bookend_dirs(prefix, source, exclude)

    file_descs: dict[str, list[Descriptor]] = {}
    dir_descs: dict[str, list[Descriptor]] = {}
    extra_descriptors: list[Descriptor] = []

    for file_obj, bookend_top, bookend_children, manifest in file_results:
        file_descs[file_obj.uri] = [bookend_top]
        extra_descriptors.append(bookend_top)
        extra_descriptors.extend(bookend_children)
        if manifest is not None:
            extra_descriptors.append(manifest)

    for dir_uri, top, children in dir_results:
        dir_descs[dir_uri] = [top]
        extra_descriptors.append(top)
        extra_descriptors.extend(children)

    return file_descs, dir_descs, extra_descriptors


ItemIdFactory = Callable[[], str]


def invocation_provenance(command: str, **options: object) -> dict[str, str]:
    """`record_harvest` keyword args naming who ran `command`, where, and with which resolved options."""
    return {
        "operator": getpass.getuser(),
        "hostname": socket.gethostname(),
        "cli_options": json.dumps({"command": command, **options}, sort_keys=True),
    }


def _default_item_id() -> str:
    return f"cryd:{uuid.uuid4()}"


def _build_directory_items(
    merged_dirs: dict[str, list[Descriptor]],
    item_id_factory: ItemIdFactory,
    root: str,
    fallback_count: list[int] | None = None,
) -> tuple[list[Item], dict[str, str], list[Descriptor]]:
    """Build directory Items, each with a relpath descriptor and an isPartOf link to
    its parent directory (the scan root's own Item has no isPartOf).

    Returns (items, {dir_uri: item_id}, relpath_descriptors). Sorted iteration order
    guarantees a directory's parent (a strict prefix, thus lexicographically smaller)
    is assigned an item_id before the directory itself is processed.
    """
    dir_item_ids: dict[str, str] = {}
    items: list[Item] = []
    relpath_descriptors: list[Descriptor] = []
    for dir_uri in sorted(merged_dirs):
        basename = Path(dir_uri).name or dir_uri
        item_id = item_id_factory()
        dir_item_ids[dir_uri] = item_id

        parent_dir = str(Path(dir_uri).parent)
        parent_id = dir_item_ids.get(parent_dir)

        relpath_desc = mint_relpath(_relative_path(dir_uri, root, fallback_count))
        relpath_descriptors.append(relpath_desc)

        desc_ids = [d.id for d in merged_dirs[dir_uri]] + [relpath_desc.id]
        items.append(
            Item(id=item_id, label=basename, hasDescriptor=desc_ids, isPartOf=parent_id),
        )
    return items, dir_item_ids, relpath_descriptors


def _relative_path(uri: str, root: str, fallback_count: list[int] | None = None) -> str:
    """Return uri as a POSIX path relative to the scan root, including the basename.

    The run pipeline is local-only, so uri and root are absolute local paths. Both
    are resolved before relative_to: uri always comes pre-resolved from LocalSource,
    but root is the raw CLI argument, so a symlink anywhere in root's path (e.g.
    macOS /tmp -> /private/tmp) would otherwise break the comparison and silently
    fall back to the basename for every item under that root.

    Falls back to the basename if uri is genuinely not under root, logging loudly
    (and incrementing fallback_count, if given) instead of hiding it -- a silent
    fallback here means the resulting Item's relpath wrongly looks like its own
    root, with no signal that anything went wrong.
    """
    try:
        return Path(uri).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        log.warning("relpath_fallback_to_basename", uri=uri, root=root)
        if fallback_count is not None:
            fallback_count[0] += 1
        return Path(uri).name


def _build_file_items(
    merged_files: dict[str, list[Descriptor]],
    dir_item_ids: dict[str, str],
    root: str,
    item_id_factory: ItemIdFactory,
    fallback_count: list[int] | None = None,
) -> tuple[list[Item], list[Descriptor]]:
    """Build file Items, each with a relpath descriptor and an isPartOf link to its parent dir.

    Returns (items, relpath_descriptors). The relpath descriptor carries the file's
    path relative to the scan root as location metadata and is referenced by the
    Item (not by the content descriptor), so content-composite IDs are unaffected.
    """
    items: list[Item] = []
    relpath_descriptors: list[Descriptor] = []
    for uri in sorted(merged_files):
        basename = Path(uri).name
        parent_dir = str(Path(uri).parent)
        parent_id = dir_item_ids.get(parent_dir)

        relpath = _relative_path(uri, root, fallback_count)
        relpath_desc = mint_relpath(relpath)
        relpath_descriptors.append(relpath_desc)

        desc_ids = [d.id for d in merged_files[uri]] + [relpath_desc.id]
        items.append(
            Item(
                id=item_id_factory(),
                label=basename,
                hasDescriptor=desc_ids,
                isPartOf=parent_id,
            ),
        )
    return items, relpath_descriptors


def run_pipeline(
    prefix: str,
    method_ids: list[str],
    output_path: Path,
    workers: int,
    fmt: str,
    verbose: bool = False,
    progress_callback: Callable[[int], None] | None = None,
    item_id_factory: ItemIdFactory | None = None,
    partials_dir: Path | None = None,
    clock: Callable[[], datetime] | None = None,
    source_root: str | None = None,
    exclude: list[str] | None = None,
) -> RunResult:
    log.info("pipeline_start", prefix=prefix, methods=method_ids, workers=workers, fmt=fmt)
    id_factory = item_id_factory or _default_item_id
    now = clock or (lambda: datetime.now(UTC))
    started = now()

    # Collect descriptors per file URI across all methods
    merged_files: dict[str, list[Descriptor]] = defaultdict(list)
    merged_dirs: dict[str, list[Descriptor]] = defaultdict(list)
    all_descriptors: list[Descriptor] = []
    total_succeeded = 0
    total_failed = 0
    total_failed_lines: list[str] = []
    methods: list[Method] = [mint_method(mid, method_by_id(mid).parameters()) for mid in method_ids]

    for method_id in method_ids:
        with sentry_sdk.start_span(op="method", name=method_id) as method_span:
            method_span.set_tag("method", method_id)
            method = method_by_id(method_id)

            if isinstance(method, GlimpseDirBase):
                file_descs, dir_descs, extras = _collect_glimpse_dir(prefix, method, exclude)
                for uri, descs in file_descs.items():
                    merged_files[uri].extend(descs)
                for uri, descs in dir_descs.items():
                    merged_dirs[uri].extend(descs)
                all_descriptors.extend(extras)
                total_succeeded += len(file_descs)
            elif isinstance(method, GlimpseBase):
                by_uri, extras = _collect_glimpse(prefix, method, exclude)
                for uri, descs in by_uri.items():
                    merged_files[uri].extend(descs)
                all_descriptors.extend(extras)
                total_succeeded += len(by_uri)
            elif isinstance(method, BookendDirBase):
                file_descs, dir_descs, extras = _collect_bookend_dir(prefix, method, exclude)
                for uri, descs in file_descs.items():
                    merged_files[uri].extend(descs)
                for uri, descs in dir_descs.items():
                    merged_dirs[uri].extend(descs)
                all_descriptors.extend(extras)
                total_succeeded += len(file_descs)
            elif isinstance(method, BookendBase):
                by_uri, extras = _collect_bookend(prefix, method, exclude)
                for uri, descs in by_uri.items():
                    merged_files[uri].extend(descs)
                all_descriptors.extend(extras)
                total_succeeded += len(by_uri)
            else:
                top_by_uri, extras, _uris, succeeded, failed, failed_lines = _run_md5_pipeline(
                    prefix,
                    method_id,
                    workers,
                    progress_callback,
                    exclude,
                )
                for uri, desc in top_by_uri.items():
                    merged_files[uri].append(desc)
                all_descriptors.extend(extras)
                total_succeeded += succeeded
                total_failed += failed
                total_failed_lines.extend(failed_lines)

    if total_failed > 0:
        if partials_dir:
            write_partials_manifest(partials_dir, output_path, total_failed_lines, all_descriptors)
        msg = f"{total_failed} of {total_succeeded + total_failed} tasks failed; harvest incomplete"
        raise HarvestIncompleteError(msg)

    # Build directory Items first so file Items can reference them via isPartOf
    relpath_fallbacks = [0]
    dir_items, dir_item_ids, dir_relpath_descriptors = _build_directory_items(
        merged_dirs,
        id_factory,
        prefix,
        relpath_fallbacks,
    )
    file_items, relpath_descriptors = _build_file_items(
        merged_files,
        dir_item_ids,
        prefix,
        id_factory,
        relpath_fallbacks,
    )
    items = dir_items + file_items
    all_descriptors.extend(dir_relpath_descriptors)
    all_descriptors.extend(relpath_descriptors)
    roots = [item for item in items if item.isPartOf is None]
    harvest_record = record_harvest(
        started,
        now(),
        __version__,
        source_root or prefix,
        methods=methods,
        roots=roots,
        **invocation_provenance("run", methods=method_ids, workers=workers, format=fmt, exclude=exclude or []),
    )

    tmp_output = output_path.with_name(output_path.name + ".tmp")
    try:
        combine_descriptors(items, tmp_output, fmt, all_descriptors, harvest_record, methods)
    except Exception:
        tmp_output.unlink(missing_ok=True)
        raise
    os.replace(tmp_output, output_path)

    if relpath_fallbacks[0]:
        log.warning("relpath_fallback_total", count=relpath_fallbacks[0], prefix=prefix)

    total = total_succeeded + total_failed
    log.info("pipeline_complete", total=total, succeeded=total_succeeded, failed=total_failed)
    return RunResult(total=total, succeeded=total_succeeded, failed=total_failed)


def compute_annotations(output_file: str, task_file: str) -> None:
    with open(task_file) as f, open(output_file, "w") as out:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                # See _mint_from_task_line: the URI (field 0) may contain spaces,
                # so split from the right to keep it intact.
                file, size_str, _method, block_size_str, offset_str = stripped.rsplit(maxsplit=4)
            except ValueError as exc:
                msg = f"Invalid task line {line!r}: {exc}"
                raise ValueError(msg) from exc
            log.info("annotating_file", file=file)
            bucket, key = file.replace("s3://", "").split("/", 1)
            _size, block_size, offset = int(size_str), int(block_size_str), int(offset_str)

            log.info(
                "computing_file_checksum",
                file=file,
                offset=offset,
                block_size=block_size,
            )
            checksum = compute_s3_checksum(bucket, key, offset, block_size)
            out.write(f"<{file}>  {checksum}\n")
