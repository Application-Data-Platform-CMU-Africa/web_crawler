"""
Dataset Model
Represents a crawled dataset from data portals
"""
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Dataset(db.Model):
    """
    Dataset model with two-hash strategy:
    - hash: URL-based primary identifier (prevents duplicates)
    - content_hash: Metadata-based change detector (tracks updates)
    """
    __tablename__ = 'datasets'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Hash Strategy - Duplicate Detection & Update Tracking
    hash = db.Column(db.String(64), unique=True, index=True, nullable=False,
                     comment='SHA256 of URL - primary identifier')
    content_hash = db.Column(db.String(64), index=True, nullable=True,
                            comment='SHA256 of title+description+tags - change detection')

    # Core Metadata
    title = db.Column(db.Text, nullable=False, index=True)
    description = db.Column(db.Text)
    url = db.Column(db.Text, nullable=False)

    # Source Information
    source = db.Column(db.String(255), index=True,
                      comment='Source portal name (e.g., Uganda Data Portal)')
    source_id = db.Column(db.String(255),
                         comment='Original ID from source portal')

    # Classification
    tags = db.Column(JSONB, default=list,
                    comment='List of tags/keywords')
    file_types = db.Column(JSONB, default=list,
                          comment='Available file formats (CSV, JSON, etc.)')

    # Geographic & Temporal
    country_code = db.Column(db.String(3), index=True,
                            comment='ISO 3166-1 alpha-3 country code')
    temporal_coverage_start = db.Column(db.Date, nullable=True)
    temporal_coverage_end = db.Column(db.Date, nullable=True)

    # Publisher Information
    publisher = db.Column(db.String(255))
    publisher_email = db.Column(db.String(255))
    license = db.Column(db.String(255))

    # Resources/Downloads
    resources = db.Column(JSONB, default=list,
                         comment='List of downloadable resources with URLs and formats')
    download_count = db.Column(db.Integer, default=0)

    # Status & Visibility
    status = db.Column(db.String(50), default='active', index=True,
                      comment='active, archived, deleted')
    is_published = db.Column(db.Boolean, default=True, index=True)
    quality_score = db.Column(db.Float, nullable=True,
                             comment='Data quality score 0-100')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow, nullable=False)
    last_crawled_at = db.Column(db.DateTime, nullable=True,
                               comment='Last time we checked this URL')
    published_date = db.Column(db.DateTime, nullable=True,
                              comment='When dataset was published on source portal')

    # Relationships
    crawl_job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id', ondelete='SET NULL'),
                            nullable=True, index=True)
    crawl_job = db.relationship('CrawlJob', back_populates='datasets')

    # Many-to-many relationships (will be defined when creating association tables)
    categories = db.relationship('Category', secondary='dataset_categories',
                                back_populates='datasets', lazy='dynamic')
    sdgs = db.relationship('SDG', secondary='dataset_sdgs',
                          back_populates='datasets', lazy='dynamic')

    def __repr__(self):
        return f'<Dataset {self.id}: {self.title[:50]}>'

    def to_dict(self, include_relationships=False):
        """Convert dataset to dictionary for API responses"""
        data = {
            'id': self.id,
            'hash': self.hash,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'source_id': self.source_id,
            'tags': self.tags or [],
            'file_types': self.file_types or [],
            'country_code': self.country_code,
            'temporal_coverage': {
                'start': self.temporal_coverage_start.isoformat() if self.temporal_coverage_start else None,
                'end': self.temporal_coverage_end.isoformat() if self.temporal_coverage_end else None,
            },
            'publisher': self.publisher,
            'publisher_email': self.publisher_email,
            'license': self.license,
            'resources': self.resources or [],
            'download_count': self.download_count,
            'status': self.status,
            'is_published': self.is_published,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_crawled_at': self.last_crawled_at.isoformat() if self.last_crawled_at else None,
            'published_date': self.published_date.isoformat() if self.published_date else None,
        }

        if include_relationships:
            data['categories'] = [cat.to_dict() for cat in self.categories]
            data['sdgs'] = [sdg.to_dict() for sdg in self.sdgs]
            if self.crawl_job:
                data['crawl_job'] = self.crawl_job.to_dict()

        return data

    @classmethod
    def find_by_hash(cls, hash_value: str):
        """Find dataset by primary hash (URL-based)"""
        return cls.query.filter_by(hash=hash_value).first()

    @classmethod
    def find_by_url(cls, url: str):
        """Find dataset by URL"""
        return cls.query.filter_by(url=url).first()

    def has_content_changed(self, new_content_hash: str) -> bool:
        """Check if content has changed based on content hash"""
        return self.content_hash != new_content_hash

    def update_metadata(self, **kwargs):
        """Update dataset metadata and set updated_at"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def mark_as_crawled(self):
        """Update last_crawled_at timestamp"""
        self.last_crawled_at = datetime.utcnow()
