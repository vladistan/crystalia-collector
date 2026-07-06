import tempfile
import uuid
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import structlog

from crystalia_collector.glimpse_compute import _content_id
from crystalia_collector.method import method_by_id
from crystalia_collector.method.generic import GenericMethod
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.s3_iface import S3Object, compute_s3_checksum, list_files_in_s3_prefix
from crystalia_collector.source import FileObject, detect_source
from crystalia_collector.util import human_readable_size, process_file, stream_offsets, write_task_file
from crystalia_data_model.datamodel.linkml_crystalia import Descriptor, Item

log = structlog.get_logger()


@dataclass
class RunResult:
    total: int
    succeeded: int
    failed: int


def _process_task_file(task_file_path: str) -> list[tuple[str, Descriptor]]:
    results: list[tuple[str, Descriptor]] = []
    with open(task_file_path) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            uri = parts[0]
            size = int(parts[1])
            method_id = parts[2]
            block_size = int(parts[3])
            offset = int(parts[4])
            length = block_size if block_size > 0 else None
            source = detect_source(uri)
            checksum = source.compute_checksum(uri, offset, length)
            coverage = min(block_size / size, 1.0) if block_size > 0 and size > 0 else 1.0
            descriptor = Descriptor(
                id=_content_id(f"cryd:{method_id}", checksum),
                hasType=f"cryd:{method_id}",
                value=checksum,
                offset=offset,
                coverage=coverage,
                length=block_size if block_size > 0 else None,
            )
            results.append((uri, descriptor))
    return results


def list_s3_dir(prefix: str, method_id: str, task_dir: Path | None) -> tuple[int, int]:
    bucket, prefix = prefix.split("/", 1)

    total_size, num_files, task_num = 0, 0, 1
    small_files: list[S3Object] = []
    method = method_by_id(method_id)

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

    return num_files, total_size


def list_dir(prefix: str, method_id: str, task_dir: Path | None) -> tuple[int, int]:
    method = method_by_id(method_id)

    if isinstance(method, GlimpseDirBase):
        return _list_dir_glimpse_dirs(prefix, method, task_dir)
    if isinstance(method, GlimpseBase):
        return _list_dir_glimpse_files(prefix, method)

    source = detect_source(prefix)
    total_size, num_files, task_num = 0, 0, 1
    small_files: list[FileObject] = []

    for file_obj in source.list_files(prefix):
        log.info(
            "file_found",
            uri=file_obj.uri,
            basename=file_obj.basename,
            size=human_readable_size(file_obj.size),
        )
        total_size += file_obj.size
        num_files += 1

        if task_dir:
            task_num = _process_file_object(file_obj, method, task_dir, task_num, small_files)

    if task_dir and small_files:
        _write_task_entries(task_dir, task_num, method, small_files)

    return num_files, total_size


def _list_dir_glimpse_files(prefix: str, method: GlimpseBase) -> tuple[int, int]:
    """Scan files with a Glimpse file method and log descriptor summaries."""
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_files

    source = detect_source(prefix)
    results = scan_files(prefix, source, method)
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
) -> tuple[int, int]:
    """Scan files and directories with a Glimpse dir method and log directory descriptors."""
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_with_dirs

    file_method_raw = method_by_id(method.paired_file_method_id)
    if not isinstance(file_method_raw, GlimpseBase):
        msg = f"Paired file method {method.paired_file_method_id!r} is not a GlimpseBase"
        raise ValueError(msg)

    source = detect_source(prefix)
    file_results, dir_results = scan_with_dirs(prefix, source, file_method_raw, method)

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
            for desc in descriptors:
                g = rdf_from_model(desc)
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
    fail_fast: bool,
    progress_callback: Callable[[int], None] | None,
) -> tuple[dict[str, list[Descriptor]], list[str], int, int]:
    with tempfile.TemporaryDirectory() as temp_dir:
        task_dir_path = Path(temp_dir)
        num_files, _total_size = list_dir(prefix, method_id, task_dir_path)

        task_files = sorted(task_dir_path.glob("task_*"))
        log.info("tasks_generated", num_tasks=len(task_files), num_files=num_files)

        all_results: list[tuple[str, Descriptor]] = []
        succeeded = 0
        failed = 0

        if task_files:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_process_task_file, str(tf)): tf for tf in task_files}
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        all_results.extend(results)
                        succeeded += len(results)
                        if progress_callback:
                            progress_callback(len(results))
                    except Exception as exc:
                        failed += 1
                        if fail_fast:
                            raise
                        log.error("task_failed", task_file=str(futures[future]), error=str(exc))

        by_uri: dict[str, list[Descriptor]] = defaultdict(list)
        for uri, descriptor in all_results:
            by_uri[uri].append(descriptor)

        return by_uri, list(by_uri), succeeded, failed


