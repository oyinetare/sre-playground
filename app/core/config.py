from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "SRE-Playground"
    environment: str = "development"

    # DB
    database_url: str = "postgresql://admin:password@localhost:5432/sredb"

    # AWS
    aws_endpoint_url: str = "http://localhost:4566"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()