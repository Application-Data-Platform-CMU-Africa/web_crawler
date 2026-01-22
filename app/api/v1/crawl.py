"""
Crawl Management Endpoints
Start, monitor, and manage web crawling jobs
"""
import uuid
import logging
from flask import request, g
from app.api.v1 import api_v1
from app.utils.response import success_response, error_response
from app.utils.auth import require_api_key
from app.extensions import db
from app.models.crawl_job import CrawlJob
from app.tasks.crawl_tasks import run_crawl

logger = logging.getLogger(__name__)


@api_v1.route('/crawl/start', methods=['POST'])
@require_api_key
def start_crawl():
    """
    Start a new crawl job
    ---
    POST /api/v1/crawl/start

    Request Body:
    {
        "site_id": "1" or "uganda-portal",
        "options": {
            "max_pages": 100,
            "test_mode": false
        }
    }

    Response:
    {
        "success": true,
        "data": {
            "job_id": "uuid-string",
            "celery_task_id": "task-id",
            "status": "pending",
            "site_id": "1",
            "options": {...}
        },
        "message": "Crawl job queued successfully"
    }
    """
    try:
        # Parse request data
        data = request.get_json() or {}

        # Validate required fields
        site_id = data.get('site_id')
        if not site_id:
            return error_response('site_id is required', status_code=400)

        # Get options
        options = data.get('options', {})

        # Load site config to validate
        from app.services.crawler_service import CrawlerService
        service = CrawlerService()
        site_config = service.load_site_config(site_id)

        if not site_config:
            return error_response(
                f'Site configuration not found: {site_id}',
                status_code=404
            )

        # Validate options
        is_valid, error_msg = service.validate_crawl_request(
            site_config, options)
        if not is_valid:
            return error_response(error_msg, status_code=400)

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Get current user (from API key)
        user_id = getattr(g, 'current_user_id', None)

        # Create crawl job record
        crawl_job = CrawlJob(
            job_id=job_id,
            site_id=str(site_id),
            start_url=site_config['start_url'],
            crawler_type=site_config.get('crawler_type', 'static'),
            options=options,
            status='pending',
            created_by=user_id
        )

        db.session.add(crawl_job)
        db.session.commit()

        # Queue Celery task
        task = run_crawl.apply_async(
            args=[job_id, str(site_id), options],
            queue='crawl'
        )

        # Update job with Celery task ID
        crawl_job.celery_task_id = task.id
        db.session.commit()

        logger.info(f"Crawl job created: {job_id}, task: {task.id}")

        return success_response(
            data={
                'job_id': job_id,
                'celery_task_id': task.id,
                'status': 'pending',
                'site_id': str(site_id),
                'start_url': site_config['start_url'],
                'options': options,
                'created_at': crawl_job.created_at.isoformat()
            },
            message='Crawl job queued successfully'
        ), 202

    except Exception as e:
        logger.error(f"Error starting crawl: {e}", exc_info=True)
        db.session.rollback()
        return error_response(
            f'Failed to start crawl job: {str(e)}',
            status_code=500
        )


@api_v1.route('/crawl/jobs', methods=['GET'])
@require_api_key
def list_crawl_jobs():
    """
    List all crawl jobs
    ---
    GET /api/v1/crawl/jobs?page=1&limit=20&status=running

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - site_id: Filter by site ID

    Response:
    {
        "success": true,
        "data": {
            "jobs": [...],
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": 100,
                "pages": 5
            }
        }
    }
    """
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status_filter = request.args.get('status', None)
        site_id_filter = request.args.get('site_id', None)

        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        # Build query
        query = CrawlJob.query

        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        if site_id_filter:
            query = query.filter_by(site_id=str(site_id_filter))

        # Order by most recent first
        query = query.order_by(CrawlJob.created_at.desc())

        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=limit,
            error_out=False
        )

        # Convert jobs to dict
        jobs = [job.to_dict() for job in pagination.items]

        return success_response(
            data={
                'jobs': jobs,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        )

    except Exception as e:
        logger.error(f"Error listing crawl jobs: {e}", exc_info=True)
        return error_response(
            f'Failed to list crawl jobs: {str(e)}',
            status_code=500
        )


@api_v1.route('/crawl/jobs/<job_id>', methods=['GET'])
@require_api_key
def get_crawl_job(job_id):
    """
    Get specific crawl job details
    ---
    GET /api/v1/crawl/jobs/{job_id}?include_datasets=false

    Query Parameters:
    - include_datasets: Include datasets created by this job (default: false)

    Response:
    {
        "success": true,
        "data": {
            "job_id": "uuid",
            "status": "running",
            "progress_percentage": 45.5,
            "statistics": {...},
            "datasets": [...]  // if include_datasets=true
        }
    }
    """
    try:
        # Find the crawl job
        crawl_job = CrawlJob.find_by_job_id(job_id)

        if not crawl_job:
            return error_response(
                f'Crawl job not found: {job_id}',
                status_code=404
            )

        # Check if datasets should be included
        include_datasets = request.args.get(
            'include_datasets', 'false').lower() == 'true'

        # Convert to dict
        job_data = crawl_job.to_dict(include_datasets=include_datasets)

        return success_response(data=job_data)

    except Exception as e:
        logger.error(f"Error getting crawl job: {e}", exc_info=True)
        return error_response(
            f'Failed to get crawl job: {str(e)}',
            status_code=500
        )


@api_v1.route('/crawl/jobs/<job_id>/cancel', methods=['POST'])
@require_api_key
def cancel_crawl_job(job_id):
    """
    Cancel a running crawl job
    ---
    POST /api/v1/crawl/jobs/{job_id}/cancel

    Response:
    {
        "success": true,
        "data": {
            "job_id": "uuid",
            "status": "cancelled"
        },
        "message": "Crawl job cancelled successfully"
    }
    """
    try:
        # Find the crawl job
        crawl_job = CrawlJob.find_by_job_id(job_id)

        if not crawl_job:
            return error_response(
                f'Crawl job not found: {job_id}',
                status_code=404
            )

        # Check if job can be cancelled
        if crawl_job.status in ['completed', 'failed', 'cancelled']:
            return error_response(
                f'Cannot cancel job with status: {crawl_job.status}',
                status_code=400
            )

        # Cancel the Celery task if it exists
        if crawl_job.celery_task_id:
            from app.extensions import celery
            celery.control.revoke(crawl_job.celery_task_id, terminate=True)

        # Mark job as cancelled
        crawl_job.cancel()
        db.session.commit()

        logger.info(f"Crawl job cancelled: {job_id}")

        return success_response(
            data=crawl_job.to_dict(),
            message='Crawl job cancelled successfully'
        )

    except Exception as e:
        logger.error(f"Error cancelling crawl job: {e}", exc_info=True)
        db.session.rollback()
        return error_response(
            f'Failed to cancel crawl job: {str(e)}',
            status_code=500
        )
