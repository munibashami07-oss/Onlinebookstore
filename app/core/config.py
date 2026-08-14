"""Application Configuration Module using Pydantic Settings."""

from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global system configuration settings loaded from environment variables."""

    # Project Information
    PROJECT_NAME: str = "Online Book Store"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security & JWT Settings
    SECRET_KEY: str = "super_secret_jwt_access_token_key_change_in_production"
    REFRESH_SECRET_KEY: str = "super_secret_jwt_refresh_token_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Separate Database Configuration Variables
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "task2_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASS: str = "postgres"

    # Admin Credentials (To be inserted by seed.py later)
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@bookstore.com"
    ADMIN_PASSWORD: str = "AdminPassword123!"

    # AI Integration Settings (Prepared for Phase 13)
    OPENAI_API_KEY: str = ""

    # Password Reset Email (Gmail SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM_EMAIL: str = ""
    MAIL_FROM_NAME: str = "BookHaven"
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    RESEND_API_KEY: str = ""
    # Public URL of the deployed frontend (Netlify), used to build the
    # password-reset link embedded in the email. No trailing slash.
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS Configuration
    BACKEND_CORS_ORIGINS=["https://subtle-marshmallow-c8aeac.netlify.app","http://localhost:5173","http://localhost:8000"]
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Dynamically constructs async PostgreSQL URL from separate environment variables."""
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASS}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Dynamically constructs sync PostgreSQL URL from separate environment variables."""
        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASS}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


settings = Settings()