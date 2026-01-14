# Data Update Strategy

## Problem Statement

Once we've crawled datasets, how do we handle updates?

### Scenarios:
1. **Dataset content changed** (e.g., new population data for 2025)
2. **Dataset metadata changed** (title, description updated)
3. **Dataset removed** from source website
4. **New datasets added** to source website
5. **Dataset URL changed** (moved to different location)

---

## 🎯 Update Strategies

### **Strategy 1: Re-crawl Everything (Full Refresh)**

**How it works:**
- Run crawl job again on same site
- Treat it as completely new crawl
- Use hash-based duplicate detection
- Update existing records if found

**Pros:**
- ✅ Simple to implement
- ✅ Catches all changes (new, updated, deleted)
- ✅ No complex logic needed

**Cons:**
- ❌ Slow (re-crawls entire site)
- ❌ Wastes bandwidth
- ❌ Hard to track what actually changed

**Implementation:**
```python
# Run normal crawl
# For each dataset:
existing = Dataset.query.filter_by(hash=dataset_hash).first()

if existing:
    # Update existing record
    existing.title = new_title
    existing.description = new_description
    existing.updated_at = datetime.utcnow()
else:
    # Create new record
    db.session.add(new_dataset)
```

**Good for:** Small sites, infrequent updates

---

### **Strategy 2: Incremental Update (Smart Crawl)**

**How it works:**
- Track last crawl timestamp per site
- Only process pages modified since last crawl
- Use `Last-Modified` or `ETag` HTTP headers
- Maintain "last_crawled_at" per dataset

**Pros:**
- ✅ Faster (only crawls changed pages)
- ✅ More efficient bandwidth usage
- ✅ Can identify what changed

**Cons:**
- ❌ Not all websites support Last-Modified headers
- ❌ More complex logic
- ❌ Might miss some changes

**Implementation:**
```python
# Check if page was modified
response = requests.head(url)
last_modified = response.headers.get('Last-Modified')

if last_modified:
    last_modified_date = parse_date(last_modified)

    if last_modified_date > dataset.last_crawled_at:
        # Re-crawl this page
        updated_data = extract_data(url)
        update_dataset(dataset, updated_data)
```

**Good for:** Large sites with frequent updates

---

### **Strategy 3: Change Detection (Delta Crawl)**

**How it works:**
- Crawl site but don't save yet
- Compare new data with existing data
- Only update if changes detected
- Track change history

**Pros:**
- ✅ Precise change tracking
- ✅ Can maintain version history
- ✅ Know exactly what changed

**Cons:**
- ❌ Requires full crawl
- ❌ Memory intensive (compare all records)
- ❌ Complex implementation

**Implementation:**
```python
# After crawling
new_datasets = crawl_site()
existing_datasets = Dataset.query.filter_by(source='DATA.UG').all()

for new_ds in new_datasets:
    existing_ds = find_by_hash(new_ds.hash)

    if existing_ds:
        changes = detect_changes(existing_ds, new_ds)

        if changes:
            # Log changes
            log_change_history(existing_ds, changes)

            # Update record
            apply_changes(existing_ds, new_ds)
```

**Good for:** When you need audit trail

---

### **Strategy 4: Scheduled Periodic Crawls**

**How it works:**
- Schedule automatic crawls (daily, weekly, monthly)
- Each crawl updates entire dataset for that source
- Keep track of crawl frequency per source
- Auto-detect stale data

**Pros:**
- ✅ Automated - no manual intervention
- ✅ Data stays fresh
- ✅ Configurable per source

**Cons:**
- ❌ Might crawl unnecessarily
- ❌ Needs scheduler (Celery Beat)

**Implementation:**
```python
# In celeryconfig.py
from celery.schedules import crontab

beat_schedule = {
    'crawl-uganda-portal-daily': {
        'task': 'app.tasks.scheduled_crawl',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': ('uganda-portal',)
    },
    'crawl-us-portal-weekly': {
        'task': 'app.tasks.scheduled_crawl',
        'schedule': crontab(day_of_week=1, hour=3),  # Monday 3 AM
        'args': ('us-portal',)
    }
}
```

**Good for:** Production systems

---

## 🏗️ Recommended Hybrid Approach

Combine multiple strategies based on use case:

### **Phase 1: MVP (Now)**
Use **Strategy 1: Full Refresh**
- Simple re-crawl everything
- Update existing based on hash
- Mark datasets as `updated_at = now()`

```python
def update_crawl(site_id):
    """Re-crawl entire site and update existing datasets"""

    # Run crawl
    datasets = crawl_site(site_id)

    for new_ds in datasets:
        # Check if exists
        existing = Dataset.query.filter_by(
            hash=new_ds.hash
        ).first()

        if existing:
            # Update existing
            existing.title = new_ds.title
            existing.description = new_ds.description
            existing.tags = new_ds.tags
            existing.updated_at = datetime.utcnow()

            logger.info(f"Updated: {existing.title}")
        else:
            # Create new
            db.session.add(new_ds)
            logger.info(f"Created: {new_ds.title}")

    db.session.commit()
```

### **Phase 2: Production Enhancement**
Add **Strategy 4: Scheduled Crawls**
- Auto-crawl weekly/monthly
- Use Celery Beat for scheduling
- Email notifications on completion

### **Phase 3: Advanced Features**
Add **Strategy 3: Change Detection**
- Track what changed (title, description, etc.)
- Maintain change history table
- Show "Updated 2 days ago" badge

---

## 🗄️ Database Schema for Updates

### **Add to Dataset Model:**
```python
class Dataset(db.Model):
    # ... existing fields ...

    # Update tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_crawled_at = db.Column(db.DateTime)  # Last time we checked this dataset
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete if removed from source

    # Version tracking (optional)
    version = db.Column(db.Integer, default=1)
```

