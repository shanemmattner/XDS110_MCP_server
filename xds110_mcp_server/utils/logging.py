"""Logging setup utilities."""

import logging
import sys
from pathlib import Path


def setup_logging(debug: bool = False) -> logging.Logger:
    """Set up logging for the application."""
    
    # Create logger
    logger = logging.getLogger("xds110_mcp_server")
    
    # Set level
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(logs_dir / "xds110_mcp_server.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger