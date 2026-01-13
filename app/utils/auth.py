"""
Authentication Utilities
API key authentication decorator
"""
from functools import wraps
from flask import request
from app.utils.response import error_response


def require_api_key(f):
    """
    Decorator to require API key authentication

    Usage:
        @app.route('/protected')
        @require_api_key
        def protected_route():
            return 'Protected data'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return error_response(
                code='MISSING_API_KEY',
                message='API key required in X-API-Key header',
                status_code=401
            )

        # TODO: Implement actual API key validation
        # For now, accept any non-empty key for development
        if not api_key or len(api_key) < 10:
            return error_response(
                code='INVALID_API_KEY',
                message='Invalid or inactive API key',
                status_code=401
            )

        # TODO: Attach user to request context
        # request.current_user = user

        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """
    Decorator to require admin privileges

    Usage:
        @app.route('/admin/users')
        @require_api_key
        @require_admin
        def admin_route():
            return 'Admin data'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Check if current user is admin
        # For now, return forbidden
        return error_response(
            code='FORBIDDEN',
            message='Admin privileges required',
            status_code=403
        )

    return decorated_function
