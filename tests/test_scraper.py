"""
Tests for the Instagram scraper.

This module contains tests for the Instagram scraper functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.scraper import InstagramScraper


@pytest.fixture
def mock_response():
    """Create a mock response for testing."""
    mock = MagicMock()
    mock.text = """
    <html>
        <body>
            <article class="post">
                <a href="/p/ABC123/">Link</a>
                <div class="caption">Test post with #ukraine hashtag</div>
                <span class="likes">100</span>
                <span class="comments">10</span>
            </article>
            <article class="post">
                <a href="/p/DEF456/">Link</a>
                <div class="caption">Another test post</div>
                <span class="likes">200</span>
                <span class="comments">20</span>
            </article>
        </body>
    </html>
    """
    mock.raise_for_status = MagicMock()
    return mock


def test_contains_target_hashtag():
    """Test the _contains_target_hashtag method."""
    scraper = InstagramScraper("telegraph", ["ukraine", "us"])
    
    # Test with matching hashtag
    assert scraper._contains_target_hashtag("Post with #ukraine hashtag") is True
    
    # Test with matching hashtag in different case
    assert scraper._contains_target_hashtag("Post with #UKRAINE hashtag") is True
    
    # Test with non-matching hashtag
    assert scraper._contains_target_hashtag("Post with #other hashtag") is False
    
    # Test with None caption
    assert scraper._contains_target_hashtag(None) is False


@patch("requests.get")
def test_scrape_posts(mock_get, mock_response):
    """Test the scrape_posts method."""
    mock_get.return_value = mock_response
    
    scraper = InstagramScraper("telegraph", ["ukraine", "us"])
    posts = scraper.scrape_posts()
    
    # Check that we got the expected number of posts
    assert len(posts) == 2
    
    # Check the first post
    assert posts[0]["shortcode"] == "ABC123"
    assert posts[0]["caption"] == "Test post with #ukraine hashtag"
    assert posts[0]["likes_count"] == 100
    assert posts[0]["comments_count"] == 10
    assert posts[0]["has_target_hashtag"] is True
    
    # Check the second post
    assert posts[1]["shortcode"] == "DEF456"
    assert posts[1]["caption"] == "Another test post"
    assert posts[1]["likes_count"] == 200
    assert posts[1]["comments_count"] == 20
    assert posts[1]["has_target_hashtag"] is False 