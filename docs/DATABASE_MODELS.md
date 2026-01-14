# Database Models Documentation

Complete documentation of all database models and relationships.

## Overview

The database schema consists of **7 core tables** and **2 association tables** for many-to-many relationships.

## Core Models

### 1. Dataset Model (`datasets`)

**Purpose:** Stores crawled datasets with two-hash strategy for duplicate detection and update tracking.

**Key Features:**
- ✅ Two-hash strategy (URL-based + content-based)
- ✅ Comprehensive metadata storage
- ✅ Geographic and temporal coverage
- ✅ Publisher information
- ✅ Quality scoring
- ✅ Soft delete support (status field)

**Schema:**

```python
class Dataset(db.Model):
    # Primary Key
    id = Integer (Primary Key)

    # Two-Hash Strategy
    hash = String(64)           # SHA256 of URL - primary identifier (UNIQUE)
    content_hash = String(64)   # SHA256 of title+description+tags - change detection

    # Core Metadata
    title = Text (NOT NULL, indexed)
    description = Text
    url = Text (NOT NULL)
    source = String(255)        # e.g., "Uganda Data Portal"
    source_id = String(255)     # Original ID from source

    # Classification
    tags = JSONB                # ["health", "population", ...]
    file_types = JSONB          # ["CSV", "JSON", "PDF", ...]

    # Geographic & Temporal
    country_code = String(3)    # ISO 3166-1 alpha-3
    temporal_coverage_start = Date
    temporal_coverage_end = Date

    # Publisher
    publisher = String(255)
    publisher_email = String(255)
    license = String(255)

    # Resources
    resources = JSONB           # [{url, format, size, ...}, ...]
    download_count = Integer

    # Status & Quality
    status = String(50)         # active, archived, deleted
    is_published = Boolean
    quality_score = Float       # 0-100

    # Timestamps
    created_at = DateTime
    updated_at = DateTime
    last_crawled_at = DateTime  # When we last checked this URL
    published_date = DateTime   # When published on source portal

    # Relationships
    crawl_job_id = Integer (FK -> crawl_jobs.id)
```

**Two-Hash Strategy:**

```python
# Primary Hash (URL-based) - Prevents duplicates
hash = SHA256(url.lower().strip())

# Content Hash (metadata-based) - Detects updates
content_hash = SHA256(f"{title}|{description}|{sorted_tags}".lower())
```

**Key Methods:**

```python
# Finding datasets
Dataset.find_by_hash(hash_value)           # Find by primary hash
Dataset.find_by_url(url)                   # Find by URL

# Change detection
dataset.has_content_changed(new_hash)      # Check if content changed

# Updates
dataset.update_metadata(**kwargs)          # Update metadata
dataset.mark_as_crawled()                  # Update last_crawled_at
```

---

### 2. CrawlJob Model (`crawl_jobs`)

**Purpose:** Tracks crawl job execution, progress, and statistics.

**Schema:**

```python
class CrawlJob(db.Model):
    # Primary Key
    id = Integer (Primary Key)

    # Job Identification
    job_id = String(255) (UNIQUE, indexed)          # UUID or custom ID
    celery_task_id = String(255) (UNIQUE, indexed)  # Celery task reference

    # Configuration
    site_id = String(255) (indexed)      # e.g., "uganda-portal"
    start_url = Text                     # Starting URL
    crawler_type = String(50)            # static, dynamic, api
    options = JSONB                      # {max_pages: 100, test_mode: false}

    # Status & Progress
    status = String(50) (indexed)        # pending, running, completed, failed, cancelled
    progress_percentage = Float          # 0-100
    current_page = String(500)           # Currently processing URL

    # Statistics
    stats = JSONB                        # Full statistics object
    pages_crawled = Integer
    datasets_found = Integer
    datasets_created = Integer           # New datasets
    datasets_updated = Integer           # Updated datasets
    datasets_unchanged = Integer         # No changes
    duplicates_skipped = Integer
    errors_count = Integer

    # Error Tracking
    error_message = Text
    error_details = JSONB

    # Timestamps
    created_at = DateTime
    started_at = DateTime
    completed_at = DateTime
    updated_at = DateTime

    # User Tracking
    created_by = Integer (FK -> users.id)
```

**Key Methods:**

```python
# Lifecycle management
job.start()                              # Mark as started
job.complete(stats)                      # Mark as completed
job.fail(error_message, error_details)   # Mark as failed
job.cancel()                             # Mark as cancelled

# Progress tracking
job.update_progress(percentage, current_page)
job.update_stats(stats_dict)

# Finding jobs
CrawlJob.find_by_job_id(job_id)
CrawlJob.find_by_celery_task_id(task_id)
CrawlJob.get_recent_jobs(limit=10)
CrawlJob.get_running_jobs()
```

---

### 3. Category Model (`categories`)

**Purpose:** Hierarchical dataset categorization.

**Schema:**

```python
class Category(db.Model):
    id = Integer (Primary Key)
    name = String(255) (UNIQUE, indexed)
    slug = String(255) (UNIQUE, indexed)  # URL-friendly
    description = Text
    icon = String(100)                    # Icon name or emoji
    color = String(7)                     # Hex color (#FF5733)

    # Hierarchy
    parent_id = Integer (FK -> categories.id)  # Self-referencing

    # Display
    is_active = Boolean
    display_order = Integer

    # Timestamps
    created_at = DateTime
    updated_at = DateTime
```

**Example Hierarchy:**

```
Health (parent_id: NULL)
├── Public Health (parent_id: 1)
├── Medical Research (parent_id: 1)
└── Healthcare Infrastructure (parent_id: 1)

Education (parent_id: NULL)
├── Primary Education (parent_id: 2)
└── Higher Education (parent_id: 2)
```

---

### 4. SDG Model (`sdgs`)

**Purpose:** UN Sustainable Development Goals for AI classification.

**Schema:**

```python
class SDG(db.Model):
    id = Integer (Primary Key)
    number = Integer (UNIQUE, 1-17)
    name = String(255)                # "No Poverty"
    description = Text                # Full SDG description
    icon_url = String(500)            # URL to official SDG icon
    color = String(7)                 # Official SDG color
    keywords = Text                   # Comma-separated for AI matching
    is_active = Boolean
    created_at = DateTime
    updated_at = DateTime
```

**Example Data:**

```python
SDG 1: No Poverty
  keywords: "poverty, income, economic, poor, wealth inequality"
  color: "#E5243B"

SDG 3: Good Health and Well-being
  keywords: "health, medical, disease, healthcare, mortality, life expectancy"
  color: "#4C9F38"
```

---

### 5. Country Model (`countries`)

**Purpose:** Geographic filtering with ISO codes.

**Schema:**

```python
class Country(db.Model):
    id = Integer (Primary Key)
    name = String(255)
    code = String(3) (UNIQUE, indexed)        # ISO 3166-1 alpha-3 (UGA)
    code_alpha2 = String(2) (UNIQUE)          # ISO 3166-1 alpha-2 (UG)
    region = String(100) (indexed)            # "East Africa"
    continent = String(50) (indexed)          # "Africa"
    flag_emoji = String(10)                   # 🇺🇬
    has_data_portal = Boolean
    portal_url = String(500)
    is_active = Boolean
    created_at = DateTime
    updated_at = DateTime
```

---

### 6. User Model (`users`)

**Purpose:** System users for authentication and ownership.

**Schema:**

```python
class User(db.Model):
    id = String(36) (Primary Key, UUID)
    email = String(255) (UNIQUE, indexed)
    name = String(255)
    is_admin = Boolean
    is_active = Boolean
    created_at = DateTime
    updated_at = DateTime
```

---

### 7. APIKey Model (`api_keys`)

**Purpose:** API key authentication.

**Schema:**

