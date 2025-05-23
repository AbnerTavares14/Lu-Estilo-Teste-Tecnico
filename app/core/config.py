from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "luestilo"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()