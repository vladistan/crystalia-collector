"""Monitoring and structured logging configuration."""

from __future__ import annotations

import os

import sentry_sdk
import structlog


def init_monitoring(dsn: str | None = None) -> None:
    """Initialize Sentry SDK for crash reporting and performance monitoring."""
    if dsn is None:
        dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
    )


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
