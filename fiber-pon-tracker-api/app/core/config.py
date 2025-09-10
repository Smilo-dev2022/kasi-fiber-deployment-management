from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    S3_ENDPOINT: str
    S3_REGION: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    CORS_ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()
