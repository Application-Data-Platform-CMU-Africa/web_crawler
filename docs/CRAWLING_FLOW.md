# Complete Crawling Flow - End to End

## Overview

This document defines the complete flow from when a user initiates a crawl request until the data is saved in the database.

---

## 🔄 High-Level Flow

```
User Request → API Validation → Celery Task Queue → Crawler Execution → Data Extraction →
Data Processing → Duplicate Check → Database Save → Job Complete
```

---

## 📋 Detailed Step-by-Step Flow

### **Phase 1: Crawl Initiation (API Layer)**

#### Step 1.1: User Makes API Request
```http
POST /api/v1/crawl/start
Headers:
  X-API-Key: sk_live_abc123...
  Content-Type: application/json

Body:
{
  "site_id": "uganda-portal",           // Which site config to use
  "options": {
    "test_mode": false,                 // Test mode = no DB writes
    "max_pages": 100,                   // Optional limit
    "country_filter": "Rwanda"          // Optional country filter
  }
}
```

#### Step 1.2: API Validates Request
**What happens:**
1. Check API key is valid (not expired, is active)
2. Validate request body (site_id exists, options are valid)
3. Check if site configuration exists in `configs/config.json`
4. Check max concurrent crawls limit (e.g., max 5 jobs running)

**If validation fails:**
- Return 400/401 error immediately
- No job created

**If validation passes:**
- Continue to Step 1.3

#### Step 1.3: Create CrawlJob Record
**Database Insert:**
```sql
INSERT INTO crawl_jobs (
  id,
  job_id,              -- Will be Celery task ID
  site_name,           -- e.g., "Uganda Data Portal"
  start_url,           -- e.g., "http://catalog.data.ug/dataset"
  status,              -- 'pending'
  progress,            -- 0
  config,              -- JSON of full config + options
  created_by,          -- User ID from API key
  created_at
) VALUES (...)
```

**Response to User:**
```json
HTTP 202 Accepted
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Crawl job queued successfully"
  }
}
```

#### Step 1.4: Dispatch to Celery
```python
# In API endpoint
from app.tasks.crawl_tasks import crawl_site_task

task = crawl_site_task.apply_async(
    args=[job_id, site_config, options],
    queue='crawl'
)

# Update job with celery task ID
crawl_job.task_id = task.id
db.session.commit()
```

**User gets response immediately** - crawling happens in background

---

### **Phase 2: Background Crawling (Celery Worker)**

#### Step 2.1: Celery Worker Picks Up Task
**Worker receives:**
- `job_id` (CrawlJob UUID)
- `site_config` (from configs/config.json)
- `options` (user-provided options)

#### Step 2.2: Initialize Crawler
**What happens:**
1. Update job status: `pending` → `running`
2. Set `started_at` timestamp
3. Load site configuration
4. Determine crawler type (static vs dynamic)
5. Initialize Scrapy spider OR Selenium browser

**Code example:**
```python
@celery.task(bind=True)
def crawl_site_task(self, job_id, site_config, options):
    # Update job status
    job = CrawlJob.query.get(job_id)
    job.status = 'running'
    job.started_at = datetime.utcnow()
    db.session.commit()

    # Initialize crawler
    if site_config['is_dynamic']:
        crawler = DynamicCrawler(site_config, job_id, options)
    else:
        crawler = StaticCrawler(site_config, job_id, options)

    # Start crawling
    crawler.crawl()
```

#### Step 2.3: Web Crawling Loop
**For each page discovered:**

