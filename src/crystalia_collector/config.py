from functools import lru_cache

from pydantic_settings import BaseSettings


class CollectorSettings(BaseSettings):
    """Configuration for crystalia-collector."""

    model_config = {"env_prefix": "CRYSTALIA_"}

    # S3 settings
    default_method_id: str = "md5-8gb"
    default_output_file: str = "out.rdf"

    # Sentry settings
    sentry_dsn: str | None = None
    sentry_environment: str = "development"

    # Logging
    log_json: bool = True


@lru_cache(maxsize=1)
def get_settings() -> CollectorSettings:
    """Get application settings (loaded once at first call)."""
    return CollectorSettings()
