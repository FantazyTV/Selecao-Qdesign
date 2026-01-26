"""
QDesign Pipeline Logger
Centralized logging configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class PipelineLogger:
    """Centralized logger for the pipeline"""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def setup(
        cls,
        name: str = "qdesign_pipeline",
        level: str = "INFO",
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        """
        Setup and return a configured logger
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for logging
        
        Returns:
            Configured logger instance
        """
        if cls._instance is not None:
            return cls._instance
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        cls._instance = logger
        return logger
    
    @classmethod
    def get(cls, name: str = "qdesign_pipeline") -> logging.Logger:
        """
        Get the logger instance (must call setup() first)
        
        Args:
            name: Logger name
        
        Returns:
            Logger instance
        """
        if cls._instance is None:
            cls.setup(name=name)
        return cls._instance


def get_logger(module_name: str = __name__) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        module_name: Name of the module
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"qdesign_pipeline.{module_name}")
