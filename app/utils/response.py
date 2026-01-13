"""
API Response Utilities
Standardized response formatting
"""
from flask import jsonify
from datetime import datetime


def success_response(data=None, message='Success', status_code=200):
    """
    Create a standardized success response

    Args:
        data: Response data (dict or list)
        message: Success message
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        'success': True,
        'data': data,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    return jsonify(response), status_code


def error_response(code, message, details=None, status_code=400):
    """
    Create a standardized error response

    Args:
        code: Error code (e.g., 'VALIDATION_ERROR')
        message: Error message
        details: Additional error details
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if details:
        response['error']['details'] = details

    return jsonify(response), status_code


def paginated_response(items, page, per_page, total):
    """
    Create a paginated response

    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items

    Returns:
        Dict with pagination info
    """
    total_pages = (total + per_page - 1) // per_page  # Ceiling division

    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
