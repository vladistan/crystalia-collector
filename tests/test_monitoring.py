"""Tests for Sentry monitoring integration."""

from crystalia_collector.monitoring import init_monitoring


def test_init_monitoring_no_dsn_does_nothing():
    """init_monitoring with no DSN and no env var does nothing (smoke test)."""
    from unittest.mock import patch

    with patch.dict("os.environ", {}, clear=True):
        init_monitoring()  # Should not raise
