from pathlib import Path

import structlog
import typer

from crystalia_collector.config import get_settings
from crystalia_collector.monitoring import configure_logging, init_monitoring
from crystalia_collector.s3_iface import compute_s3_checksum
from crystalia_collector.util import human_readable_size
from crystalia_collector.work import compute_annotations, list_s3_dir

GB = 2**30

log = structlog.get_logger()

_settings = get_settings()

app = typer.Typer()


@app.callback()
def main() -> None:
    """Crystalia Collector CLI."""
    init_monitoring(dsn=_settings.sentry_dsn)
    configure_logging(json_output=_settings.log_json)


@app.command()
def list(prefix: str, task_dir: Path | None = None, method_id: str = _settings.default_method_id) -> None:
    """List files in S3 bucket."""
    num_files, total_size = list_s3_dir(prefix, method_id, task_dir)
    log.info("listing_complete", num_files=num_files, total_size=human_readable_size(total_size))


@app.command()
def annotate(task_file: str, output_file: str = _settings.default_output_file) -> None:
    """Annotate files with metadata."""
    compute_annotations(output_file, task_file)
    log.info("annotations_complete", output_file=output_file)


@app.command()
def checksum(s3_url: str, offset: int = 0, length: int | None = None) -> None:
    """Compute checksum of a file in S3."""
    bucket, key = s3_url.replace("s3://", "").split("/", 1)
    log.info("computing_checksum", bucket=bucket, key=key)
    result = compute_s3_checksum(bucket, key, offset, length)
    log.info("checksum_complete", checksum=result)


@app.command()
def combine() -> None:
    """Combine annotations into a single file."""
    log.info("combining_annotations")


if __name__ == "__main__":
    app()
