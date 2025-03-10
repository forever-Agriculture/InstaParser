"""
Database models for the Instagram Parser.

This module defines the database models and utility functions for
interacting with the database.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/instagram_posts.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class Post(Base):
    """
    Post model.
    
    This class represents an Instagram post in the database.
    """

    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    shortcode = Column(String, unique=True, index=True)
    caption = Column(String)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    url = Column(String)
    has_target_hashtag = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self) -> Dict:
        """
        Convert the post to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the post
        """
        return {
            "id": self.id,
            "shortcode": self.shortcode,
            "caption": self.caption,
            "likes_count": self.likes_count,
            "comments_count": self.comments_count,
            "url": self.url,
            "has_target_hashtag": self.has_target_hashtag,
            "notified": self.notified,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Create tables
Base.metadata.create_all(bind=engine)


def get_all_posts(db: Session) -> List[Post]:
    """
    Get all posts.
    
    Args:
        db (Session): Database session
        
    Returns:
        List[Post]: List of posts
    """
    return db.query(Post).order_by(Post.scraped_at.desc()).all()


def get_post_by_shortcode(db: Session, shortcode: str) -> Optional[Post]:
    """
    Get a post by shortcode.
    
    Args:
        db (Session): Database session
        shortcode (str): Post shortcode
        
    Returns:
        Optional[Post]: Post if found, None otherwise
    """
    return db.query(Post).filter(Post.shortcode == shortcode).first()


def create_post(db: Session, post_data: Dict) -> Post:
    """
    Create a new post.
    
    Args:
        db (Session): Database session
        post_data (Dict): Post data
        
    Returns:
        Post: Created post
    """
    post = Post(**post_data)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_post(db: Session, post: Post, post_data: Dict) -> Post:
    """
    Update a post.
    
    Args:
        db (Session): Database session
        post (Post): Post to update
        post_data (Dict): Post data
        
    Returns:
        Post: Updated post
    """
    for key, value in post_data.items():
        setattr(post, key, value)
    
    db.commit()
    db.refresh(post)
    return post


def get_unnotified_posts(db: Session) -> List[Post]:
    """
    Get posts with target hashtags that haven't been notified yet.
    
    Args:
        db (Session): Database session
        
    Returns:
        List[Post]: List of unnotified posts
    """
    return db.query(Post).filter(Post.has_target_hashtag == True, Post.notified == False).all()


def mark_post_as_notified(db: Session, post: Post) -> Post:
    """
    Mark a post as notified.
    
    Args:
        db (Session): Database session
        post (Post): Post to mark as notified
        
    Returns:
        Post: Updated post
    """
    post.notified = True
    db.commit()
    db.refresh(post)
    return post 