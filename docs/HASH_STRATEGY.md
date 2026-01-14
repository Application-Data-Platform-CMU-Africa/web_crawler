# Hash Strategy - Duplicate Detection & Update Tracking

## Problem

We need to handle two different scenarios:

1. **Duplicate Detection** - Same dataset crawled multiple times
2. **Update Detection** - Same dataset with changed metadata (title, description, tags)

A single hash can't solve both problems effectively.

---

## Solution: Two-Hash Strategy

We use **two different hashes** for different purposes:

### **1. Primary Hash (`hash`)** - URL-based
**Purpose:** Unique identifier for the dataset
**Based on:** URL only
**Used for:** Finding and preventing duplicates

```python
hash = SHA256(url.lower().strip())
```

**Example:**
```python
url = "http://catalog.data.ug/dataset/population-2024"
hash = "a3f4b2c1d5e6f7a8..."  # Always same for this URL
```

### **2. Content Hash (`content_hash`)** - Metadata-based
**Purpose:** Detect when content/metadata has changed
**Based on:** Title + Description + Tags
**Used for:** Determining if update is needed

```python
content_hash = SHA256(f"{title}|{description}|{sorted_tags}".lower())
```

**Example:**
```python
title = "Rwanda Population 2024"
description = "Updated population data"
tags = ["population", "rwanda"]
content_hash = "b4c5d6e7f8a9..."  # Changes when metadata changes
```

---

## How It Works

### **Scenario 1: Same URL, Changed Title (Update)**

```python
# First Crawl
url = "http://catalog.data.ug/dataset/population"
title = "Rwanda Population 2023"
hash = SHA256(url) = "aaa111..."
content_hash = SHA256("rwanda population 2023|...") = "bbb222..."

# Database:
Dataset(hash="aaa111...", content_hash="bbb222...", title="Rwanda Population 2023")
```

```python
# Second Crawl (1 year later)
url = "http://catalog.data.ug/dataset/population"  # SAME URL
title = "Rwanda Population 2024"  # CHANGED TITLE
hash = SHA256(url) = "aaa111..."  # SAME HASH
content_hash = SHA256("rwanda population 2024|...") = "ccc333..."  # DIFFERENT HASH

# Logic:
existing = Dataset.query.filter_by(hash="aaa111...").first()  # FOUND!

if existing.content_hash != "ccc333...":  # Content changed!
    # UPDATE existing record
    existing.title = "Rwanda Population 2024"
    existing.content_hash = "ccc333..."
    existing.updated_at = now()
    logger.info("✅ Updated: Rwanda Population 2024")
```

**Result:** ✅ Dataset updated, no duplicate created

---

### **Scenario 2: Different URL, Same Title (New Dataset)**

```python
# Original Dataset
url1 = "http://catalog.data.ug/dataset/population-old"
title = "Rwanda Population 2024"
hash1 = SHA256(url1) = "aaa111..."

# Dataset Moved to New URL
url2 = "http://catalog.data.ug/dataset/population-new"  # DIFFERENT URL
title = "Rwanda Population 2024"  # SAME TITLE
hash2 = SHA256(url2) = "ddd444..."  # DIFFERENT HASH

# Logic:
existing = Dataset.query.filter_by(hash="ddd444...").first()  # NOT FOUND

# CREATE new record
new_dataset = Dataset(hash="ddd444...", title="Rwanda Population 2024")
logger.info("✅ Created: Rwanda Population 2024 (new location)")
```

