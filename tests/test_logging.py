"""Tests for structured logging configuration."""

import json
from io import StringIO

import structlog

from crystalia_collector.monitoring import configure_logging


def test_configure_logging_sets_up_structlog():
    """configure_logging configures structlog processors."""
    configure_logging(json_output=True)
    config = structlog.get_config()
    assert config["processors"] is not None
    assert len(config["processors"]) > 0


def test_json_output_produces_valid_json():
    """JSON output mode produces valid JSON log lines."""
    configure_logging(json_output=True)
    output = StringIO()
    # Reconfigure with a custom logger factory while keeping processors
    config = structlog.get_config()
    structlog.configure(
        processors=config["processors"],
        logger_factory=structlog.PrintLoggerFactory(output),
    )
    log = structlog.get_logger()
    log.info("test_event", bucket="test-bucket", key="some/key")
    line = output.getvalue().strip()
    parsed = json.loads(line)
    assert parsed["event"] == "test_event"
    assert parsed["bucket"] == "test-bucket"
    assert parsed["key"] == "some/key"
    assert "timestamp" in parsed
    assert parsed["level"] == "info"


def test_console_output_mode_works():
    """Console output mode produces human-readable output."""
    configure_logging(json_output=False)
    output = StringIO()
    logger = structlog.PrintLogger(output)
    bound = structlog.wrap_logger(logger)
    log = bound.bind()
    log.info("console_test", detail="works")
    line = output.getvalue().strip()
    assert "console_test" in line
    assert "works" in line
