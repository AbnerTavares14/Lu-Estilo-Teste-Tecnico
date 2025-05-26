from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    SENTRY_DSN: str = ""
    ENVIRONMENT: str
    ALLOWED_ORIGINS: list[str]
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_FROM_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_TO_NUMBER: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()