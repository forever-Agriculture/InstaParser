"""
Instagram scraper using Selenium.

This module provides functionality to scrape Instagram posts using Selenium
to handle JavaScript-rendered content.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class InstagramSeleniumScraper:
    """
    Instagram scraper class using Selenium.
    
    This class provides methods to scrape Instagram posts from public accounts
    using Selenium to handle JavaScript-rendered content.
    """

    def __init__(self, target_account: str, hashtags_to_monitor: List[str], max_posts: int = 10):
        """
        Initialize the Instagram scraper.
        
        Args:
            target_account (str): Instagram account to scrape
            hashtags_to_monitor (List[str]): List of hashtags to monitor
            max_posts (int): Maximum number of posts to retrieve
        """
        self.target_account = target_account
        self.hashtags_to_monitor = hashtags_to_monitor
        self.max_posts = max_posts
        self.base_url = f"https://www.instagram.com/{target_account}/"
        
        # Configure Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in headless mode
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent to mimic a real browser
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    def _contains_target_hashtag(self, caption: Optional[str]) -> bool:
        """
        Check if the caption contains any of the target hashtags.
        
        Args:
            caption (Optional[str]): Post caption
            
        Returns:
            bool: True if the caption contains a target hashtag, False otherwise
        """
        if not caption:
            return False
            
        caption = caption.lower()
        return any(f"#{hashtag.lower()}" in caption for hashtag in self.hashtags_to_monitor)

    def scrape_posts(self) -> List[Dict]:
        """
        Scrape the latest posts from the target account.
        
        Returns:
            List[Dict]: List of post data dictionaries
        """
        logger.info(f"Scraping posts from {self.target_account} using Selenium")
        
        driver = None
        try:
            # Initialize the WebDriver
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Navigate to the Instagram profile
            driver.get(self.base_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Allow time for dynamic content to load
            time.sleep(3)
            
            # Find post elements
            post_elements = driver.find_elements(By.TAG_NAME, "article")[:self.max_posts]
            
            # Extract post data
            posts = []
            for post_element in post_elements:
                try:
                    # Find the post link
                    post_link = post_element.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                    shortcode = post_link.get_attribute("href").split("/p/")[1].rstrip("/")
                    
                    # Find the caption
                    try:
                        caption_element = post_element.find_element(By.CSS_SELECTOR, ".caption")
                        caption = caption_element.text
                    except:
                        caption = ""
                    
                    # Find likes count
                    try:
                        likes_element = post_element.find_element(By.CSS_SELECTOR, ".likes")
                        likes_count = int(likes_element.text.replace(",", ""))
                    except:
                        likes_count = 0
                    
                    # Find comments count
                    try:
                        comments_element = post_element.find_element(By.CSS_SELECTOR, ".comments")
                        comments_count = int(comments_element.text.replace(",", ""))
                    except:
                        comments_count = 0
                    
                    # Create post data dictionary
                    post_data = {
                        "id": f"post_{shortcode}",
                        "shortcode": shortcode,
                        "caption": caption,
                        "likes_count": likes_count,
                        "comments_count": comments_count,
                        "url": f"https://www.instagram.com/p/{shortcode}/",
                        "posted_at": datetime.now(),  # Approximate time
                        "has_target_hashtag": self._contains_target_hashtag(caption),
                        "scraped_at": datetime.now(),
                    }
                    
                    posts.append(post_data)
                except Exception as e:
                    logger.error(f"Error extracting post data: {e}")
            
            logger.info(f"Scraped {len(posts)} posts from {self.target_account}")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping posts with Selenium: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def get_post_details(self, shortcode: str) -> Dict:
        """
        Get detailed information about a specific post.
        
        Args:
            shortcode (str): Post shortcode
            
        Returns:
            Dict: Dictionary with post details
        """
        logger.info(f"Getting details for post {shortcode} using Selenium")
        
        driver = None
        try:
            # Initialize the WebDriver
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Navigate to the post URL
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            driver.get(post_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Allow time for dynamic content to load
            time.sleep(2)
            
            # Extract post details
            try:
                caption_element = driver.find_element(By.CSS_SELECTOR, ".caption")
                caption = caption_element.text
            except:
                caption = ""
            
            try:
                likes_element = driver.find_element(By.CSS_SELECTOR, ".likes")
                likes_count = int(likes_element.text.replace(",", ""))
            except:
                likes_count = 0
            
            try:
                comments_element = driver.find_element(By.CSS_SELECTOR, ".comments")
                comments_count = int(comments_element.text.replace(",", ""))
            except:
                comments_count = 0
            
            # Create post details dictionary
            post_details = {
                "id": f"post_{shortcode}",
                "shortcode": shortcode,
                "caption": caption,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "url": post_url,
                "has_target_hashtag": self._contains_target_hashtag(caption),
                "scraped_at": datetime.now(),
            }
            
            return post_details
            
        except Exception as e:
            logger.error(f"Error getting post details with Selenium: {e}")
            return {}
        finally:
            if driver:
                driver.quit() 