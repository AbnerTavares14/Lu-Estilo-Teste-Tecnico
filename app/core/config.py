from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    SENTRY_DSN: str = ""
    ENVIRONMENT: str
    ALLOWED_ORIGINS: list[str]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()