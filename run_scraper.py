"""
Script to run the Instagram scraper manually.

This script can be used to test the scraper without running the full API.
"""

import os
import sys
from dotenv import load_dotenv

from app.models import SessionLocal, create_post, get_post_by_shortcode, update_post
from app.scraper import InstagramScraper

# Load environment variables
load_dotenv()

# Get configuration from environment variables
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT", "telegraph")
HASHTAGS_TO_MONITOR = os.getenv("HASHTAGS_TO_MONITOR", "ukraine,us").split(",")


def main():
    """Run the scraper and print the results."""
    print(f"Scraping posts from {TARGET_ACCOUNT}")
    print(f"Monitoring hashtags: {HASHTAGS_TO_MONITOR}")
    
    # Create scraper
    scraper = InstagramScraper(TARGET_ACCOUNT, HASHTAGS_TO_MONITOR)
    
    # Scrape posts
    posts = scraper.scrape_posts()
    
    if not posts:
        print("No posts found.")
        return
    
    print(f"Found {len(posts)} posts:")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Save posts to database
        for post_data in posts:
            existing_post = get_post_by_shortcode(db, post_data["shortcode"])
            
            if existing_post:
                # Update existing post
                update_post(db, existing_post, post_data)
                print(f"Updated post: {post_data['shortcode']}")
            else:
                # Create new post
                create_post(db, post_data)
                print(f"Created post: {post_data['shortcode']}")
            
            # Print post details
            print(f"  Caption: {post_data['caption'][:50]}..." if post_data['caption'] else "  Caption: None")
            print(f"  Likes: {post_data['likes_count']}")
            print(f"  Comments: {post_data['comments_count']}")
            print(f"  Has target hashtag: {post_data['has_target_hashtag']}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main() 