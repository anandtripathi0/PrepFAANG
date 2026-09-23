from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")
    app_env: str = "development"
    database_url: str = ""
    database_name: str = "prepForge"
    user_collection: str = "user_details"
    secret_key: str = ""
    frontend_origin: str = "http://localhost:5173"
    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_from: str = "noreply@example.com"
    code_runner_url: str = "http://localhost:8090"
    code_runner_token: str = ""
    redis_url: str = ""

    def validated(self):
        if self.app_env == "production":
            if not self.database_url.startswith(("postgresql", "mongodb")) or len(self.secret_key) < 32:
                raise RuntimeError(
                    "Production requires PostgreSQL or MongoDB DATABASE_URL and SECRET_KEY of at least 32 characters."
                )
            if not self.email_host or len(self.code_runner_token) < 32:
                raise RuntimeError("Production requires EMAIL_HOST and CODE_RUNNER_TOKEN of at least 32 characters.")
            if not self.frontend_origin.startswith("https://"):
                raise RuntimeError("Production FRONTEND_ORIGIN must use HTTPS.")
        return self


@lru_cache
def settings():
    return Settings().validated()
