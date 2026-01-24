"""
ArXiv paper collector
Fetches papers from arXiv API
"""

import requests
from datetime import datetime
from typing import List, Optional
from .base_collector import BaseCollector, CollectorRecord
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class ArxivCollector(BaseCollector):
    """Collect papers from arXiv"""
    
    def __init__(self, max_results: int = 100):
        """
        Initialize ArXiv collector
        
        Args:
            max_results: Maximum number of papers to fetch
        """
        super().__init__("arxiv_papers")
        self.max_results = max_results
        config = get_config()
        self.api_url = config.arxiv_api_url
        self.timeout = config.request_timeout
        self.max_retries = config.max_retries
    
    def collect(
        self,
        query: str = "protein engineering",
        category: str = "q-bio",
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> List[CollectorRecord]:
        """
        Collect papers from arXiv
        
        Args:
            query: Search query
            category: Category filter (e.g., 'q-bio.BM' for biomolecules)
            sort_by: Sort field
            sort_order: Sort order
        
        Returns:
            List of collected records
        """
        logger.info(f"Starting ArXiv collection: query='{query}'")
        self.records = []
        
        params = {
            "search_query": f"({query}) AND cat:{category}",
            "start": 0,
            "max_results": self.max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        try:
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse Atom feed with proper namespace handling
            import xml.etree.ElementTree as ET
            
            # Register namespace to avoid prefix issues
            ET.register_namespace('', 'http://www.w3.org/2005/Atom')
            ET.register_namespace('arxiv', 'http://arxiv.org/schemas/atom')
            
            root = ET.fromstring(response.content)
            
            # Define namespace map
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Find all entries (use atom namespace)
            entries = root.findall("atom:entry", ns)
            
            if not entries:
                logger.warning("No entries found in response")
                return self.records
            
            for entry in entries:
                try:
                    record = self._parse_entry(entry, ns)
                    self.add_record(record)
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")
            
            logger.info(f"Successfully collected {len(self.get_valid_records())} papers from ArXiv")
            
        except Exception as e:
            logger.error(f"Failed to collect from ArXiv: {e}")
        
        return self.records
    
    def _parse_entry(self, entry, ns: dict) -> CollectorRecord:
        """Parse a single ArXiv entry"""
        # Use the atom namespace
        atom_prefix = "{http://www.w3.org/2005/Atom}"
        
        title_elem = entry.find(f"atom:title", ns)
        title = title_elem.text if title_elem is not None else "Unknown"
        
        summary_elem = entry.find(f"atom:summary", ns)
        summary = summary_elem.text if summary_elem is not None else ""
        
        # Get arXiv ID
        id_elem = entry.find(f"atom:id", ns)
        arxiv_id = id_elem.text if id_elem is not None else ""
        arxiv_id = arxiv_id.split("/abs/")[-1] if arxiv_id else ""
        
        # Get published date
        published_elem = entry.find(f"atom:published", ns)
        date_published = None
        if published_elem is not None:
            try:
                date_published = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
            except:
                pass
        
        # Get authors
        authors = []
        for author in entry.findall(f"atom:author", ns):
            name_elem = author.find(f"atom:name", ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        
        # Get PDF URL
        pdf_url = None
        for link in entry.findall(f"atom:link", ns):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href")
                break
        
        record = CollectorRecord(
            data_type="text",
            source="arxiv",
            collection=self.collection_name,
            raw_content=summary,
            source_url=f"https://arxiv.org/abs/{arxiv_id}",
            title=title,
            description=summary[:500],
            date_published=date_published,
            metadata={
                "arxiv_id": arxiv_id,
                "pdf_url": pdf_url,
                "authors": authors,
                "categories": self._get_categories(entry, ns)
            }
        )
        
        return record
    
    def _get_categories(self, entry, ns: dict) -> List[str]:
        """Extract category information"""
        categories = []
        for cat in entry.findall(f"atom:category", ns):
            term = cat.get("term")
            if term:
                categories.append(term)
        return categories
    
    def validate(self, record: CollectorRecord) -> bool:
        """Validate ArXiv record"""
        return (
            record.data_type == "text" and
            record.source == "arxiv" and
            record.title and
            record.raw_content and
            len(record.raw_content) > 50
        )
