from unittest.mock import patch

from typer.testing import CliRunner

from crystalia_collector.app import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "annotate" in result.output
    assert "checksum" in result.output
    assert "combine" in result.output
    assert "test-sentry" in result.output


def test_combine():
    result = runner.invoke(app, ["combine"])
    assert result.exit_code == 0


def test_test_sentry_no_dsn(monkeypatch):
    monkeypatch.delenv("CRYSTALIA_SENTRY_DSN", raising=False)
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setenv("CRYSTALIA_ENABLE_TELEMETRY", "false")
    from crystalia_collector.config import get_settings

    get_settings.cache_clear()
    result = runner.invoke(app, ["test-sentry"])
    get_settings.cache_clear()
    assert result.exit_code != 0
    assert "SENTRY_DSN" in result.output


def test_list_error_handling():
    with patch("crystalia_collector.app.list_dir", side_effect=RuntimeError("source error")):
        result = runner.invoke(app, ["list", "/some/path"])
    assert result.exit_code != 0


def test_checksum_error_handling():
    with patch("crystalia_collector.app.detect_source", side_effect=RuntimeError("source error")):
        result = runner.invoke(app, ["checksum", "s3://bucket/key"])
    assert result.exit_code != 0
