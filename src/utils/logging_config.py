"""
Logging configuration for the application.
"""

import logging
import sys
from pathlib import Path
from config.settings import settings


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(log_dir / "crypto_agent.log")
        ]
    )

    logger = logging.getLogger("crypto_agent")
    return logger


# Global logger instance
logger = setup_logging()
