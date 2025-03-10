"""
Celery worker for scheduled tasks.

This module defines Celery tasks for scraping Instagram posts and sending
notifications.
"""

import logging
import os
from datetime import timedelta

from celery import Celery
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models import SessionLocal, create_post, get_post_by_shortcode, update_post
from app.notifications import TelegramNotifier
from app.scraper import InstagramScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT", "telegraph")
HASHTAGS_TO_MONITOR = os.getenv("HASHTAGS_TO_MONITOR", "ukraine,us").split(",")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))  # 10 minutes in seconds

# Create Celery app
app = Celery(
    "instagram_parser",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "scrape-instagram-posts": {
            "task": "app.worker.scrape_instagram_posts",
            "schedule": timedelta(seconds=CHECK_INTERVAL),
        },
    },
)

@app.task
def scrape_instagram_posts():
    """
    Celery task to scrape Instagram posts and send notifications.
    
    This task is scheduled to run every CHECK_INTERVAL seconds.
    """
    logger.info("Starting scheduled Instagram scraping task")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Scrape posts
        scraper = InstagramScraper(TARGET_ACCOUNT, HASHTAGS_TO_MONITOR)
        posts = scraper.scrape_posts()
        
        # Save posts to database
        for post_data in posts:
            existing_post = get_post_by_shortcode(db, post_data["shortcode"])
            
            if existing_post:
                # Update existing post
                update_post(db, existing_post, post_data)
            else:
                # Create new post
                create_post(db, post_data)
        
        # Send notifications
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        notifier.notify_new_posts(db)
        
        logger.info("Completed scheduled Instagram scraping task")
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}")
    finally:
        db.close()


@app.task
def send_notifications():
    """
    Celery task to send notifications for posts with target hashtags.
    
    This task can be triggered manually if needed.
    """
    logger.info("Starting notification task")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Send notifications
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        notifier.notify_new_posts(db)
        
        logger.info("Completed notification task")
    except Exception as e:
        logger.error(f"Error in notification task: {e}")
    finally:
        db.close() 