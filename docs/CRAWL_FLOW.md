# Web Crawler End-to-End Flow Documentation

This document describes the complete end-to-end flow of the web crawler application, from API endpoints to the actual crawling process.

## Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────┐
│       Flask API Endpoint            │
│   /api/v1/crawl/start               │
└──────┬──────────────────────────────┘
       │ 1. Validate request
       │ 2. Create CrawlJob in DB
       ▼
┌─────────────────────────────────────┐
│      Celery Task Queue              │
│   run_crawl.apply_async()           │
└──────┬──────────────────────────────┘
       │ Background execution
       ▼
┌─────────────────────────────────────┐
│      Celery Worker                  │
│   app.tasks.run_crawl               │
└──────┬──────────────────────────────┘
       │ Orchestrate crawl
       ▼
┌─────────────────────────────────────┐
│    CrawlerService                   │
│   Manage crawl lifecycle            │
└──────┬──────────────────────────────┘
       │ Execute crawler
       ▼
┌─────────────────────────────────────┐
│  BaseCrawler (StaticCrawler)        │
│  - Scrapy spider for static sites   │
│  - Selenium for dynamic sites       │
└──────┬──────────────────────────────┘
       │ Callbacks
       ▼
┌─────────────────────────────────────┐
│     Database Updates                │
│  - Update job progress              │
│  - Save datasets                    │
│  - Track errors                     │
└─────────────────────────────────────┘
```

## Flow Details

### 1. Starting a Crawl Job

**Endpoint:** `POST /api/v1/crawl/start`

**Request:**
```json
{
  "site_id": "1",
  "options": {
    "max_pages": 100,
    "test_mode": false
  }
}
```

**Process:**
1. API endpoint validates the request (`app/api/v1/crawl.py`)
2. Loads site configuration from `configs/config.json`
3. Creates a new `CrawlJob` record in the database
4. Queues a Celery task `run_crawl` with the job details
5. Returns 202 Accepted with job ID

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid-string",
    "celery_task_id": "task-id",
    "status": "pending",
    "site_id": "1",
    "start_url": "http://catalog.data.ug/dataset",
    "options": {...}
  },
  "message": "Crawl job queued successfully"
}
```

### 2. Celery Task Execution

**File:** `app/tasks/crawl_tasks.py`

**Process:**
1. Celery worker picks up the `run_crawl` task
2. Retrieves the `CrawlJob` from database
3. Updates job status to "running"
4. Initializes `CrawlerService`
5. Executes the crawl
6. Updates job with final statistics
7. Marks job as "completed" or "failed"

**Key Features:**
- Automatic error handling and job status updates
- Progress tracking via database updates
- Exception handling with detailed error logging

### 3. Crawler Service

**File:** `app/services/crawler_service.py`

**Responsibilities:**
- Load site configuration
- Validate crawl request
- Initialize appropriate crawler (Static/Dynamic)
- Set up progress callbacks
- Coordinate dataset saving

**Callbacks:**
- `_on_progress()`: Updates job statistics in database
- `_on_dataset_found()`: Checks duplicates and saves datasets
- `_on_error()`: Logs errors

### 4. Crawler Execution

**File:** `app/crawlers/static_crawler.py`

**For Static Sites (Scrapy):**
1. Initialize Scrapy spider with site configuration
2. Apply crawl rules (pagination, dataset pages)
3. Extract data using CSS selectors
4. Process and validate datasets
5. Report progress via callbacks

**For Dynamic Sites (Coming Soon):**
- Uses Selenium for JavaScript-heavy sites
- Waits for dynamic content to load
- Similar extraction and processing

### 5. Dataset Processing

**File:** `app/crawlers/data_processor.py`

**Process:**
1. Extract title, description, tags from HTML
2. Clean and normalize text
3. Generate content hash for duplicate detection
4. Map tags to categories and SDGs
5. Validate dataset structure

### 6. Database Updates

**Models:**
- `CrawlJob` (`app/models/crawl_job.py`): Track job status and statistics
- `Dataset` (`app/models/dataset.py`): Store crawled datasets

**Real-time Updates:**
- Job progress (pages crawled, datasets found)
- Current page being processed
- Error counts and messages
- Completion timestamps

### 7. Monitoring Job Status

**Endpoints:**

#### Get Single Job
```
GET /api/v1/crawl/jobs/{job_id}?include_datasets=false
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "running",
    "progress_percentage": 45.5,
    "current_page": "http://...",
    "statistics": {
      "pages_crawled": 45,
      "datasets_found": 23,
      "datasets_created": 20,
      "duplicates_skipped": 3,
      "errors_count": 0
    },
    "created_at": "2024-01-13T10:30:00",
    "started_at": "2024-01-13T10:30:05",
    "duration_seconds": 125.5
  }
}
```

