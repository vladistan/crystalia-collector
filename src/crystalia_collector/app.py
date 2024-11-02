import typer
import boto3
import hashlib
from typing import List, Optional
from pathlib import Path
from crystalia_collector.s3_iface import list_files_in_s3_prefix
from crystalia_collector.util import human_readable_size, stream_offsets

GB = 2**30

app = typer.Typer()


@app.command()
def list(
    prefix: str,
    task_dir: Optional[str] = None,
    block_size: int = 8 * GB,
    use_offsets: bool = False,
) -> None:
    """List files in S3 bucket."""
    bucket, prefix = prefix.split("/", 1)

    total_size, num_files, task_num = 0, 0, 1
    small_files: List[str] = []

    if task_dir:
        Path(task_dir).mkdir(parents=True, exist_ok=True)

    for file in list_files_in_s3_prefix(bucket, prefix):
        size_str = human_readable_size(file.size)
        print(
            f's3://{bucket}/{file.key:110}: {size_str:12} {file.last_modified.strftime("%Y-%m-%d")} {file.etag}',
        )
        total_size += file.size
        num_files += 1

        if task_dir:
            total_size, task_num = process_file(
                file,
                bucket,
                task_dir,
                block_size,
                task_num,
                small_files,
                total_size,
                use_offsets,
            )

    if task_dir:
        with open(f"{task_dir}/task_small", "w") as f:
            f.write("\n".join(small_files))

    print(f"Total size: {human_readable_size(total_size)} in {num_files} files")


def process_file(
    file: Any,  # Replace Any with the appropriate type if known
    bucket: str,
    task_dir: str,
    blocksize: int,
    task_num: int,
    small_files: List[str],
    total_size: int,
    use_offsets: bool,
) -> tuple[int, int]:
    if file.size < blocksize / 2:
        small_files.append(f"s3://{bucket}/{file.key} {file.size}")
    else:
        if use_offsets:
            for offset in stream_offsets(blocksize, file.size):
                write_task_file(
                    task_dir,
                    task_num,
                    bucket,
                    file.key,
                    file.size,
                    offset,
                    blocksize,
                )
                task_num += 1
        else:
            write_task_file(task_dir, task_num, bucket, file.key, file.size)
            task_num += 1
    return total_size, task_num


def write_task_file(
    task_dir: str,
    task_num: int,
    bucket: str,
    file_key: str,
    file_size: int,
    offset: Optional[int] = None,
    blocksize: Optional[int] = None,
) -> None:
    with open(f"{task_dir}/task_{task_num}", "w") as f:
        if offset is not None and blocksize is not None:
            f.write(f"s3://{bucket}/{file_key} {file_size} {offset} {blocksize}")
        else:
            f.write(f"s3://{bucket}/{file_key} {file_size}")


@app.command()
def annotate(task_file: str, output_file: str = "out.rdf") -> None:
    """Annotate files with metadata."""
    with open(task_file, "r") as f, open(output_file, "w") as out:
        for line in f:
            components = line.strip().split()
            file = components[0]
            print(f"Annotating file: {file}")
            bucket, key = file.replace("s3://", "").split("/", 1)

            if len(components) == 4:
                size = int(components[1])
                offset = int(components[2])
                blocksize = int(components[3])
            elif len(components) == 2:
                size = int(components[1])
                offset = 0
                blocksize = None
            else:
                raise ValueError(
                    f"Invalid number of components: {len(components)} for file {file} line {line}",
                )

            print(
                f"Computing checksum for {file} with offset {offset} and blocksize {blocksize}",
            )
            checksum = compute_s3_checksum(bucket, key, offset, blocksize)
            out.write(f"<{file}>  {checksum}\n")

    print(f"Wrote filenames to output file: {output_file}")


def compute_s3_checksum(
    bucket_name: str,
    object_key: str,
    offset: int = 0,
    length: Optional[int] = None,
) -> str:
    s3 = boto3.client("s3")
    hasher = hashlib.md5()

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key,
        Range=f"bytes={offset}-{offset + length - 1}" if length else f"bytes={offset}-",
    )
    for chunk in response["Body"].iter_chunks(chunk_size=8192):
        hasher.update(chunk)

    return hasher.hexdigest()


@app.command()
def checksum(s3_url: str, offset: int = 0, length: Optional[int] = None) -> None:
    """Compute checksum of a file in S3."""
    bucket, key = s3_url.replace("s3://", "").split("/", 1)
    print(f"Computing checksum for s3://{bucket}/{key}")
    checksum = compute_s3_checksum(bucket, key, offset, length)
    print(f"Checksum: {checksum}")


@app.command()
def combine() -> None:
    """Combine annotations into a single file."""
    print("Combining annotations into a single file...")


if __name__ == "__main__":
    app()
