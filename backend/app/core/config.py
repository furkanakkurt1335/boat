from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://boat:boat@db:5432/boat"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    REGISTRATION_MODE: str = "approval"  # "open", "approval", or "closed"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or v == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY must be set to a strong random value. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        return v


settings = Settings()
