"""
Base ingester class
All ingesters inherit from this
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class IngestedRecord:
    """Record after ingestion"""
    id: str
    data_type: str  # text, structure, sequence, image
    source: str
    collection: str
    
    # Processed content
    content: str  # Extracted/parsed content
    normalized_content: Optional[str] = None
    
    # Raw content (for images: PIL Image object, for others: original file content)
    raw_content: Optional[Any] = None
    
    # Metadata from ingestion
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Ingestion info
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_length: Optional[int] = None
    
    # Error tracking
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class BaseIngester(ABC):
    """Abstract base class for all ingesters"""
    
    @abstractmethod
    def can_ingest(self, source: str) -> bool:
        """
        Check if this ingester can handle the source
        
        Args:
            source: File path or source identifier
        
        Returns:
            True if this ingester can handle it
        """
        pass
    
    @abstractmethod
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest data from source
        
        Args:
            source: File path or source identifier
            record_id: ID of the record being ingested
            **kwargs: Additional arguments specific to the ingester
        
        Returns:
            IngestedRecord with extracted content
        """
        pass
    
    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size
