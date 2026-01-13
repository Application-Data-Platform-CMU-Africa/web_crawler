"""
Application Entry Point
Run the Flask development server
"""
import os
from app import create_app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    # Run the app
    app.run(
        host=host,
        port=port,
        debug=debug
    )
