from pathlib import Path

import structlog

from crystalia_collector.method.md5 import method_by_id
from crystalia_collector.s3_iface import S3Object, compute_s3_checksum, list_files_in_s3_prefix
from crystalia_collector.util import human_readable_size, process_file, write_task_file

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
