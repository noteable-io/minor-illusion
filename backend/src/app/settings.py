from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "cockroachdb://root@cockroach:26257/defaultdb?sslmode=disable"


@lru_cache
def get_settings():
    return Settings()
