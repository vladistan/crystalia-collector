import sys
from enum import IntEnum
from pathlib import Path
from typing import Annotated

import structlog
import typer

from crystalia_collector.config import get_settings
from crystalia_collector.monitoring import configure_logging, init_monitoring
from crystalia_collector.source import detect_source
from crystalia_collector.util import human_readable_size
from crystalia_collector.work import combine_descriptors, compute_annotations, list_dir, run_pipeline

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
    """List files in an S3 bucket or local directory."""
    try:
        num_files, total_size = list_dir(prefix, method_id, task_dir)
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
def checksum(uri: str, offset: int = 0, length: int | None = None) -> None:
    """Compute checksum of a file."""
    try:
        source = detect_source(uri)
        log.info("computing_checksum", uri=uri)
        result = source.compute_checksum(uri, offset, length)
        log.info("checksum_complete", checksum=result)
    except Exception as exc:
        log.error("checksum_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


@app.command()
def combine(
    input_dir: Annotated[Path, typer.Argument(help="Directory containing annotation Turtle files")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output file path")] = Path("catalog.ttl"),
    fmt: Annotated[
        str,
        typer.Option("-f", "--format", help="Output format (turtle or text)"),
    ] = get_settings().default_format,
) -> None:
    """Combine individual annotation files into a single catalog."""
    try:
        from crystalia_data_model.datamodel.linkml_crystalia import Item
        from rdflib import Graph

        from crystalia_collector.rdf import model_from_rdf

        items = []
        for ttl_file in sorted(input_dir.glob("*.ttl")):
            g = Graph()
            g.parse(ttl_file, format="turtle")
            item = model_from_rdf(g, Item)
            items.append(item)

        combine_descriptors(items, output, fmt)
        log.info("combine_complete", output=str(output), num_items=len(items))
    except Exception as exc:
        log.error("combine_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


@app.command()
def run(
    source: Annotated[str, typer.Argument(help="Local directory path to process")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output file path")] = Path("catalog.ttl"),
    method_id: Annotated[
        str,
        typer.Option("--method", help="Checksum method ID"),
    ] = get_settings().default_method_id,
    workers: Annotated[
        int,
        typer.Option("-w", "--workers", help="Number of parallel workers"),
    ] = get_settings().default_workers,
    fmt: Annotated[
        str,
        typer.Option("-f", "--format", help="Output format (turtle or text)"),
    ] = get_settings().default_format,
    fail_fast: Annotated[bool, typer.Option("--fail-fast", help="Stop on first error")] = False,
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Enable verbose per-file logging")] = False,
) -> None:
    """Run the full pipeline: list, process, and combine files into a catalog."""
    if source.startswith("s3://"):
        typer.echo("Error: S3 sources are not supported by the run command. Use list + annotate instead.")
        raise typer.Exit(code=ExitCode.ERROR)

    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn

        console = Console(stderr=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("{task.completed} files"),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task("Processing...", total=None)

            def update_progress(count: int) -> None:
                progress.update(task_id, advance=count)

            result = run_pipeline(
                source,
                method_id,
                output,
                workers,
                fmt,
                fail_fast=fail_fast,
                verbose=verbose,
                progress_callback=update_progress,
            )

        typer.echo(f"Processed {result.succeeded} files, {result.failed} failed, output: {output}")
    except Exception as exc:
        log.error("run_failed", error=str(exc))
        raise typer.Exit(code=ExitCode.ERROR) from exc


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
