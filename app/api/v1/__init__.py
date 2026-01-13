"""
API Version 1
Main API blueprint
"""
from flask import Blueprint

# Create API v1 blueprint
api_v1 = Blueprint('api_v1', __name__)

# Import routes to register them
from app.api.v1 import health, crawl, datasets

__all__ = ['api_v1']
