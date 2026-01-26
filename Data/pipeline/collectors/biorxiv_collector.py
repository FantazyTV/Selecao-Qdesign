"""
BioRxiv preprint collector
Fetches preprints from bioRxiv API
"""

import requests
from datetime import datetime
from typing import List
from .base_collector import BaseCollector, CollectorRecord
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class BiorxivCollector(BaseCollector):
    """Collect preprints from BioRxiv"""
    
    def __init__(self, max_results: int = 100):
        """
        Initialize BioRxiv collector
        
        Args:
            max_results: Maximum number of preprints to fetch
        """
        super().__init__("biorxiv_preprints")
        self.max_results = max_results
        config = get_config()
        self.api_url = config.biorxiv_api_url
        self.timeout = config.request_timeout
        self.max_retries = config.max_retries
    
    def collect(
        self,
        query: str = "protein engineering",
        limit: int = 100,
        sort_by: str = "date",
        direction: str = "descending"
    ) -> List[CollectorRecord]:
        """
        Collect preprints from BioRxiv
        
        Args:
            query: Search query
            limit: Number of results
            sort_by: Sort field
            direction: Sort direction
        
        Returns:
            List of collected records
        """
        logger.info(f"Starting BioRxiv collection: query='{query}'")
        self.records = []
        
        # BioRxiv uses different endpoint for search
        url = f"{self.api_url}/search"
        
        params = {
            "query": query,
            "limit": min(limit, self.max_results),
            "sort": sort_by,
            "direction": direction
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # BioRxiv returns results in 'results' key
            results = data.get("results", [])
            
            for item in results:
                try:
                    record = self._parse_item(item)
                    self.add_record(record)
                except Exception as e:
                    logger.warning(f"Failed to parse BioRxiv item: {e}")
            
            logger.info(f"Successfully collected {len(self.get_valid_records())} preprints from BioRxiv")
            
        except Exception as e:
            logger.error(f"Failed to collect from BioRxiv: {e}")
        
        return self.records
    
    def _parse_item(self, item: dict) -> CollectorRecord:
        """Parse a single BioRxiv item"""
        title = item.get("title", "Unknown")
        abstract = item.get("abstract", "")
        
        # Get URL
        doi = item.get("doi", "")
        url = f"https://doi.org/{doi}" if doi else ""
        
        # Parse date
        date_str = item.get("date", item.get("published", ""))
        date_published = None
        if date_str:
            try:
                date_published = datetime.fromisoformat(date_str.split("T")[0])
            except:
                pass
        
        # Get authors
        authors_str = item.get("authors", "")
        authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []
        
        # Get category/subject
        category = item.get("category", item.get("subject", ""))
        
        record = CollectorRecord(
            data_type="text",
            source="biorxiv",
            collection=self.collection_name,
            raw_content=abstract,
            source_url=url,
            title=title,
            description=abstract[:500],
            date_published=date_published,
            metadata={
                "doi": doi,
                "authors": authors,
                "category": category,
                "version": item.get("version", "1"),
                "server": "bioRxiv"
            }
        )
        
        return record
    
    def validate(self, record: CollectorRecord) -> bool:
        """Validate BioRxiv record"""
        return (
            record.data_type == "text" and
            record.source == "biorxiv" and
            record.title and
            record.raw_content and
            len(record.raw_content) > 50
        )
