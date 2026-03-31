"""Tests for Sentry monitoring integration."""

from unittest.mock import patch

from crystalia_collector.monitoring import init_monitoring


def test_init_monitoring_no_dsn_does_nothing():
    """init_monitoring with no DSN and no env var does nothing."""
    with patch.dict("os.environ", {}, clear=True):
        # Should not raise
        init_monitoring()


def test_init_monitoring_with_dsn_calls_sentry_init():
    """init_monitoring with an explicit DSN calls sentry_sdk.init."""
    with patch("crystalia_collector.monitoring.sentry_sdk.init") as mock_init:
        init_monitoring(dsn="https://examplePublicKey@o0.ingest.sentry.io/0")
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args[1]
        assert call_kwargs["dsn"] == "https://examplePublicKey@o0.ingest.sentry.io/0"
        assert call_kwargs["traces_sample_rate"] == 1.0


def test_init_monitoring_reads_dsn_from_env():
    """init_monitoring reads SENTRY_DSN from env when no arg given."""
    test_dsn = "https://envkey@o0.ingest.sentry.io/1"
    with (
        patch.dict("os.environ", {"SENTRY_DSN": test_dsn}),
        patch("crystalia_collector.monitoring.sentry_sdk.init") as mock_init,
    ):
        init_monitoring()
        mock_init.assert_called_once()
        assert mock_init.call_args[1]["dsn"] == test_dsn
