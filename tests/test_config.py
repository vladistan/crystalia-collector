import tomllib
from pathlib import Path

from crystalia_collector.config import CollectorSettings, get_settings


def test_default_values():
    settings = CollectorSettings()
    assert settings.default_method_id == "md5-8gb"
    assert settings.default_output_file == "out.rdf"
    assert settings.sentry_environment == "development"
    assert settings.log_json is True
    assert settings.enable_telemetry is True


def test_sentry_dsn_defaults_to_none_when_no_default_set(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("CRYSTALIA_SENTRY_DSN", raising=False)
    import crystalia_collector.config as cfg_module

    monkeypatch.setattr(cfg_module, "_DEFAULT_SENTRY_DSN", None)
    settings = CollectorSettings()
    assert settings.sentry_dsn is None


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_DEFAULT_METHOD_ID", "sha256-4gb")
    monkeypatch.setenv("CRYSTALIA_DEFAULT_OUTPUT_FILE", "result.ttl")
    settings = CollectorSettings()
    assert settings.default_method_id == "sha256-4gb"
    assert settings.default_output_file == "result.ttl"


def test_crystalia_prefix_overrides(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_SENTRY_ENVIRONMENT", "production")
    monkeypatch.setenv("CRYSTALIA_LOG_JSON", "false")
    settings = CollectorSettings()
    assert settings.sentry_environment == "production"
    assert settings.log_json is False


def test_bare_sentry_dsn_env_var_used_as_fallback(monkeypatch):
    monkeypatch.delenv("CRYSTALIA_SENTRY_DSN", raising=False)
    monkeypatch.setenv("SENTRY_DSN", "https://bare@o0.ingest.sentry.io/1")
    settings = CollectorSettings()
    assert settings.sentry_dsn == "https://bare@o0.ingest.sentry.io/1"


def test_crystalia_sentry_dsn_takes_precedence_over_bare(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_SENTRY_DSN", "https://custom@o0.ingest.sentry.io/2")
    monkeypatch.setenv("SENTRY_DSN", "https://bare@o0.ingest.sentry.io/1")
    settings = CollectorSettings()
    assert settings.sentry_dsn == "https://custom@o0.ingest.sentry.io/2"


def test_default_dsn_used_when_telemetry_enabled_and_no_dsn(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("CRYSTALIA_SENTRY_DSN", raising=False)
    import crystalia_collector.config as cfg_module

    monkeypatch.setattr(cfg_module, "_DEFAULT_SENTRY_DSN", "https://default@o0.ingest.sentry.io/0")
    settings = CollectorSettings()
    assert settings.enable_telemetry is True
    assert settings.sentry_dsn == "https://default@o0.ingest.sentry.io/0"


def test_default_dsn_not_used_when_telemetry_disabled(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("CRYSTALIA_SENTRY_DSN", raising=False)
    monkeypatch.setenv("CRYSTALIA_ENABLE_TELEMETRY", "false")
    import crystalia_collector.config as cfg_module

    monkeypatch.setattr(cfg_module, "_DEFAULT_SENTRY_DSN", "https://default@o0.ingest.sentry.io/0")
    settings = CollectorSettings()
    assert settings.enable_telemetry is False
    assert settings.sentry_dsn is None


def test_toml_config_file_loaded(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "crystalia.toml"
    config_file.write_text(
        'default_method_id = "md5-2gb"\nsentry_environment = "staging"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    # Ensure env vars don't interfere
    monkeypatch.delenv("CRYSTALIA_DEFAULT_METHOD_ID", raising=False)
    monkeypatch.delenv("CRYSTALIA_SENTRY_ENVIRONMENT", raising=False)
    settings = CollectorSettings()
    assert settings.default_method_id == "md5-2gb"
    assert settings.sentry_environment == "staging"


def test_toml_config_file_is_valid_toml(tmp_path: Path):
    config_file = tmp_path / "crystalia.toml"
    config_file.write_text(
        'default_method_id = "md5-8gb"\nenable_telemetry = false\n',
        encoding="utf-8",
    )
    with open(config_file, "rb") as f:
        parsed = tomllib.load(f)
    assert parsed["default_method_id"] == "md5-8gb"
    assert parsed["enable_telemetry"] is False


def test_get_settings_returns_instance():
    settings = get_settings()
    assert isinstance(settings, CollectorSettings)
