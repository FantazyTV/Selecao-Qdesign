"""
Text normalizer
"""

import re
from typing import Dict, Any, Optional
from .normalizer import BaseNormalizer
from ..logger import get_logger

logger = get_logger(__name__)


class TextNormalizer(BaseNormalizer):
    """Normalize text content"""
    
    def normalize(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Normalize text content
        
        Args:
            content: Text to normalize
            metadata: Optional metadata
        
        Returns:
            Normalized text
        """
        try:
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            # Remove control characters
            content = ''.join(c for c in content if ord(c) >= 32 or c in '\n\t\r')
            
            # Normalize newlines
            content = content.replace('\r\n', '\n')
            content = content.replace('\r', '\n')
            
            # Remove duplicate newlines
            content = re.sub(r'\n\n+', '\n\n', content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error normalizing text: {e}")
            return content
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "text"