### **Add Change History Table (Optional):**
```python
class DatasetChangeHistory(db.Model):
    """Track changes to datasets over time"""

    id = db.Column(UUID, primary_key=True, default=uuid4)
    dataset_id = db.Column(UUID, db.ForeignKey('datasets.id'))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(UUID, db.ForeignKey('users.id'))  # Or 'system' for auto-updates

    # What changed
    field_name = db.Column(db.String(100))  # e.g., 'title', 'description'
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)

    # Optional: Full snapshot
    snapshot = db.Column(db.JSON)  # Full dataset state at this point
```

---

## 🔄 Update Flow Options

### **Option A: Manual Update (User-Triggered)**

```http
POST /api/v1/crawl/update
{
  "site_id": "uganda-portal",
  "update_mode": "full"  // or "incremental"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "...",
    "message": "Update crawl started"
  }
}
```

### **Option B: Automatic Scheduled Update**

```python
# Celery Beat configuration
@celery.task
def scheduled_update_crawl(site_id):
    """Automatically update datasets from a site"""

    # Get site config
    site = SiteConfig.query.filter_by(id=site_id).first()

    # Check if enough time has passed since last crawl
    if site.should_crawl():
        # Start update crawl
        crawl_site_task.delay(site_id, update_mode=True)
```

### **Option C: On-Demand Refresh (Per Dataset)**

```http
POST /api/v1/datasets/{id}/refresh
```

**Use case:** User notices a dataset is outdated, manually triggers refresh

---

## 🚨 Handling Deleted Datasets

### **Problem:**
Dataset exists in our DB but removed from source website

### **Solutions:**

**1. Soft Delete (Recommended)**
```python
# During update crawl
current_hashes = set(new_dataset.hash for new_dataset in crawled_datasets)
existing_datasets = Dataset.query.filter_by(source='DATA.UG').all()

for existing in existing_datasets:
    if existing.hash not in current_hashes:
        # Dataset no longer exists on source
        existing.is_deleted = True
        existing.deleted_at = datetime.utcnow()
        logger.warning(f"Dataset deleted from source: {existing.title}")
```

**2. Mark as Stale**
```python
existing.is_active = False
existing.stale_reason = "Not found on source website"
```

**3. Hard Delete (Not Recommended)**
- Permanently remove from database
- Lose historical data
- Can't track what was deleted

---

## 📊 Update Metrics to Track

```python
class UpdateCrawlStats:
    """Statistics from an update crawl"""

    total_found = 0           # Total datasets on source
    total_existing = 0        # Already in our DB
    total_new = 0             # New datasets added
    total_updated = 0         # Existing datasets updated
    total_unchanged = 0       # No changes detected
    total_deleted = 0         # Removed from source

    changes_detected = {
        'title': 5,
        'description': 12,
        'tags': 8
    }
```

---

## 🎯 API Endpoints for Updates

### **1. Trigger Update Crawl**
```http
POST /api/v1/crawl/update
{
  "site_id": "uganda-portal",
  "mode": "full",  // or "incremental"
  "notify_on_completion": true
}
```

### **2. Get Update Status**
```http
GET /api/v1/crawl/jobs/{job_id}/updates

Response:
{
  "stats": {
    "new": 15,
    "updated": 42,
    "deleted": 3,
    "unchanged": 160
  },
  "changes": [
    {
      "dataset_id": "...",
      "title": "Rwanda Population 2024",
      "changed_fields": ["description", "tags"],
      "changed_at": "2026-01-13T12:00:00Z"
    }
  ]
}
```

### **3. Refresh Single Dataset**
```http
POST /api/v1/datasets/{id}/refresh

Response:
{
  "success": true,
  "changes": {
    "description": {
      "old": "Old description",
      "new": "Updated description"
    }
  },
  "updated_at": "2026-01-13T12:05:00Z"
}
```

---

## 💡 Recommended Implementation Plan

### **MVP (Phase 1):**
1. ✅ Implement Strategy 1 (Full Refresh)
2. ✅ Add `updated_at` field to Dataset model
3. ✅ Manual update via API endpoint
4. ✅ Track update stats (new/updated counts)

### **Production (Phase 2):**
1. ⏳ Add Celery Beat for scheduled crawls
2. ⏳ Implement soft delete for removed datasets
3. ⏳ Email notifications on update completion
4. ⏳ Dashboard showing update history

### **Advanced (Phase 3):**
1. ⏳ Change detection with history table
2. ⏳ Incremental crawls using Last-Modified
3. ⏳ Per-dataset refresh capability
4. ⏳ Change diff visualization in UI

---

## 🔍 Key Questions to Decide

1. **Update Frequency:**
   - How often should we update each source? (Daily, Weekly, Monthly)
   - Should it be configurable per source?

2. **Update Mode:**
   - Always full refresh?
   - Or support incremental mode?

3. **Deleted Datasets:**
   - Soft delete (keep in DB, mark as deleted)?
   - Hard delete (remove completely)?
   - Keep for X days then delete?

4. **Change Tracking:**
   - Do we need full change history?
   - Or just "last updated" timestamp?

5. **Notifications:**
   - Email on update completion?
   - Webhook to external system?
   - In-app notifications?

---

## 📝 Summary

**For MVP, I recommend:**
- ✅ Manual update crawls (re-crawl everything)
- ✅ Update existing datasets based on hash matching
- ✅ Soft delete for removed datasets
- ✅ Track `updated_at` timestamp
- ✅ Provide update stats in API response

**This gives us:**
- Simple to implement
- Works reliably
- Can be enhanced later
- Covers all update scenarios

**Does this approach work for you? Any preferences on the questions above?**