```
1. Fetch Page
   ├─ Respect robots.txt
   ├─ Apply download delay (2 seconds)
   ├─ Set user agent
   └─ Handle errors (retry 3x)

2. Extract Links
   ├─ Apply URL rules from config
   │   ├─ Pagination links (follow, don't extract)
   │   └─ Dataset links (follow AND extract)
   └─ Add to queue

3. Extract Data (if dataset page)
   ├─ Title (CSS selector from config)
   ├─ Description (CSS selector from config)
   ├─ Tags (CSS selector from config)
   ├─ Extension (detect from URL or content-type)
   └─ Source URL

4. Update Progress
   ├─ Increment pages_crawled counter
   ├─ Update job.progress = (crawled / estimated) * 100
   └─ Emit progress event (for real-time tracking)

5. Repeat until:
   ├─ No more links in queue
   ├─ Max pages reached
   └─ Timeout reached
```

---

### **Phase 3: Data Processing (Per Dataset)**

#### Step 3.1: Raw Data Extracted
```python
raw_data = {
    "title": "Rwanda Population Statistics 2024",
    "description": "Comprehensive population data...",
    "url": "http://catalog.data.ug/dataset/rwanda-pop-2024",
    "tags": ["population", "demographics", "rwanda"],
    "source": "DATA.UG"
}
```

#### Step 3.2: Data Transformation & Enrichment
**Apply transformations:**

```python
def process_dataset(raw_data, site_config, options):
    # 1. Clean & validate
    title = clean_text(raw_data['title'])
    description = clean_text(raw_data['description'])

    # 2. Extract extension from URL
    extension = extract_extension(raw_data['url'])
    # e.g., "http://example.com/data.csv" → "csv"

    # 3. Detect file size (if possible)
    file_size = get_file_size(raw_data['url'])  # HTTP HEAD request

    # 4. Build standardized dataset object
    dataset = {
        "title": title,
        "description": description,
        "extension": extension,
        "original_file_name": title,  # Use title as filename
        "file_references": [raw_data['url']],  # Array of URLs
        "file_size_mb": file_size,
        "source": site_config['source_name'],
        "tags": raw_data.get('tags', []),
        "is_link": True,  # We're storing external links
        "is_private": False,
        "is_active": True,
        "crawl_job_id": job_id,
        "owner_id": get_system_user_id()  # Default system user
    }

    return dataset
```

#### Step 3.3: Generate Hash for Duplicate Detection
```python
def generate_hash(dataset):
    # Create hash from URL + title to detect duplicates
    hash_input = f"{dataset['file_references'][0]}{dataset['title']}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

dataset['hash'] = generate_hash(dataset)
```

---

### **Phase 4: Database Operations**

#### Step 4.1: Check for Duplicates
```python
existing = Dataset.query.filter_by(
    hash=dataset['hash']
).first()

if existing:
    logger.info(f"Duplicate found: {dataset['title']}")
    job.total_found += 1
    return  # Skip this dataset
```

#### Step 4.2: Save to Database
**If not duplicate:**

```python
# Create dataset record
new_dataset = Dataset(
    title=dataset['title'],
    description=dataset['description'],
    extension=dataset['extension'],
    original_file_name=dataset['original_file_name'],
    file_references=dataset['file_references'],
    file_size_mb=dataset['file_size_mb'],
    source=dataset['source'],
    tags=dataset['tags'],
    is_link=dataset['is_link'],
    is_private=dataset['is_private'],
    is_active=dataset['is_active'],
    crawl_job_id=dataset['crawl_job_id'],
    owner_id=dataset['owner_id'],
    hash=dataset['hash']
)

# Commit to database
db.session.add(new_dataset)
db.session.commit()

# Update job counters
job.total_found += 1
job.total_saved += 1
db.session.commit()

logger.info(f"Saved dataset: {dataset['title']}")
```

#### Step 4.3: Also Save to JSON (Optional - for testing/backup)
```python
if options.get('save_json', True):
    with open(f'data/{job_id}.json', 'a') as f:
        json.dump(dataset, f)
        f.write(',\n')
```

---

### **Phase 5: Progress Tracking**

