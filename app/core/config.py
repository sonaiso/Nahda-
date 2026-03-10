from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NAHDA_")

    database_url: str = "sqlite:///./nahda.db"


settings = Settings()
