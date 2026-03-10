import pytest

from app.core import config as config_module


def test_validate_production_settings_allows_non_production() -> None:
    config_module.settings.app_env = "development"
    config_module.validate_production_settings()


def test_validate_production_settings_rejects_weak_production_values() -> None:
    original = {
        "app_env": config_module.settings.app_env,
        "database_url": config_module.settings.database_url,
        "auth_jwt_secret": config_module.settings.auth_jwt_secret,
        "auth_bootstrap_key": config_module.settings.auth_bootstrap_key,
        "otel_enabled": config_module.settings.otel_enabled,
        "otel_exporter": config_module.settings.otel_exporter,
    }

    try:
        config_module.settings.app_env = "production"
        config_module.settings.database_url = "sqlite:///./nahda.db"
        config_module.settings.auth_jwt_secret = "short"
        config_module.settings.auth_bootstrap_key = "local-dev-bootstrap-key"
        config_module.settings.otel_enabled = True
        config_module.settings.otel_exporter = "none"

        with pytest.raises(ValueError):
            config_module.validate_production_settings()
    finally:
        config_module.settings.app_env = original["app_env"]
        config_module.settings.database_url = original["database_url"]
        config_module.settings.auth_jwt_secret = original["auth_jwt_secret"]
        config_module.settings.auth_bootstrap_key = original["auth_bootstrap_key"]
        config_module.settings.otel_enabled = original["otel_enabled"]
        config_module.settings.otel_exporter = original["otel_exporter"]
