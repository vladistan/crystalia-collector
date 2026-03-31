import os
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, TomlConfigSettingsSource

# Default project Sentry DSN — used when enable_telemetry=True and no custom DSN is configured.
# Replace with your project's actual DSN from https://sentry.io/settings/<org>/projects/<project>/keys/
_DEFAULT_SENTRY_DSN: str | None = None  # TODO: set project DSN after creating Sentry project

_CONFIG_PATHS = [
    Path("crystalia.toml"),
    Path.home() / ".config" / "crystalia-collector" / "config.toml",
]


class CollectorSettings(BaseSettings):
    """Configuration for crystalia-collector.

    Sources (highest to lowest priority):
    1. Environment variables with CRYSTALIA_ prefix (or bare SENTRY_DSN)
    2. ./crystalia.toml (project-local config)
    3. ~/.config/crystalia-collector/config.toml (user global config)
    4. Defaults
    """

    model_config = {
        "env_prefix": "CRYSTALIA_",
        "toml_file": [str(p) for p in _CONFIG_PATHS],
    }

    # S3 settings
    default_method_id: str = "md5-8gb"
    default_output_file: str = "out.rdf"

    # Telemetry
    enable_telemetry: bool = True
    sentry_dsn: str | None = None
    sentry_environment: str = "development"

    # Logging
    log_json: bool = True

    @model_validator(mode="after")
    def resolve_sentry_dsn(self) -> "CollectorSettings":
        """Resolve DSN: bare SENTRY_DSN env fallback, then project default."""
        if not self.sentry_dsn:
            self.sentry_dsn = os.environ.get("SENTRY_DSN")
        if self.enable_telemetry and not self.sentry_dsn:
            self.sentry_dsn = _DEFAULT_SENTRY_DSN
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> CollectorSettings:
    """Get application settings (loaded once at first call)."""
    return CollectorSettings()
