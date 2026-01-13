"""
Health Check Utilities
Check status of system components
"""
from app.extensions import db, redis_client


def check_database():
    """Check if database is accessible"""
    try:
        # Try a simple query
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


def check_redis():
    """Check if Redis is accessible"""
    try:
        if redis_client:
            redis_client.ping()
            return True
        return False
    except Exception as e:
        print(f"Redis health check failed: {e}")
        return False


def check_celery():
    """Check if Celery workers are available"""
    try:
        from app.extensions import celery
        # Check if any workers are active
        inspect = celery.control.inspect()
        stats = inspect.stats()
        return stats is not None and len(stats) > 0
    except Exception as e:
        print(f"Celery health check failed: {e}")
        return False


def check_health():
    """
    Comprehensive health check

    Returns:
        dict: Health status of all components
    """
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    }

    all_healthy = all(checks.values())

    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks
    }
