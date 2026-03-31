import sys
from enum import IntEnum
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

app = typer.Typer(no_args_is_help=True)


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1


@app.callback()
def main() -> None:
    """Crystalia Collector CLI."""
    settings = get_settings()
    init_monitoring(dsn=settings.sentry_dsn)
    configure_logging(json_output=settings.log_json)


@app.command()
def list(prefix: str, task_dir: Path | None = None, method_id: str = get_settings().default_method_id) -> None:
    """List files in S3 bucket."""
    try:
        num_files, total_size = list_s3_dir(prefix, method_id, task_dir)
        log.info("listing_complete", num_files=num_files, total_size=human_readable_size(total_size))
    except Exception as exc:
        log.error("listing_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


@app.command()
def annotate(task_file: str, output_file: str = get_settings().default_output_file) -> None:
    """Annotate files with metadata."""
    try:
        compute_annotations(output_file, task_file)
        log.info("annotations_complete", output_file=output_file)
    except Exception as exc:
        log.error("annotations_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


@app.command()
def checksum(s3_url: str, offset: int = 0, length: int | None = None) -> None:
    """Compute checksum of a file in S3."""
    try:
        bucket, key = s3_url.replace("s3://", "").split("/", 1)
        log.info("computing_checksum", bucket=bucket, key=key)
        result = compute_s3_checksum(bucket, key, offset, length)
        log.info("checksum_complete", checksum=result)
    except Exception as exc:
        log.error("checksum_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


@app.command()
def combine() -> None:
    """Combine annotations into a single file."""
    log.info("combining_annotations")


@app.command(name="test-sentry")
def test_sentry() -> None:
    """Send a test event to Sentry to verify integration."""
    settings = get_settings()
    if not settings.sentry_dsn:
        typer.echo("SENTRY_DSN is not configured. Set it via CRYSTALIA_SENTRY_DSN or SENTRY_DSN env var.")
        raise typer.Exit(code=ExitCode.ERROR)
    init_monitoring(dsn=settings.sentry_dsn)
    try:
        raise RuntimeError("Sentry test exception from crystalia-collector")
    except RuntimeError:
        import sentry_sdk

        sentry_sdk.capture_exception()
        sentry_sdk.flush()
    typer.echo("Test event sent to Sentry. Check your Sentry dashboard to verify.")
    sys.exit(ExitCode.OK)


if __name__ == "__main__":
    app()
