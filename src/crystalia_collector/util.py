from pathlib import Path
from typing import Generator, Any, List, Optional

from crystalia_collector.method.generic import GenericMethod
from crystalia_collector.s3_iface import S3Object


def human_readable_size(size_bytes: int) -> str:
  if size_bytes >= 2 ** 50:
    return f"{size_bytes / (2 ** 50):.1f} PB"
  elif size_bytes >= 2 ** 40:
    return f"{size_bytes / (2 ** 40):.1f} TB"
  elif size_bytes >= 2 ** 30:
    return f"{size_bytes / (2 ** 30):.1f} GB"
  elif size_bytes >= 2 ** 20:
    return f"{size_bytes / (2 ** 20):.1f} MB"
  elif size_bytes >= 2 ** 10:
    return f"{size_bytes / (2 ** 10):.1f} KB"
  else:
    return f"{size_bytes}"


def stream_offsets(blocksize: int, length: int) -> Generator[int, None, None]:
  for offset in range(0, length, blocksize):
    yield offset


def process_file(
  bucket: str,
  file: S3Object,
  method: GenericMethod,
  task_dir: Path,
  task_num: int,
  small_files: List[S3Object],
) -> int:
  if file.size < (2 ** 24) or file.size < method.block_size / 2:
    small_files.append(file)
  elif method.block_size == 0:
    write_task_file(task_dir, task_num, method, bucket, file)
    task_num += 1
  else:
    for offset in stream_offsets(method.block_size, file.size):
      write_task_file(task_dir, task_num, method, bucket, file, offset)
      task_num += 1

  return task_num


def write_task_file(
  task_dir: Path,
  task_num: int,
  method: GenericMethod,
  bucket: str,
  content: S3Object | List[S3Object],
  offset: int = 0,
) -> None:

  task_dir.mkdir(parents=True, exist_ok=True)
  with open(f"{task_dir}/task_{task_num}", "w") as f:
    def write_obj(obj):
      f.write(f"s3://{bucket}/{obj.key} {obj.size} {method.id} {method.block_size} {offset}\n")

    if isinstance(content, list):
        for obj in content:
            write_obj(obj)
    else:
        write_obj(content)
