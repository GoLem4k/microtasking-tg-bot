from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    USE_DOCKER_DB: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        host = "db" if self.USE_DOCKER_DB else self.DB_HOST
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{host}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
