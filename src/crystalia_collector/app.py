from pathlib import Path

import typer
from typing import Optional

from crystalia_collector.s3_iface import compute_s3_checksum
from crystalia_collector.util import human_readable_size
from crystalia_collector.work import list_s3_dir, compute_annotations

GB = 2 ** 30

app = typer.Typer()


@app.command()
def list(prefix: str, task_dir: Optional[Path] = None, method_id: str = "md5_8gb") -> None:
  """List files in S3 bucket."""
  num_files, total_size = list_s3_dir(prefix, method_id, task_dir)
  print(f"Total size: {human_readable_size(total_size)} in {num_files} files")


@app.command()
def annotate(task_file: str, output_file: str = "out.rdf") -> None:
  """Annotate files with metadata."""
  compute_annotations(output_file, task_file)
  print(f"Wrote filenames to output file: {output_file}")


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
