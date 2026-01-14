"""Initial schema with two-hash strategy

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_prefix', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)

    # Create countries table
    op.create_table('countries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('code_alpha2', sa.String(length=2), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('continent', sa.String(length=50), nullable=True),
        sa.Column('flag_emoji', sa.String(length=10), nullable=True),
        sa.Column('has_data_portal', sa.Boolean(), nullable=True),
        sa.Column('portal_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_countries_code'), 'countries', ['code'], unique=True)
    op.create_index(op.f('ix_countries_code_alpha2'), 'countries', ['code_alpha2'], unique=True)
    op.create_index(op.f('ix_countries_continent'), 'countries', ['continent'], unique=False)
    op.create_index(op.f('ix_countries_is_active'), 'countries', ['is_active'], unique=False)
    op.create_index(op.f('ix_countries_name'), 'countries', ['name'], unique=False)
    op.create_index(op.f('ix_countries_region'), 'countries', ['region'], unique=False)

    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_is_active'), 'categories', ['is_active'], unique=False)
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)

    # Create sdgs table
    op.create_table('sdgs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdgs_is_active'), 'sdgs', ['is_active'], unique=False)
    op.create_index(op.f('ix_sdgs_number'), 'sdgs', ['number'], unique=True)

    # Create crawl_jobs table
    op.create_table('crawl_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=False),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('site_id', sa.String(length=255), nullable=False),
        sa.Column('start_url', sa.Text(), nullable=False),
        sa.Column('crawler_type', sa.String(length=50), nullable=True),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('current_page', sa.String(length=500), nullable=True),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pages_crawled', sa.Integer(), nullable=True),
        sa.Column('datasets_found', sa.Integer(), nullable=True),
        sa.Column('datasets_created', sa.Integer(), nullable=True),
        sa.Column('datasets_updated', sa.Integer(), nullable=True),
        sa.Column('datasets_unchanged', sa.Integer(), nullable=True),
        sa.Column('duplicates_skipped', sa.Integer(), nullable=True),
        sa.Column('errors_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawl_jobs_celery_task_id'), 'crawl_jobs', ['celery_task_id'], unique=True)
    op.create_index(op.f('ix_crawl_jobs_created_by'), 'crawl_jobs', ['created_by'], unique=False)
    op.create_index(op.f('ix_crawl_jobs_job_id'), 'crawl_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_crawl_jobs_site_id'), 'crawl_jobs', ['site_id'], unique=False)
    op.create_index(op.f('ix_crawl_jobs_status'), 'crawl_jobs', ['status'], unique=False)

    # Create datasets table with TWO-HASH STRATEGY
    op.create_table('datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        # Two-hash strategy for duplicate detection and update tracking
        sa.Column('hash', sa.String(length=64), nullable=False, comment='SHA256 of URL - primary identifier'),
        sa.Column('content_hash', sa.String(length=64), nullable=True, comment='SHA256 of title+description+tags - change detection'),
        # Core metadata
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        # Classification
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('file_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Geographic & temporal
        sa.Column('country_code', sa.String(length=3), nullable=True),
        sa.Column('temporal_coverage_start', sa.Date(), nullable=True),
        sa.Column('temporal_coverage_end', sa.Date(), nullable=True),
        # Publisher
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publisher_email', sa.String(length=255), nullable=True),
        sa.Column('license', sa.String(length=255), nullable=True),
        # Resources
        sa.Column('resources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        # Status
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_crawled_at', sa.DateTime(), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        # Relationships
        sa.Column('crawl_job_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_datasets_content_hash'), 'datasets', ['content_hash'], unique=False)
    op.create_index(op.f('ix_datasets_country_code'), 'datasets', ['country_code'], unique=False)
    op.create_index(op.f('ix_datasets_crawl_job_id'), 'datasets', ['crawl_job_id'], unique=False)
    op.create_index(op.f('ix_datasets_hash'), 'datasets', ['hash'], unique=True)
    op.create_index(op.f('ix_datasets_is_published'), 'datasets', ['is_published'], unique=False)
    op.create_index(op.f('ix_datasets_source'), 'datasets', ['source'], unique=False)
    op.create_index(op.f('ix_datasets_status'), 'datasets', ['status'], unique=False)
    op.create_index(op.f('ix_datasets_title'), 'datasets', ['title'], unique=False)

    # Create association table: dataset_categories
    op.create_table('dataset_categories',
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id', 'category_id')
    )

    # Create association table: dataset_sdgs
    op.create_table('dataset_sdgs',
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('sdg_id', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sdg_id'], ['sdgs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id', 'sdg_id')
    )


def downgrade():
    op.drop_table('dataset_sdgs')
    op.drop_table('dataset_categories')
    op.drop_table('datasets')
    op.drop_table('crawl_jobs')
    op.drop_table('sdgs')
    op.drop_table('categories')
    op.drop_table('countries')
    op.drop_table('api_keys')
    op.drop_table('users')
