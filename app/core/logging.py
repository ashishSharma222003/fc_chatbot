"""
Logging Configuration

This file sets up the logging configuration for the application.
It ensures that logs are formatted correctly and output to the appropriate
streams (console/file), helping with debugging and monitoring.
"""
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger

logger = setup_logging()
