from typing import Literal
from ipaddress import ip_address
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://petmatch:petmatch@localhost:5432/petmatch"
    jwt_secret: str = "local-development-only-change-this-secret"
    access_token_minutes: int = 60
    web_origin: str = "http://localhost:3000"
    s3_endpoint: str = "http://localhost:9000"
    s3_public_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "pet-photos"
    s3_access_key: str = "petmatch"
    s3_secret_key: str = "change-this-minio-password"
    max_photo_size_bytes: int = 10 * 1024 * 1024
    redis_url: str = "redis://localhost:6379/0"
    ai_enabled: bool = False
    ai_provider: Literal["ollama"] = "ollama"
    ai_text_model: str = "gemma3:4b"
    ai_vision_model: str = "gemma3:4b"
    ollama_base_url: str = "http://localhost:11434"
    ai_request_timeout_seconds: int = Field(default=180, ge=10, le=600)
    ai_max_attempts: int = Field(default=3, ge=1, le=5)
    ai_dispatch_interval_seconds: int = Field(default=5, ge=1, le=60)

    @field_validator("ai_text_model", "ai_vision_model")
    @classmethod
    def local_model_only(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 120 or "cloud" in value.split(":")[-1].lower():
            raise ValueError("Configure a local Ollama model, not a cloud model")
        return value

    @field_validator("ollama_base_url")
    @classmethod
    def local_ollama_only(cls, value: str) -> str:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        allowed = host in {"localhost", "ollama", "host.docker.internal"}
        try:
            address = ip_address(host)
            allowed = address.is_private or address.is_loopback
        except ValueError:
            pass
        if parsed.scheme not in {"http", "https"} or not allowed or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            raise ValueError("OLLAMA_BASE_URL must point to a local/private Ollama server without credentials")
        return value.rstrip("/")

    @property
    def ai_job_timeout_seconds(self) -> int:
        return self.ai_request_timeout_seconds + 60

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.web_origin.split(",") if origin.strip()]


settings = Settings()

