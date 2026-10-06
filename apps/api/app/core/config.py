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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.web_origin.split(",") if origin.strip()]


settings = Settings()