```python
class APIKey(db.Model):
    id = Integer (Primary Key)
    key_hash = String(64) (UNIQUE, indexed)   # SHA256 of actual key
    key_prefix = String(10)                   # First 10 chars for display
    name = String(255)                        # User-friendly name
    user_id = String(36) (FK -> users.id)
    is_active = Boolean
    last_used_at = DateTime
    created_at = DateTime
    expires_at = DateTime
```

---

## Association Tables (Many-to-Many)

### 1. dataset_categories

**Purpose:** Link datasets to multiple categories.

```python
dataset_categories:
    dataset_id (PK, FK -> datasets.id)
    category_id (PK, FK -> categories.id)
    created_at (DateTime)
```

**Example:**

```
Dataset "Uganda Population 2024" can belong to:
  - Demographics
  - Health
  - Public Health
```

---

### 2. dataset_sdgs

**Purpose:** Link datasets to multiple SDGs with confidence scores.

```python
dataset_sdgs:
    dataset_id (PK, FK -> datasets.id)
    sdg_id (PK, FK -> sdgs.id)
    confidence_score (Float, 0-1)     # AI classification confidence
    created_at (DateTime)
```

**Example:**

```
Dataset "Maternal Health Services" linked to:
  - SDG 3 (Good Health) - confidence: 0.95
  - SDG 5 (Gender Equality) - confidence: 0.78
  - SDG 10 (Reduced Inequalities) - confidence: 0.62
```

---

## Relationships Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ 1:N
       ├──────────┐
       │          │
       ▼          ▼
┌─────────┐  ┌──────────┐
│ APIKey  │  │CrawlJob  │
└─────────┘  └────┬─────┘
                  │ 1:N
                  ▼
             ┌──────────┐
             │ Dataset  │◄──────────┐
             └────┬─────┘           │
                  │ M:N              │ M:N
         ┌────────┼────────┐        │
         │        │        │        │
         ▼        ▼        ▼        │
    ┌────────┐ ┌────┐  ┌────────┐  │
    │Category│ │SDG │  │Country │  │
    └────────┘ └────┘  └────────┘  │
         │        │                 │
         └────────┴─────────────────┘
```

---

## Update Strategy with Two-Hash System

### Scenario 1: Same URL, Changed Title (UPDATE)

```python
# First crawl
url = "http://portal.ug/dataset/population"
title = "Population 2023"
hash = SHA256(url) = "aaa111..."
content_hash = SHA256("population 2023|...") = "bbb222..."

# Second crawl (1 year later)
url = "http://portal.ug/dataset/population"  # SAME
title = "Population 2024"  # CHANGED
hash = SHA256(url) = "aaa111..."  # SAME HASH
content_hash = SHA256("population 2024|...") = "ccc333..."  # DIFFERENT

# Logic:
existing = Dataset.find_by_hash("aaa111...")  # FOUND!
if existing.has_content_changed("ccc333..."):  # TRUE
    existing.update_metadata(title="Population 2024", content_hash="ccc333...")
    # Result: UPDATED existing record
```

### Scenario 2: Different URL, Same Title (NEW)

```python
# Original
url1 = "http://portal.ug/dataset/old-location"
hash1 = SHA256(url1) = "aaa111..."

# New location
url2 = "http://portal.ug/dataset/new-location"  # DIFFERENT URL
hash2 = SHA256(url2) = "ddd444..."  # DIFFERENT HASH

# Logic:
existing = Dataset.find_by_hash("ddd444...")  # NOT FOUND
# Result: CREATE new record
```

### Scenario 3: Same URL, Same Metadata (NO CHANGE)

```python
url = "http://portal.ug/dataset/population"
hash = "aaa111..."  # SAME
content_hash = "bbb222..."  # SAME

# Logic:
existing = Dataset.find_by_hash("aaa111...")  # FOUND
if not existing.has_content_changed("bbb222..."):  # FALSE
    existing.mark_as_crawled()  # Just update last_crawled_at
    # Result: UNCHANGED
