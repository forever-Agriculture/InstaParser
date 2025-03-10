"""
Instagram scraper module.

This module provides functionality to scrape Instagram posts using Selenium,
which handles JavaScript-rendered content for reliable data extraction.
"""

import logging
import time
import re
import os
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class InstagramScraper:
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
        # Normalize hashtags to lowercase and remove duplicates
        self.hashtags_to_monitor = list(set([tag.lower() for tag in hashtags_to_monitor]))
        self.max_posts = max_posts
        self.base_url = f"https://www.instagram.com/{target_account}/"
        
        # Alternative URLs that might bypass login requirement
        self.alternative_urls = [
            f"https://www.instagram.com/{target_account}/",
            f"https://www.instagram.com/{target_account}/?__a=1&__d=dis",
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={target_account}"
        ]
        
        # Configure Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in headless mode
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # User agents to rotate (to avoid detection)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        # Set a random user agent
        self.chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
        # Create data directory if it doesn't exist
        os.makedirs("/app/data", exist_ok=True)
        
        # Cookies file path
        self.cookies_file = "/app/data/cookies.json"

    def _contains_target_hashtag(self, text: Optional[str]) -> bool:
        """
        Check if the text contains any of the target hashtags.
        
        Args:
            text (Optional[str]): Text to check for hashtags
            
        Returns:
            bool: True if the text contains a target hashtag, False otherwise
        """
        if not text:
            return False
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Method 1: Check for hashtags in the format #hashtag
        hashtags = re.findall(r'#(\w+)', text_lower)
        if hashtags:
            logger.info(f"Found hashtags: {hashtags}")
            
            for tag in self.hashtags_to_monitor:
                if tag in hashtags:
                    logger.info(f"Found target hashtag: #{tag}")
                    return True
        
        # Method 2: Direct string matching for each hashtag
        for hashtag in self.hashtags_to_monitor:
            if f"#{hashtag}" in text_lower:
                logger.info(f"Found target hashtag: #{hashtag}")
                return True
            
            # Also check without the # symbol (sometimes hashtags are mentioned without the symbol)
            if f" {hashtag} " in f" {text_lower} ":
                logger.info(f"Found target keyword: {hashtag}")
                return True
        
        return False

    def _save_cookies(self, driver: webdriver.Remote):
        """Save cookies to a file for later use."""
        try:
            cookies = driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            logger.info("Cookies saved successfully")
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")

    def _load_cookies(self, driver: webdriver.Remote):
        """Load cookies from file if available."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)
                logger.info("Cookies loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    def _get_post_urls(self, driver: webdriver.Remote) -> List[str]:
        """
        Get post URLs from the target account.
        
        Args:
            driver (webdriver.Remote): Selenium WebDriver
            
        Returns:
            List[str]: List of post URLs
        """
        logger.info(f"Getting post URLs from https://www.instagram.com/{self.target_account}/")
        
        # Try the main profile URL
        profile_url = f"https://www.instagram.com/{self.target_account}/"
        logger.info(f"Trying URL: {profile_url}")
        
        try:
            driver.get(profile_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            logger.info("Successfully accessed profile page")
            
            # Find post links
            logger.info("Trying to find posts with selector: article a[href*='/p/']")
            post_elements = driver.find_elements(By.CSS_SELECTOR, "article a[href*='/p/']")
            
            if not post_elements:
                # Try alternative selector
                logger.info("Trying alternative selector: a[href*='/p/']")
                post_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            
            # Extract URLs
            post_urls = []
            for element in post_elements:
                href = element.get_attribute("href")
                if href and "/p/" in href and href not in post_urls:
                    post_urls.append(href)
            
            if post_urls:
                logger.info(f"Found {len(post_urls)} posts")
                return post_urls
            else:
                logger.warning("No posts found on profile page")
                return []
                
        except Exception as e:
            logger.error(f"Error getting post URLs: {e}")
            return []

    def _get_post_details(self, driver: webdriver.Remote, post_url: str) -> Dict:
        """
        Get details for a specific post.
        
        Args:
            driver (webdriver.Remote): Selenium WebDriver instance
            post_url (str): URL of the post
            
        Returns:
            Dict: Post data dictionary
        """
        # Extract shortcode from URL
        shortcode = post_url.split("/p/")[1].rstrip("/")
        logger.info(f"Getting details for post {shortcode}")
        
        # Initialize post data
        post_data = {
            "id": f"post_{shortcode}",
            "shortcode": shortcode,
            "caption": "",
            "likes_count": 0,
            "comments_count": 0,
            "url": post_url,
            "has_target_hashtag": False,
            "scraped_at": datetime.now()
        }
        
        try:
            # Navigate to the post
            driver.get(post_url)
            
            # Wait for the post to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
            except TimeoutException:
                logger.error(f"Timed out waiting for post {shortcode} to load")
                driver.save_screenshot(f"/app/data/post_timeout_{shortcode}.png")
                return post_data
            
            # Take a screenshot of the post page
            driver.save_screenshot(f"/app/data/post_{shortcode}.png")
            
            # Get the page source for regex extraction
            page_source = driver.page_source
            page_source_lower = page_source.lower()
            
            # Get caption
            try:
                # Try different selectors to find the caption
                caption_selectors = [
                    "div._a9zr span",
                    "div.C4VMK span",
                    "article div:nth-child(3) span",
                    "h1 + div span",
                    "article span"
                ]
                
                for selector in caption_selectors:
                    try:
                        caption_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if caption_elements:
                            post_data["caption"] = caption_elements[0].text
                            logger.info(f"Found caption with selector {selector}: {post_data['caption'][:50]}...")
                            break
                    except:
                        continue
                
                # If no caption found, try to get it from the article
                if not post_data["caption"]:
                    article_elements = driver.find_elements(By.CSS_SELECTOR, "article")
                    if article_elements:
                        post_data["caption"] = article_elements[0].text
                        logger.info(f"Found caption from article: {post_data['caption'][:50]}...")
                        
                # If still no caption, try to extract it from the page source
                if not post_data["caption"]:
                    meta_description = re.search(r'<meta property="og:description" content="([^"]+)"', page_source)
                    if meta_description:
                        post_data["caption"] = meta_description.group(1)
                        logger.info(f"Found caption from meta description: {post_data['caption'][:50]}...")
            except Exception as e:
                logger.error(f"Error getting caption for post {shortcode}: {e}")
            
            # Get likes count
            try:
                # Look for text containing "likes" or similar
                likes_patterns = [
                    r'(\d+[,.]?\d*[KkMm]?)\s+likes',
                    r'liked by\s+(\d+[,.]?\d*[KkMm]?)',
                    r'(\d+[,.]?\d*[KkMm]?)\s+like this',
                    r'(\d+[,.]?\d*[KkMm]?)\s+views'
                ]
                
                for pattern in likes_patterns:
                    matches = re.findall(pattern, page_source_lower)
                    if matches:
                        likes_text = matches[0].replace(',', '')
                        # Handle K/M suffixes
                        if 'k' in likes_text.lower():
                            likes_text = likes_text.lower().replace('k', '')
                            likes_count = float(likes_text) * 1000
                        elif 'm' in likes_text.lower():
                            likes_text = likes_text.lower().replace('m', '')
                            likes_count = float(likes_text) * 1000000
                        else:
                            likes_count = float(likes_text)
                        
                        post_data["likes_count"] = int(likes_count)
                        logger.info(f"Found likes count: {post_data['likes_count']}")
                        break
            except Exception as e:
                logger.error(f"Error getting likes count for post {shortcode}: {e}")
            
            # Get comments count
            try:
                # Look for text containing "comments" or similar
                comments_patterns = [
                    r'(\d+,?\d*)\s+comments',
                    r'view all\s+(\d+,?\d*)\s+comments',
                    r'(\d+,?\d*)\s+comment'
                ]
                
                for pattern in comments_patterns:
                    matches = re.findall(pattern, page_source_lower)
                    if matches:
                        comments_text = matches[0].replace(',', '')
                        if comments_text.isdigit():
                            post_data["comments_count"] = int(comments_text)
                            logger.info(f"Found comments count: {post_data['comments_count']}")
                            break
            except Exception as e:
                logger.error(f"Error getting comments count for post {shortcode}: {e}")
            
            # Extract all text from the page for hashtag detection
            all_text = ""
            try:
                # Get text from the body
                body_element = driver.find_element(By.TAG_NAME, "body")
                all_text = body_element.text
                
                # Add caption
                all_text += " " + post_data["caption"]
                
                # Add page source (for hidden hashtags)
                all_text += " " + page_source
                
                # Log a sample of the text for debugging
                logger.info(f"Text sample for hashtag detection: {all_text[:200]}...")
            except Exception as e:
                logger.error(f"Error extracting text from page for post {shortcode}: {e}")
            
            # Look for hashtags in all text
            try:
                hashtag_pattern = r'#(\w+)'
                all_hashtags = re.findall(hashtag_pattern, all_text.lower())
                
                if all_hashtags:
                    logger.info(f"Found hashtags in post {shortcode}: {all_hashtags}")
                    
                    # Check if any of the target hashtags are in the extracted hashtags
                    for tag in self.hashtags_to_monitor:
                        if tag in all_hashtags:
                            post_data["has_target_hashtag"] = True
                            logger.info(f"Post {shortcode} has target hashtag: #{tag}")
                            break
            except Exception as e:
                logger.error(f"Error checking hashtags in page for post {shortcode}: {e}")
            
            # Final check using the _contains_target_hashtag method
            if not post_data["has_target_hashtag"]:
                post_data["has_target_hashtag"] = self._contains_target_hashtag(all_text)
            
        except Exception as e:
            logger.error(f"Error getting details for post {shortcode}: {e}")
        
        return post_data

    def scrape_posts(self) -> List[Dict]:
        """
        Scrape the latest posts from the target account with optimized performance.
        
        Returns:
            List[Dict]: List of post data dictionaries
        """
        logger.info(f"Scraping posts from {self.target_account} using Selenium")
        logger.info(f"Monitoring hashtags: {self.hashtags_to_monitor}")
        
        driver = None
        try:
            # Initialize the WebDriver with remote Chrome
            driver = webdriver.Remote(
                command_executor='http://chrome:4444/wd/hub',
                options=self.chrome_options
            )
            
            # Reduce page load timeout
            driver.set_page_load_timeout(5)
            
            # Load cookies if available
            driver.get("https://www.instagram.com")
            time.sleep(1)
            self._load_cookies(driver)
            
            # Get post URLs
            post_urls = self._get_post_urls(driver)
            
            if not post_urls:
                logger.error("No posts found")
                return []
            
            # Get details for each post
            posts = []
            for url in post_urls[:self.max_posts]:
                try:
                    post_data = self._get_post_details(driver, url)
                    posts.append(post_data)
                    
                    # Reduced sleep between requests
                    time.sleep(1)  # Reduced from 2 seconds
                except Exception as e:
                    logger.error(f"Error processing post {url}: {e}")
            
            logger.info(f"Scraped {len(posts)} posts from {self.target_account}")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping posts with Selenium: {e}")
            return []
        finally:
            if driver:
                driver.quit()