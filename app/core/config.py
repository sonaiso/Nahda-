import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NAHDA_")

    app_env: str = "development"
    database_url: str = "sqlite:///./nahda.db"
    sql_pool_size: int = 10
    sql_max_overflow: int = 20
    sql_pool_timeout: int = 30
    sql_pool_recycle: int = 1800
    auth_enabled: bool = True
    auth_jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_exp_minutes: int = 60
    auth_bootstrap_key: str = "local-dev-bootstrap-key"
    rate_limit_enabled: bool = True
    rate_limit_requests_per_window: int = 120
    rate_limit_window_seconds: int = 60
    observability_enabled: bool = True
    observability_include_path_labels: bool = True
    otel_enabled: bool = True
    otel_service_name: str = "nahda-engine"
    otel_exporter: str = "none"
    otel_otlp_endpoint: str = "http://localhost:4318/v1/traces"
    otel_sampling_ratio: float = 1.0
    alert_webhook_url: str = "http://localhost:5001/alerts"
    alert_slack_webhook_url: str = "http://localhost:5001/slack"
    secret_provider: str = "env"


def validate_production_settings() -> None:
    if settings.app_env.lower() not in {"production", "prod"}:
        return

    errors: list[str] = []
    if settings.database_url.startswith("sqlite"):
        errors.append("NAHDA_DATABASE_URL must not use sqlite in production")
    if len(settings.auth_jwt_secret) < 32:
        errors.append("NAHDA_AUTH_JWT_SECRET must be a strong value (min 32 chars)")
    if settings.auth_bootstrap_key == "local-dev-bootstrap-key":
        errors.append("NAHDA_AUTH_BOOTSTRAP_KEY must be rotated for production")
    if settings.otel_enabled and settings.otel_exporter == "none":
        errors.append("NAHDA_OTEL_EXPORTER must be console or otlp in production")

    if errors:
        raise ValueError("Production configuration validation failed: " + "; ".join(errors))


settings = Settings()
