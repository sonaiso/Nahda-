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
    auth_jwt_secret: str = "change-me-in-production-32-bytes-min"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_exp_minutes: int = 60
    auth_bootstrap_key: str = "local-dev-bootstrap-key"
    rate_limit_enabled: bool = True
    rate_limit_requests_per_window: int = 120
    rate_limit_window_seconds: int = 60


settings = Settings()
