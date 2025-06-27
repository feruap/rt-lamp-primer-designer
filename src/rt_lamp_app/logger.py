
"""
Logging utilities for the RT-LAMP application.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional logging level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)

