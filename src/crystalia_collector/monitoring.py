"""Monitoring and structured logging configuration."""

import os
from contextlib import AbstractContextManager

import sentry_sdk
import structlog
from sentry_sdk.tracing import Span

from crystalia_collector import __version__


def init_monitoring(dsn: str | None = None) -> None:
    """Initialize Sentry SDK for crash reporting and performance monitoring."""
    if dsn is None:
        dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.03")),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        release=__version__,
        attach_stacktrace=True,
        send_default_pii=False,
    )


def cli_transaction(command: str) -> AbstractContextManager[object]:
    """Open the root transaction for one CLI invocation."""
    return sentry_sdk.start_transaction(op="cli", name=command)


def mark_active_span_failed() -> None:
    """Flag the active span as failed; the error event then links to it."""
    span = sentry_sdk.get_current_span()
    if span is not None:
        span.set_status("internal_error")


def trace_context(span: Span) -> dict[str, str] | None:
    """Return the headers a subprocess needs to join `span`'s trace, or None."""
    if not sentry_sdk.get_client().is_active():
        return None
    headers = {"sentry-trace": span.to_traceparent()}
    baggage = span.to_baggage()
    if baggage is not None:
        headers["baggage"] = baggage.serialize()
    return headers


def configure_logging(json_output: bool = True) -> None:
    """Configure structlog for structured logging."""
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(processors=processors)
