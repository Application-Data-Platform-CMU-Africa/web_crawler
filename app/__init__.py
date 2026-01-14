"""
Flask Application Factory
Creates and configures the Flask application
"""
from flask import Flask, jsonify
from app.config import get_config
from app.extensions import db, migrate, cors, limiter, celery, init_redis


def create_app(config_name=None):
    """
    Application factory pattern

    Args:
        config_name: Configuration to use (development, testing, production)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name:
        from app.config import config
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(get_config())

    # Initialize extensions
    init_extensions(app)

    # Initialize Celery
    init_celery(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register shell context
    register_shell_context(app)

    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    limiter.init_app(app)
    init_redis(app)


def init_celery(app):
    """Initialize Celery with Flask app context"""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer=app.config['CELERY_TASK_SERIALIZER'],
        result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
        accept_content=app.config['CELERY_ACCEPT_CONTENT'],
        timezone=app.config['CELERY_TIMEZONE'],
        enable_utc=app.config['CELERY_ENABLE_UTC'],
        task_track_started=app.config['CELERY_TASK_TRACK_STARTED'],
        task_time_limit=app.config['CELERY_TASK_TIME_LIMIT'],
        task_soft_time_limit=app.config['CELERY_TASK_SOFT_TIME_LIMIT'],
    )

    # Task routes
    celery.conf.task_routes = {
        'app.tasks.crawl_tasks.*': {'queue': 'crawl'},
        'app.tasks.classify_tasks.*': {'queue': 'classify'},
        'app.tasks.publish_tasks.*': {'queue': 'publish'},
    }

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.api.v1 import api_v1

    # Register API v1
    app.register_blueprint(api_v1, url_prefix='/api/v1')

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': app.config['APP_NAME'],
            'version': app.config['API_VERSION'],
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'api': '/api/v1',
                'docs': '/api/docs'
            }
        })

    # Health check endpoint
    @app.route('/health')
    def health():
        from app.utils.health import check_health
        health_status = check_health()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code


def register_error_handlers(app):
    """Register error handlers"""
    from app.api.errors import (
        handle_400,
        handle_401,
        handle_403,
        handle_404,
        handle_405,
        handle_429,
        handle_500
    )

    app.register_error_handler(400, handle_400)
    app.register_error_handler(401, handle_401)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(405, handle_405)
    app.register_error_handler(429, handle_429)
    app.register_error_handler(500, handle_500)


def register_shell_context(app):
    """Register shell context objects"""
    def make_shell_context():
        return {
            'db': db,
            'app': app
        }

    app.shell_context_processor(make_shell_context)
