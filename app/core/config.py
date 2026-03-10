from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NAHDA_")

    app_env: str = "development"
    database_url: str = "sqlite:///./nahda.db"
    sql_pool_size: int = 10
    sql_max_overflow: int = 20
    sql_pool_timeout: int = 30
    sql_pool_recycle: int = 1800


settings = Settings()
