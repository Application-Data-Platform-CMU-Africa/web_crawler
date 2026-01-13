"""
Celery Worker Entry Point
Start Celery workers for background task processing
"""
from app import create_app
from app.extensions import celery

# Create Flask app to initialize Celery with app context
app = create_app()

# Make Celery application available for worker
celery_app = celery

if __name__ == '__main__':
    # This is here for documentation
    # Actually run with: celery -A celery_worker.celery_app worker
    print("Start Celery worker with:")
    print("  celery -A celery_worker.celery_app worker --loglevel=info")
    print("  celery -A celery_worker.celery_app worker -Q crawl --loglevel=info")
