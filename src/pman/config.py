"""Configurazione centralizzata via pydantic-settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variabili ambiente per SMOT-PMANAGER."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = Field(default="", alias="PMAN_GITHUB_TOKEN")
    github_api_url: str = "https://api.github.com"

    # ── Ollama AI ─────────────────────────────────────────────────────────────
    ollama_host: str = Field(default="http://10.0.0.2:11434", alias="PMAN_OLLAMA_HOST")
    ollama_model: str = Field(default="gemma4-dev", alias="PMAN_OLLAMA_MODEL")

    # ── Database ──────────────────────────────────────────────────────────────
    db_path: str = Field(default="/tmp/pman.db", alias="PMAN_DB_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # ── Vault / Shared Brain ────────────────────────────────────────────────────
    vault_path: str = Field(
        default=str(Path.home() / "shared-brain"),
        alias="PMAN_VAULT_PATH",
    )

    # ── Task Queue ────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0", alias="PMAN_REDIS_URL")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")

    # ── Notifiche ─────────────────────────────────────────────────────────────
    slack_webhook: str | None = Field(default=None, alias="PMAN_SLACK_WEBHOOK")

    # ── App ───────────────────────────────────────────────────────────────────
    debug: bool = Field(default=False, alias="PMAN_DEBUG")
    log_level: str = Field(default="INFO", alias="PMAN_LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="PMAN_HOST")
    port: int = Field(default=8000, alias="PMAN_PORT")

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def effective_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()
