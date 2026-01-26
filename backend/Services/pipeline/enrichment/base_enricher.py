"""
Base enricher class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseEnricher(ABC):
    """Abstract base class for all enrichers"""
    
    @abstractmethod
    def enrich(
        self,
        content: str,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich metadata with additional information
        
        Args:
            content: Content to analyze
            metadata: Existing metadata
            data_type: Type of data
        
        Returns:
            Enhanced metadata dictionary
        """
        pass
    
    @abstractmethod
    def is_applicable(self, data_type: str) -> bool:
        """
        Check if this enricher applies to the given data type
        
        Args:
            data_type: Type of data (text, structure, sequence, image)
        
        Returns:
            True if applicable
        """
        pass
