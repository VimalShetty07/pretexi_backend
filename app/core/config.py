from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Protexi API"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # JWT Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Credentials / defaults that must be private
    DEFAULT_EMPLOYEE_PASSWORD: str
    MOCK_SEED_PASSWORD: str

    # Mock auth (flag) — when True, accept X-Mock-User-Email (+ optional X-Mock-User-Role) instead of Bearer for dev
    MOCK_AUTH: bool = False
    # Default user email when mock auth is used and no X-Mock-User-Email header is sent (optional)
    MOCK_USER_EMAIL: str | None = None

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    STORAGE_PROVIDER: str = "local"  # local | s3
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    S3_BUCKET: str | None = None
    S3_PREFIX: str = "uploads/"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
