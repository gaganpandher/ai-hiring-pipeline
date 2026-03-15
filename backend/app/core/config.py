from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Hiring Pipeline"
    APP_ENV: str = "development"
    SECRET_KEY: str
    DEBUG: bool = True

    # Database
    DATABASE_URL: str
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "hiring_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_TOPIC_APPLICATIONS: str = "applications"
    KAFKA_TOPIC_SCORING_RESULTS: str = "scoring-results"
    KAFKA_TOPIC_BIAS_ALERTS: str = "bias-alerts"
    KAFKA_TOPIC_AUDIT_LOG: str = "audit-log"
    KAFKA_TOPIC_NOTIFICATIONS: str = "notifications"
    KAFKA_TOPIC_RECRUITER_ACTIONS: str = "recruiter-actions"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Storage
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "/app/uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
