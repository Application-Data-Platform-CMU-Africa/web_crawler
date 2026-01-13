"""
Error Handlers
Centralized error handling for the API
"""
from flask import jsonify
from app.utils.response import error_response


def handle_400(error):
    """Handle 400 Bad Request"""
    return error_response(
        code='BAD_REQUEST',
        message='Invalid request data',
        status_code=400
    )


def handle_401(error):
    """Handle 401 Unauthorized"""
    return error_response(
        code='UNAUTHORIZED',
        message='Authentication required',
        status_code=401
    )


def handle_403(error):
    """Handle 403 Forbidden"""
    return error_response(
        code='FORBIDDEN',
        message='Insufficient permissions',
        status_code=403
    )


def handle_404(error):
    """Handle 404 Not Found"""
    return error_response(
        code='NOT_FOUND',
        message='Resource not found',
        status_code=404
    )


def handle_405(error):
    """Handle 405 Method Not Allowed"""
    return error_response(
        code='METHOD_NOT_ALLOWED',
        message='Method not allowed for this endpoint',
        status_code=405
    )


def handle_429(error):
    """Handle 429 Too Many Requests"""
    return error_response(
        code='RATE_LIMIT_EXCEEDED',
        message='Too many requests. Please try again later.',
        status_code=429
    )


def handle_500(error):
    """Handle 500 Internal Server Error"""
    return error_response(
        code='INTERNAL_ERROR',
        message='An internal server error occurred',
        status_code=500
    )