#### List All Jobs
```
GET /api/v1/crawl/jobs?page=1&limit=20&status=running
```

**Response:**
```json
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
```

### 8. Cancel a Job

**Endpoint:** `POST /api/v1/crawl/jobs/{job_id}/cancel`

**Process:**
1. Validates job exists and can be cancelled
2. Revokes the Celery task
3. Updates job status to "cancelled"

## Running the System

### 1. Start the Flask Application
```bash
python run.py
```

### 2. Start Celery Worker
```bash
celery -A celery_worker.celery_app worker -Q crawl --loglevel=info
```

### 3. Start Redis (Required for Celery)
```bash
redis-server
```

### 4. Make API Request
```bash
curl -X POST http://localhost:5000/api/v1/crawl/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "1",
    "options": {
      "max_pages": 10,
      "test_mode": false
    }
  }'
```

## Testing the Flow

### Automated Test Script
```bash
# Update API key in test_crawl_flow.py first
python test_crawl_flow.py
```

This script will:
1. Start a crawl job
2. Get job status
3. List all jobs
4. Monitor progress until completion

### Manual Testing

**1. Health Check:**
```bash
curl http://localhost:5000/api/v1/health
```

**2. Start Crawl:**
```bash
curl -X POST http://localhost:5000/api/v1/crawl/start \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"site_id": "1", "options": {"max_pages": 5}}'
```

**3. Check Status:**
```bash
curl http://localhost:5000/api/v1/crawl/jobs/{job_id} \
  -H "X-API-Key: test-key"
```

## Configuration

### Site Configuration (`configs/config.json`)
```json
{
  "id": 1,
  "start_url": "http://catalog.data.ug/dataset",
  "domain": "catalog.data.ug",
  "source_name": "DATA.UG",
  "rules": [...],
  "title_selector": "#content > div > h1::text",
  "description_selector": "...",
  "tags_selector": "...",
  "is_dynamic": false
}
```

### Crawl Options
- `max_pages`: Limit number of pages to crawl
- `test_mode`: Run in test mode (saves to JSON, not DB)

## Error Handling

### Job Failures
- Automatic status update to "failed"
- Error message and details stored in database
- Stack trace logged for debugging

### Retry Logic
- Scrapy auto-retries failed requests (3 times)
- Celery can be configured for task retries
- Rate limiting and politeness delays

## Database Schema

### CrawlJob Table
- `job_id`: Unique UUID
- `celery_task_id`: Celery task identifier
- `status`: pending, running, completed, failed, cancelled
- `progress_percentage`: 0-100
- `statistics`: JSON with crawl stats
- Timestamps: created_at, started_at, completed_at

### Dataset Table
- `title`, `description`, `url`
- `content_hash`: For duplicate detection
- `tags`: Array of tags
- `crawl_job_id`: Foreign key to CrawlJob
- Relationships: countries, categories, SDGs

## Performance Considerations

### Concurrent Requests
- Scrapy: 4 concurrent requests per domain
- Auto-throttle enabled for adaptive delays
- Respects robots.txt

### Database Optimization
- Batch inserts (10 datasets at a time)
- Indexes on job_id, status, created_at
- Lazy loading for relationships

### Memory Management
- Datasets buffered before batch save
- Scrapy memory-efficient streaming

## Next Steps

1. **Dynamic Crawler**: Implement Selenium-based crawler for JavaScript sites
2. **Scheduling**: Add cron jobs for periodic crawls
3. **Webhooks**: Notify on job completion
4. **Analytics**: Dashboard for crawl statistics
5. **API Rate Limiting**: Per-user quotas
6. **Dataset Deduplication**: Enhanced duplicate detection

## Files Modified/Created

### New Files
- `app/tasks/crawl_tasks.py` - Celery task for crawling
- `test_crawl_flow.py` - End-to-end test script
- `CRAWL_FLOW.md` - This documentation

### Updated Files
- `app/api/v1/crawl.py` - Implemented all endpoints
- `app/services/crawler_service.py` - Database integration
- `app/tasks/__init__.py` - Export crawl task

### Existing Files (No Changes)
- `app/crawlers/base_crawler.py` - Base crawler class
- `app/crawlers/static_crawler.py` - Static site crawler
- `app/models/crawl_job.py` - Job model
- `app/models/dataset.py` - Dataset model

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Celery worker output
3. Check database for job status
4. Enable debug mode for detailed errors
