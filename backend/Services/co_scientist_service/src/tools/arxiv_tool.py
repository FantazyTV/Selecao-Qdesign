"""
ArXiv Search Tool

Searches arXiv.org for scientific papers using their public API.
API Documentation: https://info.arxiv.org/help/api/
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# ArXiv API base URL
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Relevant arXiv categories for biological/materials research
RELEVANT_CATEGORIES = [
    "q-bio",       # Quantitative Biology
    "physics.bio-ph",  # Biological Physics
    "cond-mat.soft",   # Soft Condensed Matter
    "cond-mat.mtrl-sci",  # Materials Science
]


@dataclass
class ArxivPaper:
    """Represents an arXiv paper."""
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str
    updated: str
    categories: list[str]
    pdf_url: str
    arxiv_url: str
    
    def to_dict(self) -> dict:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "published": self.published,
            "updated": self.updated,
            "categories": self.categories,
            "pdf_url": self.pdf_url,
            "arxiv_url": self.arxiv_url
        }
    
    def to_citation(self) -> str:
        """Generate a citation string."""
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        return f"{author_str}. \"{self.title}\" arXiv:{self.arxiv_id} ({self.published[:4]})"


class ArxivSearchTool(BaseTool):
    """Tool for searching arXiv scientific papers.
    
    Rate limit: arXiv recommends no more than 1 request per 3 seconds.
    """
    
    def __init__(self):
        super().__init__(
            requests_per_second=0.33,  # 1 request per 3 seconds
            burst_size=2,
            max_retries=3,
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "arxiv_search"
    
    @property
    def description(self) -> str:
        return "Search arXiv.org for scientific preprints and papers"
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        categories: Optional[list[str]] = None,
        sort_by: str = "relevance"
    ) -> ToolResult:
        """Search arXiv for papers matching the query.
        
        Args:
            query: Search query (supports arXiv query syntax)
            max_results: Maximum number of results (default 5, max 100)
            categories: Filter by arXiv categories (e.g., ["q-bio", "physics.bio-ph"])
            sort_by: Sort order - "relevance", "lastUpdatedDate", or "submittedDate"
            
        Returns:
            ToolResult containing list of ArxivPaper objects
        """
        try:
            # Build search query
            search_query = self._build_query(query, categories)
            
            # Map sort options
            sort_map = {
                "relevance": "relevance",
                "lastUpdatedDate": "lastUpdatedDate",
                "submittedDate": "submittedDate"
            }
            sort_by = sort_map.get(sort_by, "relevance")
            
            # Build URL
            params = {
                "search_query": search_query,
                "start": 0,
                "max_results": min(max_results, 100),
                "sortBy": sort_by,
                "sortOrder": "descending"
            }
            
            url = f"{ARXIV_API_URL}?search_query={quote_plus(search_query)}&start=0&max_results={params['max_results']}&sortBy={sort_by}&sortOrder=descending"
            
            logger.info(f"Searching arXiv: {query[:50]}...")
            
            # Make request
            response = await self._request_with_retry("GET", url)
            
            # Parse XML response
            papers = self._parse_response(response.text)
            
            logger.info(f"Found {len(papers)} papers on arXiv")
            
            return self._success_result(
                data=[p.to_dict() for p in papers],
                query=query,
                total_results=len(papers),
                search_url=url
            )
            
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return self._error_result(
                error=str(e),
                query=query
            )
    
    def _build_query(self, query: str, categories: Optional[list[str]] = None) -> str:
        """Build arXiv query string.
        
        Args:
            query: User's search query
            categories: Optional category filters
            
        Returns:
            Formatted arXiv query string
        """
        # Search in title and abstract
        base_query = f"all:{query}"
        
        if categories:
            cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
            return f"({base_query}) AND ({cat_query})"
        
        return base_query
    
    def _parse_response(self, xml_content: str) -> list[ArxivPaper]:
        """Parse arXiv API XML response.
        
        Args:
            xml_content: Raw XML response from arXiv API
            
        Returns:
            List of ArxivPaper objects
        """
        papers = []
        
        # Define namespaces
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }
        
        try:
            root = ET.fromstring(xml_content)
            
            for entry in root.findall("atom:entry", namespaces):
                # Extract arxiv ID from the id URL
                id_elem = entry.find("atom:id", namespaces)
                if id_elem is None:
                    continue
                    
                arxiv_id = id_elem.text.split("/abs/")[-1]
                
                # Title
                title_elem = entry.find("atom:title", namespaces)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""
                
                # Abstract
                summary_elem = entry.find("atom:summary", namespaces)
                abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
                
                # Authors
                authors = []
                for author in entry.findall("atom:author", namespaces):
                    name_elem = author.find("atom:name", namespaces)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                
                # Dates
                published_elem = entry.find("atom:published", namespaces)
                published = published_elem.text[:10] if published_elem is not None else ""
                
                updated_elem = entry.find("atom:updated", namespaces)
                updated = updated_elem.text[:10] if updated_elem is not None else ""
                
                # Categories
                categories = []
                for category in entry.findall("atom:category", namespaces):
                    term = category.get("term")
                    if term:
                        categories.append(term)
                
                # PDF link
                pdf_url = ""
                for link in entry.findall("atom:link", namespaces):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")
                        break
                
                paper = ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    published=published,
                    updated=updated,
                    categories=categories,
                    pdf_url=pdf_url,
                    arxiv_url=f"https://arxiv.org/abs/{arxiv_id}"
                )
                papers.append(paper)
                
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv XML: {e}")
        
        return papers
    
    async def search_biology(self, query: str, max_results: int = 5) -> ToolResult:
        """Search arXiv specifically for biology-related papers.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            ToolResult with biology papers
        """
        return await self.search(
            query=query,
            max_results=max_results,
            categories=["q-bio", "physics.bio-ph"]
        )
    
    async def search_materials(self, query: str, max_results: int = 5) -> ToolResult:
        """Search arXiv specifically for materials science papers.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            ToolResult with materials science papers
        """
        return await self.search(
            query=query,
            max_results=max_results,
            categories=["cond-mat.soft", "cond-mat.mtrl-sci"]
        )
