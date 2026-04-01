from pathlib import Path

import structlog

from crystalia_collector.method import method_by_id
from crystalia_collector.method.generic import GenericMethod
from crystalia_collector.method.glimpse import GlimpseBase
from crystalia_collector.method.glimpse_dir import GlimpseDirBase
from crystalia_collector.s3_iface import S3Object, compute_s3_checksum, list_files_in_s3_prefix
from crystalia_collector.source import FileObject, detect_source
from crystalia_collector.util import human_readable_size, process_file, stream_offsets, write_task_file

log = structlog.get_logger()


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
    from crystalia_collector.glimpse_scanner import scan_with_dirs
    from crystalia_collector.method import method_by_id as _method_by_id

    file_method_raw = _method_by_id(method.paired_file_method_id)
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