#### Throughout Crawling:
```python
# Update every N pages (e.g., every 10 pages)
if pages_crawled % 10 == 0:
    job.progress = calculate_progress(pages_crawled, estimated_total)
    db.session.commit()

    # Update Celery task state (for real-time monitoring)
    self.update_state(
        state='PROGRESS',
        meta={
            'progress': job.progress,
            'pages_crawled': pages_crawled,
            'datasets_found': job.total_found,
            'datasets_saved': job.total_saved
        }
    )
```

#### User can check progress:
```http
GET /api/v1/crawl/jobs/{job_id}

Response:
{
  "job_id": "550e8400...",
  "status": "running",
  "progress": 45,
  "total_found": 120,
  "total_saved": 98,
  "started_at": "2026-01-13T10:00:00Z"
}
```

---

### **Phase 6: Crawl Completion**

#### Step 6.1: Crawler Finishes
**Normal completion:**
```python
# Update job status
job.status = 'completed'
job.completed_at = datetime.utcnow()
job.progress = 100
db.session.commit()

logger.info(f"Crawl job {job_id} completed. Found: {job.total_found}, Saved: {job.total_saved}")
```

**Error during crawling:**
```python
except Exception as e:
    job.status = 'failed'
    job.error_message = str(e)
    job.completed_at = datetime.utcnow()
    db.session.commit()

    logger.error(f"Crawl job {job_id} failed: {e}")
    raise
```

#### Step 6.2: Cleanup
```python
# Close connections
crawler.close()

# Optional: Send notification (email, webhook, etc.)
notify_job_complete(job_id, user_email)
```

---

## 🎯 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INITIATES CRAWL                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   API Validation     │
                  │  - API Key Check     │
                  │  - Config Check      │
                  │  - Concurrency Check │
                  └──────────┬───────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
              [INVALID]           [VALID]
                   │                   │
                   ▼                   ▼
            ┌──────────┐      ┌────────────────┐
            │Return 400│      │Create CrawlJob │
            └──────────┘      │ status=pending │
                              └────────┬───────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │ Queue Celery   │
                              │ Task (async)   │
                              └────────┬───────┘
                                       │
                              ┌────────┴───────┐
                              │                │
                        [API RETURNS]    [WORKER STARTS]
                              │                │
                              ▼                ▼
                     ┌──────────────┐  ┌──────────────────┐
                     │ 202 Accepted │  │ Update job to    │
                     │ job_id: xxx  │  │ status='running' │
                     └──────────────┘  └────────┬─────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Initialize      │
                                        │ Crawler         │
                                        │ (Static/Dynamic)│
                                        └────────┬────────┘
                                                 │
                                                 ▼
                    ┌────────────────────────────────────────────┐
                    │          CRAWLING LOOP                     │
                    │  ┌──────────────────────────────────┐      │
                    │  │ For each page:                   │      │
                    │  │  1. Fetch page                   │      │
                    │  │  2. Extract links                │      │
                    │  │  3. Extract data                 │      │
                    │  │  4. Process data                 │      │
                    │  │  5. Check duplicates             │      │
                    │  │  6. Save to DB (if not duplicate)│      │
                    │  │  7. Update progress              │      │
                    │  │  8. Repeat                       │      │
                    │  └──────────────────────────────────┘      │
                    └────────────────────┬───────────────────────┘
                                         │
                            ┌────────────┴────────────┐
                            │                         │
                      [SUCCESS]                  [ERROR]
                            │                         │
                            ▼                         ▼
                   ┌─────────────────┐      ┌──────────────────┐
                   │ Update job:     │      │ Update job:      │
                   │ status=completed│      │ status=failed    │
                   │ progress=100    │      │ error_message=...│
                   └─────────────────┘      └──────────────────┘
