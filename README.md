# Dataset Crawler API

A world-class Flask-based API service for crawling, classifying, and publishing open datasets from various data portals.

## 🚀 Features

- **RESTful API** - Modern Flask API with comprehensive endpoints
- **Background Processing** - Celery + Redis for async crawling
- **PostgreSQL Database** - Production-grade data persistence
- **API Key Authentication** - Secure access control
- **Real-time Progress** - Monitor crawl jobs in real-time
- **SDG Classification** - AI-powered dataset categorization
- **Multi-site Crawling** - Support for static and dynamic websites
- **Docker Ready** - Containerized for easy deployment
- **Kubernetes Support** - Scale horizontally with K8s

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Client    │────▶│  Flask API  │────▶│  PostgreSQL  │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌──────────────┐
                    │ Celery Worker│────▶│    Redis     │
                    └──────────────┘     └──────────────┘
```

**Tech Stack:**
- Flask 3.0+ (Web Framework)
- PostgreSQL 15+ (Database)
- Celery 5.3+ (Task Queue)
- Redis 7.0+ (Message Broker & Cache)
- Scrapy 2.11+ (Web Scraping)
- SQLAlchemy 2.0+ (ORM)

## 📦 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Redis 7.0+
- pip & virtualenv

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd web_crawler
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 4: Set Up PostgreSQL

```bash
# Create database
createdb web_crawler_dev

# Or via psql
psql postgres
CREATE DATABASE web_crawler_dev;
\q
```

### Step 5: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Step 6: Initialize Database

```bash
# Run migrations
flask db upgrade

# Seed initial data (optional)
python scripts/seed_data.py
```

## ⚙️ Configuration

Key environment variables in `.env`:

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://localhost/web_crawler_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (for classification)
OPENAI_API_KEY=sk-your-key-here
```

See `.env.example` for complete configuration options.

## 🏃 Running the Application

### Development Mode

**Terminal 1: Start Redis**
```bash
redis-server
```

**Terminal 2: Start Flask API**
```bash
python run.py
# or
flask run
```

**Terminal 3: Start Celery Worker**
```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

**Terminal 4: Start Celery Flower (optional - monitoring)**
```bash
celery -A celery_worker.celery_app flower --port=5555
```

### Access Points

- **API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API v1**: http://localhost:5000/api/v1
- **Flower (Celery Monitor)**: http://localhost:5555

## 📚 API Documentation

### Authentication

All API requests require an API key in the header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/v1/datasets
```

### Core Endpoints

#### Health & Status
- `GET /health` - System health check
- `GET /api/v1/stats` - System statistics

#### Crawl Management
- `POST /api/v1/crawl/start` - Start new crawl job
- `GET /api/v1/crawl/jobs` - List all crawl jobs
- `GET /api/v1/crawl/jobs/{id}` - Get crawl job details
- `POST /api/v1/crawl/jobs/{id}/cancel` - Cancel crawl job

#### Datasets
- `GET /api/v1/datasets` - List datasets (paginated)
- `GET /api/v1/datasets/{id}` - Get dataset details
- `POST /api/v1/datasets` - Create dataset manually
- `PATCH /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset

### Example Requests

**Start a crawl job:**
```bash
curl -X POST http://localhost:5000/api/v1/crawl/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "uganda-portal",
    "start_url": "http://catalog.data.ug/dataset",
    "options": {
      "test_mode": false,
      "max_pages": 100
    }
  }'
```

**List datasets:**
```bash
curl http://localhost:5000/api/v1/datasets?page=1&limit=50 \
  -H "X-API-Key: your-api-key"
```

See [DESIGN.md](docs/DESIGN.md) for complete API documentation.

## 🛠️ Development

### Project Structure

```
web_crawler/
├── app/
│   ├── api/              # API endpoints
│   │   └── v1/           # API version 1
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   ├── crawlers/         # Web crawlers
│   ├── schemas/          # Data schemas
│   └── utils/            # Utilities
├── migrations/           # Database migrations
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── docker/               # Docker files
├── k8s/                  # Kubernetes manifests
├── run.py                # App entry point
├── celery_worker.py      # Celery entry point
└── requirements.txt      # Dependencies
```

### Code Quality

```bash
# Format code
black app tests

# Lint code
flake8 app tests

# Type checking
mypy app

# Sort imports
isort app tests
```

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Adding New Endpoints

1. Create route in `app/api/v1/your_module.py`
2. Import in `app/api/v1/__init__.py`
3. Add tests in `tests/test_api/test_your_module.py`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_crawl.py

# Run specific test
pytest tests/test_api/test_crawl.py::test_start_crawl
```

## 🐳 Docker Deployment

### Build and Run with Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services

```bash
# PostgreSQL
docker-compose up -d postgres

# Redis
docker-compose up -d redis

# API Server
docker-compose up -d api

# Celery Worker
docker-compose up -d celery_worker
```

## ☸️ Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/crawler-api

# Scale workers
kubectl scale deployment celery-worker --replicas=5
```

## 📊 Monitoring

### Logs

```bash
# View Flask logs
tail -f logs/app.log

# View Celery logs
tail -f logs/celery.log
```

### Metrics

- Prometheus metrics: http://localhost:5000/metrics
- Celery monitor (Flower): http://localhost:5555

### Health Checks

```bash
# Quick health check
curl http://localhost:5000/health

# Detailed stats
curl http://localhost:5000/api/v1/stats
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please contact the development team.

---

**Documentation:**
- [Design Document](docs/DESIGN.md) - Architecture and technical design
- [Setup Guide](docs/SETUP_COMPLETE.md) - Project setup completion summary
- [API Reference](docs/DESIGN.md#api-design) - Complete API documentation
- [Development Guide](docs/DESIGN.md#project-structure) - Development guidelines
