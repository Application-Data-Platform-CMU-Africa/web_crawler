# World-Class Dataset Crawler - Design Document

**Version:** 2.0
**Date:** January 13, 2026
**Branch:** feat/advanced-crawler
**Status:** Design Phase

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [API Design](#api-design)
6. [Background Job Processing](#background-job-processing)
7. [Authentication & Security](#authentication--security)
8. [Project Structure](#project-structure)
9. [Data Flow](#data-flow)
10. [Deployment Strategy](#deployment-strategy)
11. [Monitoring & Observability](#monitoring--observability)
12. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

### Current State (v1.0)
- CLI-based web crawler
- SQLite database
- Manual operation via command-line interface
- Synchronous crawling (blocking operations)
- Limited scalability and monitoring

### Target State (v2.0)
- **RESTful Flask API** with async background processing
- **PostgreSQL database** for production-grade data persistence
- **Celery + Redis** task queue for scalable crawling
- **API Key authentication** for secure access
- **Real-time progress tracking** and job monitoring
- **Docker-ready** with Kubernetes deployment capability

### Key Objectives
1. ✅ Transform CLI tool → Production-ready API service
2. ✅ Enable concurrent multi-site crawling
3. ✅ Provide real-time job status and progress tracking
4. ✅ Support the new data structure with ObjectID references
5. ✅ Scale horizontally with container orchestration
6. ✅ Implement comprehensive monitoring and logging

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Applications                      │
│                    (Web UI, CLI, External APIs)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask API Server                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth Layer   │  │  API Routes  │  │  Validators  │          │
│  │ (API Keys)   │  │  (Blueprints)│  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────────────────────────────────────────┐          │
│  │           Business Logic Layer                    │          │
│  │  • Crawler Service  • Classifier Service          │          │
│  │  • Publisher Service • Job Manager                │          │
│  └──────────────────────────────────────────────────┘          │
└───────────┬─────────────────────────────┬───────────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────┐    ┌──────────────────────────┐
│  PostgreSQL Database  │    │   Celery Workers         │
│                       │    │  ┌────────────────────┐  │
│  • Datasets           │    │  │ Crawl Jobs         │  │
│  • Crawl Jobs         │    │  │ Classify Jobs      │  │
│  • API Keys           │    │  │ Publish Jobs       │  │
│  • Categories/SDGs    │    │  └────────────────────┘  │
│  • Audit Logs         │    │         ▲                │
└───────────────────────┘    └─────────┼────────────────┘
                                       │
                             ┌─────────▼────────┐
                             │   Redis Queue    │
                             │  • Task Queue    │
                             │  • Result Store  │
                             │  • Cache         │
                             └──────────────────┘
```

### Component Responsibilities

#### **Flask API Server**
- Handle HTTP requests/responses
- Authenticate requests via API keys
- Validate input data
- Dispatch background jobs to Celery
- Serve real-time status updates

#### **Celery Workers**
- Execute long-running crawl operations
- Process classification jobs (OpenAI integration)
- Handle data publishing to external APIs
- Update job status in real-time

#### **PostgreSQL Database**
- Persistent storage for datasets and metadata
- Job history and status tracking
- User/API key management
- Relational integrity with foreign keys

#### **Redis**
- Task queue for Celery
- Result backend for job status
- Caching layer for frequently accessed data
- Session storage (optional)

---

## 3. Technology Stack

### Core Framework
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Flask | 3.0+ | REST API server |
| **WSGI Server** | Gunicorn | 21.0+ | Production web server |
| **Task Queue** | Celery | 5.3+ | Background job processing |
| **Message Broker** | Redis | 7.0+ | Task queue & caching |
| **Database** | PostgreSQL | 15+ | Primary data store |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Migration Tool** | Alembic | 1.13+ | Database migrations |

### Supporting Libraries
| Library | Purpose |
|---------|---------|
| `Flask-CORS` | Cross-origin resource sharing |
| `Flask-Migrate` | Database migration management |
| `Flask-SQLAlchemy` | Flask-SQLAlchemy integration |
| `marshmallow` | Serialization/deserialization |
| `python-dotenv` | Environment variable management |
| `psycopg2-binary` | PostgreSQL adapter |
| `redis-py` | Redis client |
| `celery[redis]` | Celery with Redis support |
| `scrapy` | Web crawling framework |
| `beautifulsoup4` | HTML parsing |
| `requests` | HTTP client |
| `openai` | GPT-based classification |
| `flask-limiter` | Rate limiting |
| `flask-swagger-ui` | API documentation UI |

### Development Tools
| Tool | Purpose |
|------|---------|
| `pytest` | Unit/integration testing |
| `pytest-cov` | Code coverage |
| `black` | Code formatting |
| `flake8` | Linting |
| `mypy` | Type checking |
| `pre-commit` | Git hooks |

---

## 4. Database Design

### Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   Categories    │         │      SDGs       │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ name            │         │ sdg_number      │
│ description     │         │ name            │
│ created_at      │         │ description     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │ Many-to-Many             │ Many-to-Many
         │                           │
         └───────────┬───────────────┘
                     │
              ┌──────▼──────────┐
              │   Datasets      │
              ├─────────────────┤
              │ id (PK)         │
              │ title           │
              │ description     │
              │ extension       │
              │ source          │
              │ tags (JSONB)    │
              │ file_references │
              │ file_size_mb    │
              │ is_link         │
              │ is_private      │
              │ is_deleted      │
              │ is_active       │
              │ comments_count  │
              │ likes_count     │
              │ downloads_count │
              │ owner_id (FK)   │
              │ crawl_job_id(FK)│
              │ created_at      │
              │ updated_at      │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │                           │
    ┌────▼────────┐          ┌──────▼────────┐
    │  Countries  │          │  Crawl Jobs   │
    ├─────────────┤          ├───────────────┤
    │ id (PK)     │          │ id (PK)       │
    │ name        │          │ job_id (UUID) │
    │ code        │          │ site_name     │
    │ region      │          │ start_url     │
    └─────────────┘          │ status        │
                             │ progress      │
    ┌─────────────┐          │ total_found   │
    │  API Keys   │          │ total_saved   │
    ├─────────────┤          │ error_message │
    │ id (PK)     │          │ started_at    │
    │ key_hash    │          │ completed_at  │
    │ name        │          │ created_by(FK)│
    │ is_active   │          └───────────────┘
    │ created_at  │
    │ last_used   │          ┌───────────────┐
    │ user_id(FK) │          │  Audit Logs   │
    └─────────────┘          ├───────────────┤
                             │ id (PK)       │
    ┌─────────────┐          │ user_id (FK)  │
    │   Users     │          │ action        │
    ├─────────────┤          │ resource_type │
    │ id (PK)     │◄─────────│ resource_id   │
    │ email       │          │ ip_address    │
    │ name        │          │ timestamp     │
    │ is_admin    │          │ details(JSONB)│
    │ created_at  │          └───────────────┘
    └─────────────┘
```

### Table Schemas

#### **datasets**
```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    extension VARCHAR(50),
    original_file_name VARCHAR(500),
    file_references TEXT[],  -- Array of URLs/paths
    file_size_mb DECIMAL(10, 2),
    source VARCHAR(255),
    tags JSONB DEFAULT '[]',
    is_link BOOLEAN DEFAULT true,
    is_private BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    comments_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    owner_id UUID REFERENCES users(id),
    crawl_job_id UUID REFERENCES crawl_jobs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_datasets_title ON datasets(title);
CREATE INDEX idx_datasets_source ON datasets(source);
CREATE INDEX idx_datasets_is_active ON datasets(is_active);
CREATE INDEX idx_datasets_tags ON datasets USING GIN(tags);
CREATE INDEX idx_datasets_created_at ON datasets(created_at DESC);
```

#### **crawl_jobs**
```sql
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) UNIQUE NOT NULL,  -- Celery task ID
    site_name VARCHAR(255) NOT NULL,
    start_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    progress INTEGER DEFAULT 0,  -- Percentage 0-100
    total_found INTEGER DEFAULT 0,
    total_saved INTEGER DEFAULT 0,
    error_message TEXT,
    config JSONB,  -- Store crawler configuration
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
```

#### **categories**
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **sdgs**
```sql
CREATE TABLE sdgs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sdg_number INTEGER UNIQUE NOT NULL CHECK (sdg_number BETWEEN 1 AND 17),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **dataset_categories** (Junction Table)
```sql
CREATE TABLE dataset_categories (
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (dataset_id, category_id)
);
```

#### **dataset_sdgs** (Junction Table)
```sql
CREATE TABLE dataset_sdgs (
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    sdg_id UUID REFERENCES sdgs(id) ON DELETE CASCADE,
    PRIMARY KEY (dataset_id, sdg_id)
);
```

#### **dataset_countries** (Junction Table)
```sql
CREATE TABLE dataset_countries (
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    country_id UUID REFERENCES countries(id) ON DELETE CASCADE,
    PRIMARY KEY (dataset_id, country_id)
);
```

#### **countries**
```sql
CREATE TABLE countries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(3) UNIQUE NOT NULL,  -- ISO 3166-1 alpha-3
    region VARCHAR(100),  -- e.g., "East Africa"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    is_admin BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **api_keys**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash of the key
    name VARCHAR(255) NOT NULL,  -- Friendly name for the key
    is_active BOOLEAN DEFAULT true,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
```

#### **audit_logs**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,  -- e.g., "crawl_started", "dataset_created"
    resource_type VARCHAR(50),  -- e.g., "dataset", "crawl_job"
    resource_id UUID,
    ip_address INET,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

---

## 5. API Design

### Base URL
```
http://localhost:5000/api/v1
```

### Authentication
All endpoints require an API key in the header:
```http
X-API-Key: your-api-key-here
```

### Response Format
All responses follow this structure:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2026-01-13T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2026-01-13T10:30:00Z"
}
```

### API Endpoints

#### **1. Health & Status**

##### `GET /health`
Check API health status
```json
Response 200:
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "celery": "available"
  }
}
```

##### `GET /stats`
Get system statistics
```json
Response 200:
{
  "success": true,
  "data": {
    "total_datasets": 1250,
    "total_crawl_jobs": 45,
    "active_jobs": 3,
    "datasets_today": 87,
    "uptime_seconds": 3600
  }
}
```

---

#### **2. Crawl Management**

##### `POST /crawl/start`
Start a new crawl job
```json
Request:
{
  "site_id": "uuid-or-config-id",
  "start_url": "http://catalog.data.ug/dataset",
  "options": {
    "test_mode": false,
    "max_pages": 100,
    "country_filter": "Rwanda"
  }
}

Response 202:
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Crawl job queued successfully"
  }
}
```

##### `GET /crawl/jobs`
List all crawl jobs (with pagination)
```json
Query params: ?page=1&limit=20&status=running

Response 200:
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "uuid",
        "job_id": "celery-task-id",
        "site_name": "DATA.UG",
        "status": "running",
        "progress": 45,
        "total_found": 120,
        "total_saved": 98,
        "started_at": "2026-01-13T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

##### `GET /crawl/jobs/{job_id}`
Get specific job details
```json
Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "job_id": "celery-task-id",
    "site_name": "DATA.UG",
    "start_url": "http://catalog.data.ug/dataset",
    "status": "running",
    "progress": 45,
    "total_found": 120,
    "total_saved": 98,
    "error_message": null,
    "started_at": "2026-01-13T10:00:00Z",
    "config": { ... }
  }
}
```

##### `POST /crawl/jobs/{job_id}/cancel`
Cancel a running job
```json
Response 200:
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "cancelled",
    "message": "Job cancelled successfully"
  }
}
```

##### `GET /crawl/jobs/{job_id}/logs`
Get job logs (real-time)
```json
Response 200:
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2026-01-13T10:05:00Z",
        "level": "INFO",
        "message": "Parsing: http://catalog.data.ug/dataset/example-1"
      },
      {
        "timestamp": "2026-01-13T10:05:02Z",
        "level": "INFO",
        "message": "Successfully stored: Example Dataset 1"
      }
    ]
  }
}
```

---

#### **3. Dataset Management**

##### `GET /datasets`
List all datasets (with filtering & pagination)
```json
Query params: ?page=1&limit=50&source=DATA.UG&is_link=true

