# Instagram Parser

An application for scraping and monitoring Instagram posts for specific hashtags.

## Overview

Instagram Parser is a containerized application that:
- Scrapes posts from specified Instagram accounts (e.g. @telegraph)
- Monitors posts for target hashtags (e.g. #ukraine or #Ukraine)
- Stores post data in a database
- Sends notifications via Telegram when posts with target hashtags are found
- Runs scheduled tasks using Celery for continuous monitoring

## Architecture

The application consists of several components:
- **API**: FastAPI-based REST API for interacting with the application
- **Scraper**: Selenium-based scraper for extracting data from Instagram
- **Worker**: Celery worker for running background tasks
- **Beat**: Celery beat for scheduling periodic tasks
- **Redis**: Message broker for Celery
- **Chrome**: Headless Chrome browser for Selenium

## Setup and running

### Prerequisites
- Docker and Docker Compose
- Telegram Bot (for notifications)

### Setup
Build and start the Docker containers using Docker Compose:
- docker-compose up --build -d

Check if all containers are running:
- docker ps

Access the API at http://localhost:8000/docs to verify it's working

Check Celery:
- docker-compose exec worker celery -A app.worker inspect active
- docker-compose logs worker
- docker-compose logs beat

Stop the containers:
- docker-compose down
