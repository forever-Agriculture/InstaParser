"""
FastAPI application for Instagram Parser.

This module defines the FastAPI application and its endpoints.
"""

import logging
from typing import Dict, List

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import SessionLocal, get_all_posts, Post
from app.worker import scrape_instagram_posts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Instagram Parser",
    description="API for parsing Instagram posts and monitoring hashtags",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> Dict:
    """
    Root endpoint.
    
    Returns:
        Dict: Basic information about the API
    """
    return {
        "name": "Instagram Parser API",
        "version": "1.0.0",
        "description": "API for parsing Instagram posts and monitoring hashtags",
    }

@app.get("/posts")
def read_posts() -> List[Dict]:
    """
    Get all posts.
    
    Returns:
        List[Dict]: List of posts
    """
    db = SessionLocal()
    try:
        posts = get_all_posts(db)
        return [post.to_dict() for post in posts]
    finally:
        db.close()

@app.post("/scrape")
def scrape_posts() -> Dict:
    """
    Trigger a manual scrape of Instagram posts.
    
    Returns:
        Dict: Status message
    """
    try:
        result = scrape_instagram_posts.apply()
        return {"status": "success", "message": "Scrape completed", "task_id": result.id}
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/async")
def scrape_posts_async(background_tasks: BackgroundTasks) -> Dict:
    """
    Trigger an asynchronous scrape of Instagram posts.
    
    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks
        
    Returns:
        Dict: Status message
    """
    try:
        task = scrape_instagram_posts.delay()
        return {"status": "success", "message": "Scrape started", "task_id": task.id}
    except Exception as e:
        logger.error(f"Error triggering async scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check() -> Dict:
    """
    Health check endpoint.
    
    Returns:
        Dict: Health status
    """
    return {"status": "healthy"} 