Response 200:
{
  "success": true,
  "data": {
    "datasets": [
      {
        "id": "uuid",
        "title": "Rwanda Population Statistics 2024",
        "description": "Comprehensive population data...",
        "extension": "csv",
        "source": "National Institute of Statistics Rwanda",
        "tags": ["population", "demographics"],
        "is_link": false,
        "file_size_mb": 2.5,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1250,
      "pages": 25
    }
  }
}
```

##### `GET /datasets/{id}`
Get specific dataset details
```json
Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Rwanda Population Statistics 2024",
    "description": "Comprehensive population data...",
    "extension": "csv",
    "categories": [
      {"id": "uuid", "name": "Demographics"}
    ],
    "countries": [
      {"id": "uuid", "name": "Rwanda", "code": "RWA"}
    ],
    "sdgs": [
      {"id": "uuid", "sdg_number": 1, "name": "No Poverty"}
    ],
    "file_references": ["http://example.com/data.csv"],
    "source": "National Institute of Statistics Rwanda",
    "tags": ["population", "demographics"],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

##### `POST /datasets`
Manually create a dataset
```json
Request:
{
  "title": "Manual Dataset",
  "description": "Description here",
  "file_references": ["http://example.com/data.csv"],
  "source": "Manual Entry",
  "tags": ["test"],
  "is_link": true
}

Response 201:
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Manual Dataset",
    "created_at": "2026-01-13T10:30:00Z"
  }
}
```

##### `PATCH /datasets/{id}`
Update dataset metadata
```json
Request:
{
  "description": "Updated description",
  "tags": ["updated", "tags"]
}

Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "updated_at": "2026-01-13T10:30:00Z"
  }
}
```

##### `DELETE /datasets/{id}`
Soft delete a dataset
```json
Response 200:
{
  "success": true,
  "message": "Dataset marked as deleted"
}
```

---

#### **4. Classification**

##### `POST /classify/dataset/{id}`
Classify a single dataset by SDGs
```json
Response 202:
{
  "success": true,
  "data": {
    "task_id": "celery-task-id",
    "message": "Classification job queued"
  }
}
```

##### `POST /classify/batch`
Classify multiple datasets
```json
Request:
{
  "dataset_ids": ["uuid1", "uuid2", "uuid3"],
  "options": {
    "overwrite_existing": false
  }
}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "celery-task-id",
    "total_queued": 3
  }
}
```

---

#### **5. Publishing**

##### `POST /publish/dataset/{id}`
Publish a dataset to external API
```json
Request:
{
  "target": "production",  // or "test"
  "passcode": "your-passcode"
}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "celery-task-id",
    "message": "Publish job queued"
  }
}
```

##### `POST /publish/batch`
Publish multiple datasets
```json
Request:
{
  "dataset_ids": ["uuid1", "uuid2"],
  "target": "test",
  "passcode": "your-passcode"
}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "celery-task-id",
    "total_queued": 2
  }
}
```

---

#### **6. Configuration**

##### `GET /config/sites`
List configured crawl sites
```json
Response 200:
{
  "success": true,
  "data": {
    "sites": [
      {
        "id": "uuid",
        "name": "Uganda Data Portal",
        "start_url": "http://catalog.data.ug/dataset",
        "domain": "catalog.data.ug",
        "is_dynamic": false
      }
    ]
  }
}
```

##### `POST /config/sites`
Add a new crawl site configuration
```json
Request:
{
  "name": "New Data Portal",
  "start_url": "http://example.com/datasets",
  "domain": "example.com",
  "rules": [
    {
      "allow": "/dataset\\?page.*",
      "deny": ""
    }
  ],
  "selectors": {
    "title": "h1.title::text",
    "description": "div.description::text",
    "tags": "span.tag::text"
  },
  "is_dynamic": false
}

Response 201:
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "New Data Portal"
  }
}
```

---

#### **7. API Key Management** (Admin only)

##### `POST /admin/api-keys`
Generate a new API key
```json
Request:
{
  "name": "Production Key",
  "user_id": "uuid",
  "expires_in_days": 365
}

Response 201:
{
  "success": true,
  "data": {
    "api_key": "sk_live_abc123...",  // Only shown once
    "id": "uuid",
    "name": "Production Key",
    "expires_at": "2027-01-13T10:30:00Z"
  }
}
```

##### `GET /admin/api-keys`
List all API keys
```json
Response 200:
{
  "success": true,
  "data": {
    "api_keys": [
      {
        "id": "uuid",
        "name": "Production Key",
        "is_active": true,
        "last_used_at": "2026-01-13T09:00:00Z",
        "created_at": "2026-01-01T10:00:00Z"
      }
    ]
  }
}
```

##### `DELETE /admin/api-keys/{id}`
Revoke an API key
```json
Response 200:
{
  "success": true,
  "message": "API key revoked"
}
```

---

## 6. Background Job Processing

### Celery Task Architecture

```python
# Task Types
tasks/
├── crawl_tasks.py      # Crawling operations
├── classify_tasks.py   # SDG classification
├── publish_tasks.py    # External API publishing
└── maintenance_tasks.py # Cleanup, monitoring
```

### Task Examples

#### Crawl Task
```python
@celery.task(bind=True, name='crawl.site')
def crawl_site_task(self, job_id: str, config: dict):
    """
    Background task to crawl a website

    Args:
        job_id: UUID of the crawl job
        config: Crawl configuration dictionary
    """
    # Update job status to 'running'
    update_job_status(job_id, 'running')

    try:
        # Initialize crawler
        crawler = StaticSpider(config, job_id=job_id)

        # Run crawler with progress callback
        for progress in crawler.crawl():
            # Update progress in database
            update_job_progress(job_id, progress)

            # Update Celery task state
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress}
            )

        # Mark job as completed
        update_job_status(job_id, 'completed')

    except Exception as e:
        # Mark job as failed with error
        update_job_status(job_id, 'failed', error=str(e))
        raise
```

#### Classification Task
```python
@celery.task(bind=True, name='classify.dataset')
def classify_dataset_task(self, dataset_id: str):
    """
    Classify a dataset by SDGs using OpenAI
    """
    dataset = Dataset.query.get(dataset_id)

    # Call OpenAI API
    sdgs = classify_by_sdgs(
        title=dataset.title,
        description=dataset.description,
        tags=dataset.tags
    )

    # Update dataset with SDG associations
    for sdg_number in sdgs:
        sdg = SDG.query.filter_by(sdg_number=sdg_number).first()
        if sdg:
            dataset.sdgs.append(sdg)

    db.session.commit()
```

### Task Routing & Queues

```python
# celeryconfig.py
task_routes = {
    'crawl.*': {'queue': 'crawl'},
    'classify.*': {'queue': 'classify'},
    'publish.*': {'queue': 'publish'},
}

# Worker startup commands
# High priority crawl workers (2 instances)
celery -A app.celery worker -Q crawl -c 4 -n crawl1@%h

# Classification workers (1 instance)
celery -A app.celery worker -Q classify -c 2 -n classify1@%h

# Publish workers (1 instance)
celery -A app.celery worker -Q publish -c 2 -n publish1@%h
```

### Task Monitoring

```python
# Celery Flower (Web UI for monitoring)
celery -A app.celery flower --port=5555

# Access at: http://localhost:5555
```

---

## 7. Authentication & Security

### API Key Authentication

#### Key Generation
```python
import secrets
import hashlib

def generate_api_key():
    """Generate a secure API key"""
    # Generate random key
    key = f"sk_{'live' if PRODUCTION else 'test'}_{secrets.token_urlsafe(32)}"

    # Hash for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    return key, key_hash
```

#### Authentication Decorator
```python
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_API_KEY',
                    'message': 'API key required'
                }
            }), 401

        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Look up in database
        api_key_obj = APIKey.query.filter_by(
            key_hash=key_hash,
            is_active=True
        ).first()

        if not api_key_obj:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_API_KEY',
                    'message': 'Invalid or inactive API key'
                }
            }), 401

        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EXPIRED_API_KEY',
                    'message': 'API key has expired'
                }
            }), 401

        # Update last used timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        db.session.commit()

        # Attach user to request context
        request.current_user = api_key_obj.user

        return f(*args, **kwargs)

    return decorated_function
```

### Security Best Practices

1. **HTTPS Only** - Enforce SSL/TLS in production
2. **Rate Limiting** - Prevent abuse
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-API-Key'),
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/crawl/start', methods=['POST'])
@limiter.limit("10 per hour")
@require_api_key
def start_crawl():
    pass
```

3. **Input Validation** - Sanitize all inputs
4. **SQL Injection Prevention** - Use SQLAlchemy ORM
5. **CORS Configuration** - Restrict origins
6. **Audit Logging** - Track all operations

---

## 8. Project Structure

```
web_crawler/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration classes
│   ├── extensions.py            # Flask extensions (db, celery, etc.)
│   │
│   ├── api/                     # API blueprints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── crawl.py         # Crawl endpoints
│   │   │   ├── datasets.py      # Dataset endpoints
│   │   │   ├── classify.py      # Classification endpoints
│   │   │   ├── publish.py       # Publishing endpoints
│   │   │   ├── config.py        # Configuration endpoints
│   │   │   └── admin.py         # Admin endpoints
│   │   └── errors.py            # Error handlers
│   │
│   ├── models/                  # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── crawl_job.py
│   │   ├── category.py
│   │   ├── sdg.py
│   │   ├── country.py
│   │   ├── user.py
│   │   ├── api_key.py
│   │   └── audit_log.py
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── crawler_service.py
│   │   ├── classifier_service.py
│   │   ├── publisher_service.py
│   │   └── job_manager.py
│   │
│   ├── tasks/                   # Celery tasks
│   │   ├── __init__.py
│   │   ├── crawl_tasks.py
│   │   ├── classify_tasks.py
│   │   ├── publish_tasks.py
│   │   └── maintenance_tasks.py
│   │
│   ├── crawlers/                # Crawler implementations
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── static_crawler.py
│   │   └── dynamic_crawler.py
│   │
│   ├── schemas/                 # Marshmallow schemas
│   │   ├── __init__.py
│   │   ├── dataset_schema.py
│   │   ├── crawl_job_schema.py
│   │   └── api_response_schema.py
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── validators.py
│       ├── helpers.py
│       └── constants.py
│
├── migrations/                  # Alembic migrations
│   └── versions/
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_crawlers/
│
├── scripts/                     # Utility scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── generate_api_key.py
│
├── docker/                      # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
├── k8s/                         # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
│
├── docs/                        # Documentation
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
│
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── run.py                       # Application entry point
├── celery_worker.py             # Celery worker entry point
├── pytest.ini
├── DESIGN.md                    # This document
└── README.md
```

---

## 9. Data Flow

### Crawl Operation Flow

```
1. Client Request
   ↓
2. API Endpoint (/crawl/start)
   ↓
3. Validate Input & API Key
   ↓
4. Create CrawlJob Record (status: pending)
   ↓
5. Dispatch Celery Task
   ↓
6. Return 202 Accepted with job_id
   ↓

[Background Worker]
7. Celery Worker Picks Up Task
   ↓
8. Update CrawlJob (status: running)
   ↓
9. Initialize Scrapy Spider
   ↓
10. For Each Page:
    - Extract Data
    - Validate & Transform
    - Check for Duplicates
    - Create Dataset Record
    - Update Progress
    ↓
11. Update CrawlJob (status: completed)
    ↓
12. Send Completion Notification (optional)
```

### Classification Flow

```
1. Trigger Classification (API or automatic after crawl)
   ↓
2. Queue Celery Task
   ↓
3. For Each Dataset:
    - Prepare prompt
    - Call OpenAI API
    - Parse SDG numbers
    - Look up SDG records
    - Create associations
    ↓
4. Update Dataset with SDGs
   ↓
5. Mark as classified
```

### Publishing Flow

```
1. Client Request with Passcode
   ↓
2. Verify Passcode Hash
   ↓
3. Queue Publish Task
   ↓
4. For Each Dataset:
    - Authenticate with External API
    - Transform to target format
    - POST to external endpoint
    - Handle response
    - Update published status
    ↓
5. Log publish event
```

---

## 10. Deployment Strategy

### Phase 1: Local Development

#### Setup
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Set up PostgreSQL
createdb web_crawler_dev

# Run migrations
flask db upgrade

# Start Redis
redis-server

# Start Celery worker
celery -A app.celery worker --loglevel=info

# Start Flask app
flask run --debug
```

### Phase 2: Docker Containerization

#### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: web_crawler
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      DATABASE_URL: postgresql://crawler:${DB_PASSWORD}@postgres:5432/web_crawler
      REDIS_URL: redis://redis:6379/0
      FLASK_ENV: production
    depends_on:
      - postgres
      - redis
    ports:
      - "5000:5000"
    command: gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      DATABASE_URL: postgresql://crawler:${DB_PASSWORD}@postgres:5432/web_crawler
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: celery -A app.celery worker -Q crawl,classify,publish -c 4

  flower:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
    ports:
      - "5555:5555"
    command: celery -A app.celery flower --port=5555

volumes:
  postgres_data:
```

### Phase 3: Kubernetes Deployment

#### Key Components

1. **Deployments**
   - API Server (3 replicas)
   - Celery Workers (5 replicas)
   - Flower Monitor (1 replica)

2. **StatefulSets**
   - PostgreSQL (1 replica with persistent volume)
   - Redis (1 replica with persistent volume)

3. **Services**
   - API LoadBalancer
   - Internal services for postgres/redis

4. **ConfigMaps & Secrets**
   - Application configuration
   - Database credentials
   - API keys

5. **Ingress**
   - Route external traffic to API
   - TLS termination

#### Example Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler-api
  template:
    metadata:
      labels:
        app: crawler-api
    spec:
      containers:
      - name: api
        image: registry.example.com/crawler-api:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 11. Monitoring & Observability

### Logging

#### Structured Logging
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

# Configure
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log')
    ]
)
formatter = JSONFormatter()
for handler in logging.root.handlers:
    handler.setFormatter(formatter)
```

### Metrics

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
crawl_jobs_total = Counter(
    'crawl_jobs_total',
    'Total number of crawl jobs',
    ['status']
)

datasets_created_total = Counter(
    'datasets_created_total',
    'Total datasets created',
    ['source']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_crawl_jobs = Gauge(
    'active_crawl_jobs',
    'Number of currently active crawl jobs'
)

# Use in code
@app.route('/crawl/start', methods=['POST'])
def start_crawl():
    with api_request_duration.labels('POST', '/crawl/start').time():
        # ... logic ...
        crawl_jobs_total.labels(status='started').inc()
        active_crawl_jobs.inc()
```

### Health Checks

```python
@app.route('/health')
def health_check():
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    }

    all_healthy = all(checks.values())

    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if all_healthy else 503
```

### Alerting

**Alert Conditions:**
- API error rate > 5%
- Database connection failures
- Celery queue depth > 1000
- Disk usage > 85%
- Memory usage > 90%

---

## 12. Future Enhancements

### Phase 1 Enhancements (Q1 2026)
- [ ] WebSocket support for real-time progress
- [ ] Bulk operations API
- [ ] Advanced filtering & search
- [ ] Dataset versioning
- [ ] File upload & storage (S3/MinIO)

### Phase 2 Enhancements (Q2 2026)
- [ ] GraphQL API alternative
- [ ] Machine learning for auto-categorization
- [ ] Smart duplicate detection (fuzzy matching)
- [ ] Scheduled crawl jobs (cron-like)
- [ ] Webhook notifications

### Phase 3 Enhancements (Q3 2026)
- [ ] Multi-tenancy support
- [ ] Data quality scoring
- [ ] Automated testing of crawl configs
- [ ] Browser extension for adding sites
- [ ] Public dataset marketplace

### Phase 4 Enhancements (Q4 2026)
- [ ] Federated learning for classification
- [ ] Blockchain-based provenance tracking
- [ ] Natural language query interface
- [ ] Automated report generation
- [ ] Mobile app for monitoring

---

## Appendix A: Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `MISSING_API_KEY` | 401 | No API key provided |
| `INVALID_API_KEY` | 401 | Invalid or inactive key |
| `EXPIRED_API_KEY` | 401 | API key has expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Appendix B: Configuration Variables

### Environment Variables
```bash
# Flask
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/crawler
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# OpenAI
OPENAI_API_KEY=sk-...

# External API
EXTERNAL_API_URL=https://api.example.com/v1
EXTERNAL_API_KEY=...

# Security
API_KEY_EXPIRY_DAYS=365
PASSCODE_HASH=sha256-hash

# Crawler
MAX_CONCURRENT_CRAWLS=5
CRAWL_TIMEOUT_SECONDS=3600
```

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-13 | Design Team | Initial design document |

---

**Next Steps:**
1. Review and approve design
2. Set up development environment
3. Implement Phase 1 (Flask Foundation)
4. Begin migration of existing functionality

**Questions or Feedback:**
Contact the development team or open an issue in the repository.
