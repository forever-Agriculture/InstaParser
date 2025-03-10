"""
Celery worker module.

This module imports the Celery app from app.worker to make it available
for the Celery command-line interface.
"""

from app.worker import app

if __name__ == "__main__":
    app.start() 