**Result:** ✅ New dataset created (it's at a different URL)

---

### **Scenario 3: Same URL, Same Metadata (No Change)**

```python
# First Crawl
url = "http://catalog.data.ug/dataset/population"
title = "Rwanda Population 2024"
hash = "aaa111..."
content_hash = "bbb222..."

# Second Crawl (same day)
url = "http://catalog.data.ug/dataset/population"  # SAME
title = "Rwanda Population 2024"  # SAME
hash = "aaa111..."  # SAME
content_hash = "bbb222..."  # SAME

# Logic:
existing = Dataset.query.filter_by(hash="aaa111...").first()  # FOUND

if existing.content_hash == "bbb222...":  # Content unchanged
    # Just update last_crawled_at
    existing.last_crawled_at = now()
    logger.info("ℹ️ Unchanged: Rwanda Population 2024")
```

**Result:** ✅ No update needed, just timestamp refresh

---

## Update Logic Flow

```python
def process_dataset(new_dataset):
    """Process crawled dataset - create or update"""

    # Look up by primary hash (URL-based)
    existing = Dataset.query.filter_by(
        hash=new_dataset['hash']
    ).first()

    if existing:
        # Dataset exists - check if content changed
        if existing.content_hash != new_dataset['content_hash']:
            # ✅ Content changed - UPDATE
            existing.title = new_dataset['title']
            existing.description = new_dataset['description']
            existing.tags = new_dataset['tags']
            existing.content_hash = new_dataset['content_hash']
            existing.updated_at = datetime.utcnow()

            logger.info(f"✅ UPDATED: {new_dataset['title']}")
            return 'updated'
        else:
            # ℹ️ No changes - just refresh timestamp
            existing.last_crawled_at = datetime.utcnow()

            logger.info(f"ℹ️ UNCHANGED: {new_dataset['title']}")
            return 'unchanged'
    else:
        # ✅ New dataset - CREATE
        dataset = Dataset(**new_dataset)
        db.session.add(dataset)

        logger.info(f"✅ CREATED: {new_dataset['title']}")
        return 'created'
```

---

## Database Schema

```python
class Dataset(db.Model):
    # Primary identifier (URL-based)
    hash = db.Column(db.String(64), unique=True, index=True, nullable=False)

    # Content identifier (metadata-based)
    content_hash = db.Column(db.String(64), index=True)

    # Metadata
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(JSONB)  # PostgreSQL JSONB

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_crawled_at = db.Column(db.DateTime)  # Last time we checked this URL
```

---

## Benefits

### ✅ **Prevents Duplicates**
- Same URL always has same `hash`
- Can't create two records with same URL

### ✅ **Tracks Updates**
- `content_hash` changes when metadata changes
- Know exactly when dataset was updated

### ✅ **Update Statistics**
```python
# After crawl
{
  "total_found": 150,
  "created": 10,      # New datasets
  "updated": 25,      # Changed metadata
  "unchanged": 115,   # No changes
  "errors": 0
}
```

### ✅ **Handles Edge Cases**
- URL changes → new dataset (correct!)
- Title changes → update (correct!)
- Description changes → update (correct!)
- No changes → skip (efficient!)

---

## Implementation

### **In DataProcessor:**

```python
# Generate both hashes
hash_value = DataProcessor.generate_hash(url)  # URL only
content_hash = DataProcessor.generate_content_hash(title, description, tags)

dataset = {
    'hash': hash_value,           # Primary key
    'content_hash': content_hash, # Change detection
    'title': title,
    'description': description,
    'tags': tags
}
```

### **In CrawlerService:**

```python
def _on_dataset_found(self, dataset: Dict):
    """Process found dataset"""

    # Look up by primary hash
    existing = Dataset.query.filter_by(hash=dataset['hash']).first()

    if existing:
        # Check content hash
        if existing.content_hash != dataset['content_hash']:
            # Update existing
            update_dataset(existing, dataset)
            stats['updated'] += 1
        else:
            # No changes
            stats['unchanged'] += 1
    else:
        # Create new
        create_dataset(dataset)
        stats['created'] += 1
```

---

## Summary

**Two hashes solve two problems:**

1. **`hash` (URL-based)** = "Is this the same resource?"
2. **`content_hash` (metadata-based)** = "Has this resource changed?"

This allows us to:
- ✅ Prevent duplicates
- ✅ Track updates
- ✅ Distinguish between new datasets and updated datasets
- ✅ Provide accurate statistics

**Perfect for handling your scenario: Same URL, different title = UPDATE!**
