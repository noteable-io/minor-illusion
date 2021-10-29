from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = "cockroachdb://root@cockroach:26257/defaultdb?sslmode=disable"


settings = Settings()
