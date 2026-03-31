from crystalia_collector.config import CollectorSettings, get_settings


def test_default_values():
    settings = CollectorSettings()
    assert settings.default_method_id == "md5-8gb"
    assert settings.default_output_file == "out.rdf"
    assert settings.sentry_environment == "development"
    assert settings.log_json is True


def test_sentry_dsn_defaults_to_none():
    settings = CollectorSettings()
    assert settings.sentry_dsn is None


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_DEFAULT_METHOD_ID", "sha256-4gb")
    monkeypatch.setenv("CRYSTALIA_DEFAULT_OUTPUT_FILE", "result.ttl")
    settings = CollectorSettings()
    assert settings.default_method_id == "sha256-4gb"
    assert settings.default_output_file == "result.ttl"


def test_crystalia_prefix_works(monkeypatch):
    monkeypatch.setenv("CRYSTALIA_SENTRY_DSN", "https://example.com/sentry")
    monkeypatch.setenv("CRYSTALIA_SENTRY_ENVIRONMENT", "production")
    monkeypatch.setenv("CRYSTALIA_LOG_JSON", "false")
    settings = CollectorSettings()
    assert settings.sentry_dsn == "https://example.com/sentry"
    assert settings.sentry_environment == "production"
    assert settings.log_json is False


def test_get_settings_returns_instance():
    settings = get_settings()
    assert isinstance(settings, CollectorSettings)