```

---

## 📊 Data Flow Example

### Input (from website):
```html
<h1>Rwanda Population Statistics 2024</h1>
<p>Comprehensive population data for Rwanda...</p>
<a href="data.csv">Download CSV</a>
<span class="tag">population</span>
<span class="tag">demographics</span>
```

### Extracted:
```python
{
  "title": "Rwanda Population Statistics 2024",
  "description": "Comprehensive population data for Rwanda...",
  "url": "http://catalog.data.ug/dataset/rwanda-pop-2024",
  "tags": ["population", "demographics"]
}
```

### Processed & Enriched:
```python
{
  "title": "Rwanda Population Statistics 2024",
  "description": "Comprehensive population data for Rwanda...",
  "extension": "csv",
  "original_file_name": "Rwanda Population Statistics 2024",
  "file_references": ["http://catalog.data.ug/dataset/rwanda-pop-2024/data.csv"],
  "file_size_mb": 2.5,
  "source": "DATA.UG",
  "tags": ["population", "demographics"],
  "is_link": true,
  "is_private": false,
  "is_active": true,
  "hash": "a3f4b2c1d5e6...",
  "crawl_job_id": "550e8400...",
  "owner_id": "system-user-id"
}
```

### Saved to Database:
```sql
INSERT INTO datasets (
  title, description, extension, file_references,
  source, tags, is_link, crawl_job_id, ...
) VALUES (...);
```

---

## 🔍 Key Decision Points

### **Question 1: Where do we extract file extension?**
**Options:**
- A) From URL path (e.g., `.csv` in `data.csv`)
- B) From HTTP Content-Type header
- C) From download link text
- **Recommendation:** Try A, fallback to B if not found

### **Question 2: Do we download files or just store links?**
**For MVP:**
- ✅ Store links only (`is_link = true`)
- ✅ Save `file_references` as array of URLs
- ⏳ Later: Add file download feature

### **Question 3: When do we classify by SDG?**
**Options:**
- A) During crawling (slows down crawl)
- B) After crawling (separate job)
- **Recommendation:** Option B - separate classification step

### **Question 4: How do we detect duplicates?**
**Hash calculation:**
```python
hash = SHA256(url + title)
```
This catches:
- Exact same URL
- Same dataset crawled multiple times
- Same dataset on different pages (if title matches)

### **Question 5: Do we save to JSON file?**
**Recommendation:**
- ✅ Yes, for testing/debugging
- ✅ Saved to `data/{job_id}.json`
- ❌ Not for production (DB only)

---

## 📝 Open Questions / To Decide

1. **Categories & SDGs** - Do we assign during crawl or later?
   - My recommendation: Later, via separate classification task

2. **Countries** - How do we associate datasets with countries?
   - From URL country filter?
   - From dataset content (requires AI)?
   - Manual tagging?

3. **File Size** - Do we make HTTP HEAD request for every link?
   - Pro: Accurate file size
   - Con: Slower crawling (extra request per dataset)
   - Recommendation: Optional, skip for MVP

4. **Progress Calculation** - How to estimate total pages?
   - Start with unknown total
   - Update as we discover more links
   - Show "X datasets found" instead of percentage?

5. **Error Handling** - What if single page fails?
   - Continue crawling other pages?
   - Retry failed pages?
   - Recommendation: Log error, continue

---

## ✅ What We Need to Build

Based on this flow:

1. **Database Models** (complete them)
   - ✅ User
   - ✅ APIKey
   - ⏳ Dataset (with all new fields)
   - ⏳ CrawlJob (with progress tracking)
   - ⏳ Category, SDG, Country (for relationships)

2. **API Endpoints**
   - ⏳ POST /crawl/start (initiate crawl)
   - ⏳ GET /crawl/jobs/{id} (check progress)
   - ⏳ GET /datasets (list results)

3. **Celery Tasks**
   - ⏳ crawl_site_task (main crawler)

4. **Crawler Service**
   - ⏳ StaticCrawler (Scrapy-based)
   - ⏳ DynamicCrawler (Selenium-based, later)

5. **Data Processors**
   - ⏳ Data extraction
   - ⏳ Data transformation
   - ⏳ Duplicate detection
   - ⏳ Hash generation

---

**Does this flow make sense? Any changes or clarifications needed?**
