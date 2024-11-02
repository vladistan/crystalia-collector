from pathlib import Path
from typing import List

from crystalia_collector.method.md5 import method_by_id
from crystalia_collector.s3_iface import list_files_in_s3_prefix, compute_s3_checksum, S3Object
from crystalia_collector.util import human_readable_size, process_file, write_task_file


def list_s3_dir(prefix, method_id, task_dir):
  bucket, prefix = prefix.split("/", 1)

  total_size, num_files, task_num = 0, 0, 1
  small_files: List[S3Object] = []
  method = method_by_id(method_id)

  for file in list_files_in_s3_prefix(bucket, prefix):
    size_str = human_readable_size(file.size)
    print(
      f's3://{bucket}/{file.key:110}: {size_str:12} {file.last_modified.strftime("%Y-%m-%d")} {file.etag}',
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


def compute_annotations(output_file, task_file):
  with open(task_file, "r") as f, open(output_file, "w") as out:
    for line in f:
      components = line.strip().split()
      if not components:
        continue
      file = components[0]
      print(f"Annotating file: {file}")
      bucket, key = file.replace("s3://", "").split("/", 1)

      if len(components) == 5:
        size, method, block_size, offset = int(components[1]), components[2], int(components[3]), int(components[4])
      else:
        raise ValueError(
          f"Invalid number of components: {len(components)} for file {file} line {line}",
        )

      print(
        f"Computing checksum for {file} with offset {offset} and blocksize {block_size}",
      )
      checksum = compute_s3_checksum(bucket, key, offset, block_size)
      out.write(f"<{file}>  {checksum}\n")
