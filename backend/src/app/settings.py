from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "cockroachdb://root@cockroach:26257/defaultdb?sslmode=disable"
    LOG_LEVEL: str = "INFO"
    LOGS_AS_JSON: bool = False


@lru_cache
def get_settings():
    return Settings()
