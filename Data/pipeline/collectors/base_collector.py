"""
Base collector class
All collectors inherit from this
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class CollectorRecord:
    """Base record structure for all collected data"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_type: str = ""  # text, structure, sequence, image
    source: str = ""  # arxiv, biorxiv, pdb, custom
    collection: str = ""  # collection/category name
    
    # Raw content
    raw_content: Any = None
    source_url: Optional[str] = None
    
    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    date_collected: datetime = field(default_factory=datetime.utcnow)
    date_published: Optional[datetime] = None
    
    # Source-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing status
    processed: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling special types"""
        data = asdict(self)
        # Convert datetime to ISO format
        data['date_collected'] = self.date_collected.isoformat()
        if data['date_published']:
            data['date_published'] = self.date_published.isoformat()
        return data


class BaseCollector(ABC):
    """Abstract base class for all collectors"""
    
    def __init__(self, collection_name: str):
        """
        Initialize collector
        
        Args:
            collection_name: Name of the collection being built
        """
        self.collection_name = collection_name
        self.records: List[CollectorRecord] = []
    
    @abstractmethod
    def collect(self, *args, **kwargs) -> List[CollectorRecord]:
        """
        Collect data from source
        
        Returns:
            List of CollectorRecord objects
        """
        pass
    
    @abstractmethod
    def validate(self, record: CollectorRecord) -> bool:
        """
        Validate a record from this source
        
        Args:
            record: Record to validate
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def add_record(self, record: CollectorRecord) -> None:
        """Add a record to the collection"""
        if self.validate(record):
            self.records.append(record)
        else:
            record.error = "Validation failed"
            self.records.append(record)
    
    def get_valid_records(self) -> List[CollectorRecord]:
        """Get all valid (non-error) records"""
        return [r for r in self.records if r.error is None]
    
    def get_error_records(self) -> List[CollectorRecord]:
        """Get all records with errors"""
        return [r for r in self.records if r.error is not None]
    
    def count(self) -> int:
        """Get number of records collected"""
        return len(self.records)
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"collection={self.collection_name}, "
            f"records={self.count()}"
            f")"
        )
