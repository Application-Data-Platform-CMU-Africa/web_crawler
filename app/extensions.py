"""
Flask Extensions
Initialize all Flask extensions here
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
from redis import Redis

# Database
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# CORS
cors = CORS()

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]  # Will be set from config
)

# Celery task queue
celery = Celery(__name__)

# Redis client
redis_client = None


def init_redis(app):
    """Initialize Redis client"""
    global redis_client
    redis_url = app.config.get('REDIS_URL')
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    return redis_client
