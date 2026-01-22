# Quick Start Guide

This guide will help you get the web crawler up and running in minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.10+ installed
- [ ] PostgreSQL 15+ installed and running
- [ ] Redis 7.0+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed

## Step-by-Step Setup

### 1. Database Setup

```bash
# Create database
createdb web_crawler_dev

# Verify database
psql web_crawler_dev
\dt  # Should show empty database
\q
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum required settings:**
```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://localhost/web_crawler_dev
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Migration

```bash
# Run migrations to create tables
flask db upgrade

# Verify tables were created
psql web_crawler_dev
\dt  # Should show all tables
\q
```

### 4. Create API Key (for testing)

```bash
# Open Python shell
python

# Create a test API key
from app import create_app
from app.models.api_key import APIKey
from app.extensions import db

app = create_app()
with app.app_context():
    key = APIKey.create(name="Test Key", description="For testing")
    db.session.add(key)
    db.session.commit()
    print(f"API Key: {key.key}")
    # Save this key for testing
```

## Running the Application

### Terminal 1: Redis
```bash
redis-server
```

**Expected output:**
```
Ready to accept connections
```

### Terminal 2: Flask API
```bash
python run.py
```

**Expected output:**
```
* Running on http://0.0.0.0:5000
* Debugger is active!
```

### Terminal 3: Celery Worker
```bash
celery -A celery_worker.celery_app worker -Q crawl --loglevel=info
```

**Expected output:**
```
[tasks]
  . app.tasks.run_crawl
celery@hostname ready.
```

## Verify Everything Works

### 1. Health Check
```bash
curl http://localhost:5000/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 2. Start a Test Crawl

```bash
curl -X POST http://localhost:5000/api/v1/crawl/start \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "1",
    "options": {
      "max_pages": 5,
      "test_mode": false
    }
  }'
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid-string",
    "celery_task_id": "task-id",
    "status": "pending"
  },
  "message": "Crawl job queued successfully"
}
```

### 3. Check Job Status

```bash
curl http://localhost:5000/api/v1/crawl/jobs/{job_id} \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "running",
    "progress_percentage": 45.5,
    "statistics": {
      "pages_crawled": 3,
      "datasets_found": 2
    }
  }
}
```

## Using the Test Script

For automated testing:

```bash
# Edit test script with your API key
nano test_crawl_flow.py
# Update: API_KEY = "your-api-key-here"

# Run the test
python test_crawl_flow.py

# Follow the prompts
```

The script will:
1. Start a crawl job
2. Monitor progress every 5 seconds
3. Display statistics in real-time
4. Show final results

## Common Issues

### Issue: "Connection refused" when starting Flask

**Solution:**
- Check if port 5000 is already in use
- Try: `lsof -i :5000` and kill the process
- Or change port in `.env`: `FLASK_PORT=5001`

### Issue: Celery worker won't start

**Solution:**
- Verify Redis is running: `redis-cli ping` (should return "PONG")
- Check REDIS_URL in `.env`
- Ensure virtual environment is activated

### Issue: Database migrations fail

**Solution:**
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in `.env`
- Ensure database exists: `psql -l | grep web_crawler`

### Issue: "API key invalid"

**Solution:**
- Create a new API key (see step 4 above)
- Verify key in database:
  ```bash
  psql web_crawler_dev
  SELECT key, name FROM api_keys;
  ```

### Issue: Crawl job stays in "pending" status

**Solution:**
- Check Celery worker is running
- Look for errors in Celery terminal
- Verify queue name: should be `-Q crawl`

## Monitoring

### View Celery Tasks
```bash
# Install Flower (if not already)
pip install flower

# Start Flower
celery -A celery_worker.celery_app flower --port=5555

# Access at: http://localhost:5555
```

### View Database Tables
```bash
psql web_crawler_dev

# List all jobs
SELECT job_id, status, site_id, created_at FROM crawl_jobs ORDER BY created_at DESC LIMIT 10;

# Count datasets
SELECT COUNT(*) FROM datasets;

# View recent datasets
SELECT title, source, created_at FROM datasets ORDER BY created_at DESC LIMIT 10;
```

### View Logs
```bash
# Flask logs (in Flask terminal)
# Celery logs (in Celery terminal)

# Application logs (if configured)
tail -f logs/app.log
```

## Next Steps

Now that everything is working:

1. **Explore the API**
   - Try different endpoints
   - Read [docs/DESIGN.md](DESIGN.md) for full API reference

2. **Understand the Flow**
   - Read [docs/CRAWL_FLOW.md](CRAWL_FLOW.md)
   - Study the architecture diagram

3. **Add New Sites**
   - Edit `configs/config.json`
   - Add site configuration
   - Test with your new site

4. **Development**
   - Read [docs/DESIGN.md](DESIGN.md) for architecture
   - Check code structure
   - Run tests: `pytest tests/`

## Quick Reference Commands

```bash
# Start all services
redis-server &
python run.py &
celery -A celery_worker.celery_app worker -Q crawl &

# Stop all services
pkill redis-server
pkill -f "python run.py"
pkill -f celery

# Reset database
flask db downgrade base
flask db upgrade

# Create new migration
flask db migrate -m "Description"

# Run tests
pytest tests/

# View logs
tail -f logs/*.log
```

## Documentation

- [README.md](../README.md) - Main project README
- [CRAWL_FLOW.md](CRAWL_FLOW.md) - End-to-end flow documentation
- [DESIGN.md](DESIGN.md) - Complete technical design
- [DATABASE_MODELS.md](DATABASE_MODELS.md) - Database schema

## Support

If you encounter issues:

1. Check terminal outputs for error messages
2. Review the Common Issues section above
3. Check the logs directory
4. Consult the full documentation

---

**Last Updated:** January 22, 2026
