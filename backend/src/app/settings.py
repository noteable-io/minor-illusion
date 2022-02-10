import secrets
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "cockroachdb+asyncpg://root@localhost:26257/defaultdb"
    SYNC_DB_DSN: str = "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"
    LOG_LEVEL: str = "INFO"
    LOGS_AS_JSON: bool = False
    ROOT_PATH: Optional[str] = None
    SECRET_KEY: str = secrets.token_urlsafe(32)


@lru_cache
def get_settings():
    return Settings()
