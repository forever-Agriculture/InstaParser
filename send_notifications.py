"""
Script to send Telegram notifications manually.

This script can be used to test the Telegram notifier without running the full API.
"""

import os
from dotenv import load_dotenv

from app.models import SessionLocal
from app.notifications import TelegramNotifier

# Load environment variables
load_dotenv()

# Get configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def main():
    """Send notifications for posts with target hashtags."""
    print("Sending notifications for posts with target hashtags")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file.")
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create notifier
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        # Send notifications
        notified_posts = notifier.notify_new_posts(db)
        
        if not notified_posts:
            print("No new posts with target hashtags to notify.")
            return
        
        print(f"Sent notifications for {len(notified_posts)} posts:")
        
        for post in notified_posts:
            print(f"  Post: {post.shortcode}")
            print(f"  Caption: {post.caption[:50]}...")
            print(f"  URL: {post.url}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main() 