```

---

## Database Indexes

**Performance Optimizations:**

```sql
-- Datasets
CREATE INDEX idx_datasets_hash ON datasets(hash);                    -- Primary lookup
CREATE INDEX idx_datasets_content_hash ON datasets(content_hash);    -- Change detection
CREATE INDEX idx_datasets_title ON datasets(title);                  -- Search
CREATE INDEX idx_datasets_source ON datasets(source);                -- Filter by source
CREATE INDEX idx_datasets_status ON datasets(status);                -- Filter active/archived
CREATE INDEX idx_datasets_country_code ON datasets(country_code);    -- Geographic filter
CREATE INDEX idx_datasets_is_published ON datasets(is_published);    -- Public datasets

-- Crawl Jobs
CREATE INDEX idx_crawl_jobs_job_id ON crawl_jobs(job_id);
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);            -- Find running jobs
CREATE INDEX idx_crawl_jobs_site_id ON crawl_jobs(site_id);          -- Filter by site

-- Categories & SDGs
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_sdgs_number ON sdgs(number);

-- Countries
CREATE INDEX idx_countries_code ON countries(code);
CREATE INDEX idx_countries_region ON countries(region);
CREATE INDEX idx_countries_continent ON countries(continent);
```

---

## Migration Commands

### Initialize Database (First Time)

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial schema with two-hash strategy"

# Apply migration
flask db upgrade
```

### Applying Existing Migration

```bash
# Apply all pending migrations
flask db upgrade

# Check current migration version
flask db current

# View migration history
flask db history
```

### Rollback Migration

```bash
# Rollback one migration
flask db downgrade

# Rollback to specific version
flask db downgrade <revision_id>
```

---

## Sample Data Seeding

Create a seed script to populate initial data:

```python
# scripts/seed_data.py

from app import create_app, db
from app.models import Country, SDG, Category

app = create_app()

with app.app_context():
    # Seed Countries
    countries = [
        Country(name="Uganda", code="UGA", code_alpha2="UG",
                region="East Africa", continent="Africa",
                has_data_portal=True,
                portal_url="http://catalog.data.ug"),
        Country(name="Kenya", code="KEN", code_alpha2="KE",
                region="East Africa", continent="Africa",
                has_data_portal=True,
                portal_url="http://opendata.go.ke"),
        # ... more countries
    ]

    # Seed SDGs
    sdgs = [
        SDG(number=1, name="No Poverty",
            keywords="poverty,income,economic,poor,inequality",
            color="#E5243B"),
        SDG(number=3, name="Good Health and Well-being",
            keywords="health,medical,disease,healthcare,mortality",
            color="#4C9F38"),
        # ... all 17 SDGs
    ]

    # Seed Categories
    categories = [
        Category(name="Health", slug="health", display_order=1),
        Category(name="Education", slug="education", display_order=2),
        Category(name="Agriculture", slug="agriculture", display_order=3),
        # ... more categories
    ]

    db.session.bulk_save_objects(countries)
    db.session.bulk_save_objects(sdgs)
    db.session.bulk_save_objects(categories)
    db.session.commit()

    print("✅ Database seeded successfully!")
```

Run with:
```bash
python scripts/seed_data.py
```

---

## Summary

**Database Models Implemented:**

✅ **Dataset** - Two-hash strategy for duplicates and updates
✅ **CrawlJob** - Crawl execution tracking
✅ **Category** - Hierarchical categorization
✅ **SDG** - UN Sustainable Development Goals
✅ **Country** - Geographic filtering
✅ **User** - Authentication and ownership
✅ **APIKey** - API authentication
✅ **Associations** - Many-to-many relationships

**Key Features:**

- 🎯 Two-hash strategy prevents duplicates while detecting updates
- 📊 Comprehensive statistics tracking
- 🌍 Geographic and temporal coverage
- 🎨 Hierarchical categories
- 🎯 AI-ready SDG classification
- 🔐 Secure API key authentication
- 📈 Quality scoring system
- 🗄️ Optimized indexes for performance

**Next Steps:**

1. Run database migrations
2. Seed initial data (countries, SDGs, categories)
3. Implement Celery tasks for crawling
4. Build API endpoints
5. Test with real data portal
