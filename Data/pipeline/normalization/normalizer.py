"""
Base normalizer class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseNormalizer(ABC):
    """Abstract base class for all normalizers"""
    
    @abstractmethod
    def normalize(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Normalize content
        
        Args:
            content: Content to normalize
            metadata: Optional metadata that might affect normalization
        
        Returns:
            Normalized content
        """
        pass
    
    @abstractmethod
    def is_applicable(self, data_type: str) -> bool:
        """
        Check if this normalizer applies to the given data type
        
        Args:
            data_type: Type of data (text, structure, sequence, image)
        
        Returns:
            True if applicable
        """
        pass