def _collect_glimpse(
    prefix: str,
    method: GlimpseBase,
) -> tuple[dict[str, list[Descriptor]], list[Descriptor]]:
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_files

    source = detect_source(prefix)
    results = scan_files(prefix, source, method)

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
) -> tuple[dict[str, list[Descriptor]], dict[str, list[Descriptor]], list[Descriptor]]:
    # local import: defers the Glimpse scanning stack until a Glimpse method runs
    from crystalia_collector.glimpse_scanner import scan_with_dirs

    file_method_raw = method_by_id(method.paired_file_method_id)
    if not isinstance(file_method_raw, GlimpseBase):
        msg = f"Paired file method {method.paired_file_method_id!r} is not a GlimpseBase"
        raise ValueError(msg)

    source = detect_source(prefix)
    file_results, dir_results = scan_with_dirs(prefix, source, file_method_raw, method)

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


def _build_directory_items(
    merged_dirs: dict[str, list[Descriptor]],
) -> tuple[list[Item], dict[str, str]]:
    """Build directory Items and return them with a {dir_uri: item_id} map."""
    dir_item_ids: dict[str, str] = {}
    items: list[Item] = []
    for dir_uri in sorted(merged_dirs):
        basename = Path(dir_uri).name or dir_uri
        item_id = f"crys:{uuid.uuid4()}"
        dir_item_ids[dir_uri] = item_id
        desc_ids = [d.id for d in merged_dirs[dir_uri]]
        items.append(Item(id=item_id, label=basename, hasDescriptor=desc_ids))
    return items, dir_item_ids


def _build_file_items(
    merged_files: dict[str, list[Descriptor]],
    dir_item_ids: dict[str, str],
) -> list[Item]:
    """Build file Items, linking each to its parent directory Item via isPartOf."""
    items: list[Item] = []
    for uri in sorted(merged_files):
        basename = Path(uri).name
        parent_dir = str(Path(uri).parent)
        parent_id = dir_item_ids.get(parent_dir)
        desc_ids = [d.id for d in merged_files[uri]]
        items.append(
            Item(
                id=f"crys:{uuid.uuid4()}",
                label=basename,
                hasDescriptor=desc_ids,
                isPartOf=parent_id,
            ),
        )
    return items


def run_pipeline(
    prefix: str,
    method_ids: list[str],
    output_path: Path,
    workers: int,
    fmt: str,
    fail_fast: bool = False,
    verbose: bool = False,
    progress_callback: Callable[[int], None] | None = None,
) -> RunResult:
    log.info("pipeline_start", prefix=prefix, methods=method_ids, workers=workers, fmt=fmt)

    # Collect descriptors per file URI across all methods
    merged_files: dict[str, list[Descriptor]] = defaultdict(list)
    merged_dirs: dict[str, list[Descriptor]] = defaultdict(list)
    all_descriptors: list[Descriptor] = []
    total_succeeded = 0
    total_failed = 0

    for method_id in method_ids:
        method = method_by_id(method_id)

        if isinstance(method, GlimpseDirBase):
            file_descs, dir_descs, extras = _collect_glimpse_dir(prefix, method)
            for uri, descs in file_descs.items():
                merged_files[uri].extend(descs)
            for uri, descs in dir_descs.items():
                merged_dirs[uri].extend(descs)
            all_descriptors.extend(extras)
            total_succeeded += len(file_descs)
        elif isinstance(method, GlimpseBase):
            by_uri, extras = _collect_glimpse(prefix, method)
            for uri, descs in by_uri.items():
                merged_files[uri].extend(descs)
            all_descriptors.extend(extras)
            total_succeeded += len(by_uri)
        else:
            md5_by_uri, _uris, succeeded, failed = _run_md5_pipeline(
                prefix,
                method_id,
                workers,
                fail_fast,
                progress_callback,
            )
            for uri, descs in md5_by_uri.items():
                merged_files[uri].extend(descs)
            all_descriptors.extend(d for descs in md5_by_uri.values() for d in descs)
            total_succeeded += succeeded
            total_failed += failed

    # Build directory Items first so file Items can reference them via isPartOf
    dir_items, dir_item_ids = _build_directory_items(merged_dirs)
    file_items = _build_file_items(merged_files, dir_item_ids)
    items = dir_items + file_items

    combine_descriptors(items, output_path, fmt, all_descriptors)

    total = total_succeeded + total_failed
    log.info("pipeline_complete", total=total, succeeded=total_succeeded, failed=total_failed)
    return RunResult(total=total, succeeded=total_succeeded, failed=total_failed)


def compute_annotations(output_file: str, task_file: str) -> None:
    with open(task_file) as f, open(output_file, "w") as out:
        for line in f:
            components = line.strip().split()
            if not components:
                continue
            file = components[0]
            log.info("annotating_file", file=file)
            bucket, key = file.replace("s3://", "").split("/", 1)

            if len(components) == 5:
                _size, _method, block_size, offset = (
                    int(components[1]),
                    components[2],
                    int(components[3]),
                    int(components[4]),
                )
            else:
                raise ValueError(
                    f"Invalid number of components: {len(components)} for file {file} line {line}",
                )

            log.info(
                "computing_file_checksum",
                file=file,
                offset=offset,
                block_size=block_size,
            )
            checksum = compute_s3_checksum(bucket, key, offset, block_size)
            out.write(f"<{file}>  {checksum}\n")
