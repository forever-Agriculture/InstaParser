"""
Telegram notification module.

This module provides functionality to send notifications to Telegram
when posts with target hashtags are found.
"""

import logging
from typing import List

import telegram
from sqlalchemy.orm import Session

from app.models import Post, get_unnotified_posts, mark_post_as_notified

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Telegram notification class.
    
    This class provides methods to send notifications to Telegram.
    """

    def __init__(self, token: str, chat_id: str):
        """
        Initialize the Telegram notifier.
        
        Args:
            token (str): Telegram bot token
            chat_id (str): Telegram chat ID
        """
        self.token = token
        self.chat_id = chat_id
        
        # Initialize Telegram bot
        if token and chat_id:
            self.bot = telegram.Bot(token=token)
        else:
            self.bot = None
            logger.warning("Telegram bot not configured. Notifications will not be sent.")

    def notify_new_posts(self, db: Session) -> List[Post]:
        """
        Send notifications for posts with target hashtags.
        
        Args:
            db (Session): Database session
            
        Returns:
            List[Post]: List of notified posts
        """
        if not self.bot:
            logger.warning("Telegram bot not configured. Notifications will not be sent.")
            return []
        
        # Get posts with target hashtags that haven't been notified yet
        posts = get_unnotified_posts(db)
        
        if not posts:
            logger.info("No new posts to notify about.")
            return []
        
        logger.info(f"Sending notifications for {len(posts)} posts")
        
        # Send notifications
        notified_posts = []
        for post in posts:
            try:
                # Create message
                message = f"🔔 New post with target hashtag!\n\n"
                message += f"📝 Caption: {post.caption[:100]}...\n" if len(post.caption) > 100 else f"📝 Caption: {post.caption}\n"
                message += f"👍 Likes: {post.likes_count}\n"
                message += f"💬 Comments: {post.comments_count}\n"
                message += f"🔗 Link: {post.url}"
                
                # Send message
                self.bot.send_message(chat_id=self.chat_id, text=message, disable_web_page_preview=False)
                
                # Mark post as notified
                mark_post_as_notified(db, post)
                
                notified_posts.append(post)
                logger.info(f"Notification sent for post {post.shortcode}")
            except Exception as e:
                logger.error(f"Error sending notification for post {post.shortcode}: {e}")
        
        return notified_posts 