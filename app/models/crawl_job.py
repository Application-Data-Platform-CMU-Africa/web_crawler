"""
CrawlJob Model
Represents a crawl operation tracking
"""
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class CrawlJob(db.Model):
    """
    Tracks crawl job execution, status, and statistics
    """
    __tablename__ = 'crawl_jobs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Job Identification
    job_id = db.Column(db.String(255), unique=True, index=True, nullable=False,
                       comment='Unique job identifier (UUID or similar)')
    celery_task_id = db.Column(db.String(255), unique=True, index=True,
                               comment='Celery task ID for tracking')

    # Crawl Configuration
    site_id = db.Column(db.String(255), nullable=False, index=True,
                        comment='Site configuration ID (e.g., uganda-portal)')
    start_url = db.Column(db.Text, nullable=False,
                          comment='Starting URL for the crawl')
    crawler_type = db.Column(db.String(50), default='static',
                             comment='static, dynamic, api, etc.')

    # Options & Configuration
    options = db.Column(JSONB, default=dict,
                        comment='Crawl options (max_pages, test_mode, etc.)')

    # Status Tracking
    status = db.Column(db.String(50), default='pending', index=True, nullable=False,
                       comment='pending, running, completed, failed, cancelled')
    progress_percentage = db.Column(db.Float, default=0.0,
                                    comment='Progress 0-100')
    current_page = db.Column(db.String(500),
                             comment='Currently processing page URL')

    # Statistics
    stats = db.Column(JSONB, default=dict,
                      comment='Crawl statistics (pages_crawled, datasets_found, etc.)')
    pages_crawled = db.Column(db.Integer, default=0)
    datasets_found = db.Column(db.Integer, default=0)
    datasets_created = db.Column(db.Integer, default=0)
    datasets_updated = db.Column(db.Integer, default=0)
    datasets_unchanged = db.Column(db.Integer, default=0)
    duplicates_skipped = db.Column(db.Integer, default=0)
    errors_count = db.Column(db.Integer, default=0)

    # Error Tracking
    error_message = db.Column(db.Text, nullable=True,
                              comment='Error message if job failed')
    error_details = db.Column(JSONB, nullable=True,
                              comment='Detailed error information')

    # Timestamps
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True,
                           comment='When crawl actually started')
    completed_at = db.Column(db.DateTime, nullable=True,
                             comment='When crawl finished (success or failure)')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # User Tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                           nullable=True, index=True)
    user = db.relationship('User', back_populates='crawl_jobs')

    # Relationships
    datasets = db.relationship('Dataset', back_populates='crawl_job',
                               cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<CrawlJob {self.job_id}: {self.status}>'

    def to_dict(self, include_datasets=False):
        """Convert crawl job to dictionary for API responses"""
        duration = None
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            duration = (datetime.utcnow() - self.started_at).total_seconds()

        data = {
            'id': self.id,
            'job_id': self.job_id,
            'celery_task_id': self.celery_task_id,
            'site_id': self.site_id,
            'start_url': self.start_url,
            'crawler_type': self.crawler_type,
            'options': self.options or {},
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'current_page': self.current_page,
            'statistics': {
                'pages_crawled': self.pages_crawled,
                'datasets_found': self.datasets_found,
                'datasets_created': self.datasets_created,
                'datasets_updated': self.datasets_updated,
                'datasets_unchanged': self.datasets_unchanged,
                'duplicates_skipped': self.duplicates_skipped,
                'errors_count': self.errors_count,
            },
            'error_message': self.error_message,
            'duration_seconds': duration,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat(),
        }

        if include_datasets:
            data['datasets'] = [dataset.to_dict() for dataset in self.datasets]

        return data

    def start(self):
        """Mark job as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, stats: dict = None):
        """Mark job as completed successfully"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        if stats:
            self.update_stats(stats)
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str, error_details: dict = None):
        """Mark job as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details
        self.updated_at = datetime.utcnow()

    def cancel(self):
        """Mark job as cancelled"""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_progress(self, percentage: float, current_page: str = None):
        """Update job progress"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if current_page:
            self.current_page = current_page
        self.updated_at = datetime.utcnow()

    def update_stats(self, stats: dict):
        """Update job statistics"""
        self.stats = stats
        self.pages_crawled = stats.get('pages_crawled', 0)
        self.datasets_found = stats.get('datasets_found', 0)
        self.datasets_created = stats.get('datasets_created', 0)
        self.datasets_updated = stats.get('datasets_updated', 0)
        self.datasets_unchanged = stats.get('datasets_unchanged', 0)
        self.duplicates_skipped = stats.get('duplicates_skipped', 0)
        self.errors_count = stats.get('errors', 0)
        self.updated_at = datetime.utcnow()

    @classmethod
    def find_by_job_id(cls, job_id: str):
        """Find crawl job by job_id"""
        return cls.query.filter_by(job_id=job_id).first()

    @classmethod
    def find_by_celery_task_id(cls, task_id: str):
        """Find crawl job by Celery task ID"""
        return cls.query.filter_by(celery_task_id=task_id).first()

    @classmethod
    def get_recent_jobs(cls, limit: int = 10):
        """Get most recent crawl jobs"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_running_jobs(cls):
        """Get all currently running jobs"""
        return cls.query.filter_by(status='running').all()
