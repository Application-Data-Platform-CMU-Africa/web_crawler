"""
Crawl Tasks
Celery tasks for web crawling operations
"""
import logging
from datetime import datetime
from typing import Dict, Optional

from app.extensions import celery, db
from app.models.crawl_job import CrawlJob
from app.services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='app.tasks.run_crawl')
def run_crawl(self, job_id: str, site_id: str, options: Optional[Dict] = None):
    """
    Execute a crawl job

    Args:
        self: Celery task instance (bound)
        job_id: CrawlJob UUID
        site_id: Site configuration ID from configs/config.json
        options: Optional crawl options (max_pages, test_mode, etc.)

    Returns:
        Dict with crawl statistics
    """
    logger.info(f"Starting crawl task: job_id={job_id}, site_id={site_id}")

    # Find the crawl job in database
    crawl_job = CrawlJob.find_by_job_id(job_id)
    if not crawl_job:
        logger.error(f"CrawlJob not found: {job_id}")
        raise ValueError(f"CrawlJob not found: {job_id}")

    # Update job with Celery task ID
    crawl_job.celery_task_id = self.request.id
    crawl_job.start()
    db.session.commit()

    try:
        # Initialize crawler service
        crawler_service = CrawlerService(db_session=db.session)

        # Set up progress callback to update database
        def update_job_progress(stats: Dict, **kwargs):
            """Update CrawlJob progress in database"""
            try:
                crawl_job.update_stats(stats)

                # Calculate progress percentage
                max_pages = options.get('max_pages') if options else None
                if max_pages:
                    progress = min(
                        100.0, (stats['pages_crawled'] / max_pages) * 100)
                    crawl_job.update_progress(progress)

                db.session.commit()

            except Exception as e:
                logger.error(f"Error updating job progress: {e}")

        # Execute the crawl
        stats = crawler_service.start_crawl(
            site_id=site_id,
            job_id=job_id,
            options=options or {}
        )

        # Mark job as completed
        crawl_job.complete(stats)
        db.session.commit()

        logger.info(f"Crawl task completed: {job_id}, stats={stats}")
        return stats

    except Exception as e:
        # Mark job as failed
        error_msg = str(e)
        error_details = {
            'exception_type': type(e).__name__,
            'error': error_msg,
            'task_id': self.request.id
        }

        crawl_job.fail(error_message=error_msg, error_details=error_details)
        db.session.commit()

        logger.error(
            f"Crawl task failed: {job_id}, error={error_msg}", exc_info=True)
        raise
