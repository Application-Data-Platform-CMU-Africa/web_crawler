"""
Health Check Endpoints
System health and status monitoring
"""
from flask import jsonify, current_app
from app.api.v1 import api_v1
from app.utils.response import success_response


@api_v1.route('/health', methods=['GET'])
def health_check():
    """
    Check API health status
    ---
    GET /api/v1/health
    """
    from app.utils.health import check_health
    health_data = check_health()
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return success_response(data=health_data), status_code


@api_v1.route('/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics
    ---
    GET /api/v1/stats
    """
    # TODO: Implement actual stats
    stats = {
        'total_datasets': 0,
        'total_crawl_jobs': 0,
        'active_jobs': 0,
        'datasets_today': 0
    }
    return success_response(data=stats)
