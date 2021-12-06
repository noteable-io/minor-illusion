from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "cockroachdb+asyncpg://root@cockroach:26257/defaultdb"
    LOG_LEVEL: str = "INFO"
    LOGS_AS_JSON: bool = False
    ROOT_PATH: Optional[str] = None


@lru_cache
def get_settings():
    return Settings()
