"""
Application Configuration
Manages different configurations for development, testing, and production
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # App
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    APP_NAME = "Dataset Crawler API"
    API_VERSION = "v1"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://localhost/web_crawler_dev"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20)),
    }

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv(
        "CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
    )
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
    CELERY_TASK_SOFT_TIME_LIMIT = 3300  # 55 minutes

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # External API (for publishing)
    EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL")
    EXTERNAL_API_URL_TEST = os.getenv("EXTERNAL_API_URL_TEST")
    EXTERNAL_API_EMAIL = os.getenv("EXTERNAL_API_EMAIL")
    EXTERNAL_API_PASSWORD = os.getenv("EXTERNAL_API_PASSWORD")
    EXTERNAL_API_EMAIL_TEST = os.getenv("EXTERNAL_API_EMAIL_TEST")
    EXTERNAL_API_PASSWORD_TEST = os.getenv("EXTERNAL_API_PASSWORD_TEST")

    # Security
    PASSCODE_HASH = os.getenv("PASSCODE_HASH")
    API_KEY_EXPIRY_DAYS = int(os.getenv("API_KEY_EXPIRY_DAYS", 365))

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Crawler Settings
    MAX_CONCURRENT_CRAWLS = int(os.getenv("MAX_CONCURRENT_CRAWLS", 5))
    CRAWL_TIMEOUT_SECONDS = int(os.getenv("CRAWL_TIMEOUT_SECONDS", 3600))
    CRAWL_DOWNLOAD_DELAY = int(os.getenv("CRAWL_DOWNLOAD_DELAY", 2))

    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "json"  # or "text"

    # File Upload (for future use)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost/web_crawler_test"
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in tests
    CELERY_TASK_EAGER_PROPAGATES = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    # Require HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Stricter rate limiting
    RATELIMIT_DEFAULT = "100 per day, 20 per hour"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv("FLASK_ENV", "development")
    return config.get(env, config["default"])
