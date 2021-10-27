from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "postgresql://postgres:postgres@postgres:5432/postgres"


settings = Settings()
