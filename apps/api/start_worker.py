#!/usr/bin/env python3
"""
Celery worker startup script
Starts Celery worker process with proper configuration
"""

import os
import sys
import logging
from src.core.celery_app import celery_app
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def start_worker():
    """Start Celery worker with configuration"""
    try:
        logger.info("Starting Celery worker...")
        logger.info(f"Broker: {settings.celery_broker_url}")
        logger.info(f"Backend: {settings.celery_result_backend}")
        
        # Start worker with configuration
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--pool=prefork',
            '--without-gossip',
            '--without-mingle',
            '--without-heartbeat'
        ])
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_worker()