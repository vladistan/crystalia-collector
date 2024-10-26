
import typer
import boto3
import hashlib
from typing import Generator, Optional
from pathlib import Path
from crystalia_collector.s3_iface import list_files_in_s3_prefix


def human_readable_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes}"


app = typer.Typer()

@app.command()
def list(prefix: str, task_dir: Optional[str] = None, small_file_threshold: int = 1024*1024) -> None:
    """List files in S3 bucket."""
    bucket, prefix = prefix.split('/', 1)

    total_size = 0
    num_files = 0
    task_num = 1
    small_files = []

    if task_dir:
        Path(task_dir).mkdir(parents=True, exist_ok=True)
    for file in list_files_in_s3_prefix(bucket, prefix):
        size_str = human_readable_size(file.size)
        typer.echo(f's3://{bucket}/{file.key:110}: {size_str:12} {file.last_modified.strftime("%Y-%m-%d")} {file.etag}')
        total_size += file.size
        num_files += 1
        
        if task_dir:
            if file.size < small_file_threshold:
                small_files.append(f's3://{bucket}/{file.key}')
            else:
                with open(f"{task_dir}/task_{task_num}", "w") as f:
                    f.write(f's3://{bucket}/{file.key}')
                task_num += 1
    
    if task_dir:
        with open(f"{task_dir}/task_small", "w") as f:
            f.write("\n".join(small_files))
    typer.echo(f'Total size: {human_readable_size(total_size)} in {num_files} files')


@app.command()
def annotate(task_file: str, output_file: str = "out.rdf") -> None:
    """Annotate files with metadata."""
    with open(task_file, "r") as f, open(output_file, "w") as out:
        for file in f:
            file = file.strip()
            typer.echo(f"Annotating file: {file}")
            bucket, key = file.replace("s3://", "").split("/", 1)
            checksum = compute_s3_checksum(bucket, key, 0, None)
            out.write(f"<{file}>  {checksum}\n")
    
    typer.echo(f"Wrote filenames to output file: {output_file}")
    
    typer.echo("Done annotating files.")


def compute_s3_checksum(bucket_name: str, object_key: str, offset: int = 0, length: Optional[int] = None) -> str:
    s3 = boto3.client('s3')
    hasher = hashlib.md5()

    response = s3.get_object(Bucket=bucket_name, Key=object_key, Range=f'bytes={offset}-{offset + length - 1}' if length else f'bytes={offset}-')
    for chunk in response['Body'].iter_chunks(chunk_size=8192):
        hasher.update(chunk)

    return hasher.hexdigest()


def generate_offsets(blocksize: int, length: int) -> Generator[int, None, None]:
    for offset in range(0, length, blocksize):
        yield offset



@app.command()
def checksum(s3_url: str, offset: int = 0, length: Optional[int] = None) -> None:
    """Compute checksum of a file in S3."""
    bucket, key = s3_url.replace("s3://", "").split("/", 1)
    typer.echo(f"Computing checksum for s3://{bucket}/{key}")
    checksum = compute_s3_checksum(bucket, key, offset, length)
    typer.echo(f"Checksum: {checksum}")



@app.command()
def combine():
    """Combine annotations into a single file."""
    typer.echo("Combining annotations into a single file...")

if __name__ == "__main__":
    app()

