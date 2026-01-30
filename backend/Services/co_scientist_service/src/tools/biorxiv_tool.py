"""
bioRxiv Search Tool

Searches bioRxiv.org for biology preprints using their API.
API Documentation: https://api.biorxiv.org/
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# bioRxiv API base URL
BIORXIV_API_URL = "https://api.biorxiv.org"


@dataclass
class BiorxivPaper:
    """Represents a bioRxiv preprint."""
    doi: str
    title: str
    authors: str
    abstract: str
    date: str
    category: str
    biorxiv_url: str
    pdf_url: str
    version: str
    
    def to_dict(self) -> dict:
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "date": self.date,
            "category": self.category,
            "biorxiv_url": self.biorxiv_url,
            "pdf_url": self.pdf_url,
            "version": self.version
        }
    
    def to_citation(self) -> str:
        """Generate a citation string."""
        author_list = self.authors.split(";")
        author_str = author_list[0].strip()
        if len(author_list) > 1:
            author_str += " et al."
        year = self.date[:4] if self.date else ""
        return f"{author_str}. \"{self.title}\" bioRxiv doi:{self.doi} ({year})"


class BiorxivSearchTool(BaseTool):
    """Tool for searching bioRxiv preprints.
    
    Rate limit: bioRxiv API allows reasonable usage, we use 1 req/sec.
    """
    
    def __init__(self):
        super().__init__(
            requests_per_second=1.0,
            burst_size=3,
            max_retries=3,
            timeout=30.0
        )
    
    @property
    def name(self) -> str:
        return "biorxiv_search"
    
    @property
    def description(self) -> str:
        return "Search bioRxiv.org for biology preprints"
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        days_back: int = 365,
        server: str = "biorxiv"
    ) -> ToolResult:
        """Search bioRxiv for papers.
        
        Note: bioRxiv API doesn't support direct keyword search.
        We use the content detail endpoint and filter results.
        For keyword search, we query recent papers and filter client-side.
        
        Args:
            query: Search query (keywords to look for in title/abstract)
            max_results: Maximum number of results
            days_back: How many days back to search
            server: "biorxiv" or "medrxiv"
            
        Returns:
            ToolResult with matching papers
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for API
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            # bioRxiv API endpoint for content by date range
            # We'll fetch recent papers and filter by query
            url = f"{BIORXIV_API_URL}/details/{server}/{start_str}/{end_str}/0/100"
            
            logger.info(f"Searching bioRxiv: {query[:50]}...")
            
            response = await self._request_with_retry("GET", url)
            data = response.json()
            
            # Parse and filter results
            papers = self._parse_and_filter(data, query, max_results)
            
            logger.info(f"Found {len(papers)} matching papers on bioRxiv")
            
            return self._success_result(
                data=[p.to_dict() for p in papers],
                query=query,
                total_results=len(papers),
                date_range=f"{start_str} to {end_str}"
            )
            
        except Exception as e:
            logger.error(f"bioRxiv search failed: {e}")
            return self._error_result(
                error=str(e),
                query=query
            )
    
    def _parse_and_filter(
        self,
        data: dict,
        query: str,
        max_results: int
    ) -> list[BiorxivPaper]:
        """Parse API response and filter by query keywords.
        
        Args:
            data: Raw API response
            query: Search query for filtering
            max_results: Maximum results to return
            
        Returns:
            List of matching BiorxivPaper objects
        """
        papers = []
        collection = data.get("collection", [])
        
        # Tokenize query for matching
        query_terms = query.lower().split()
        
        for item in collection:
            if len(papers) >= max_results:
                break
            
            title = item.get("title", "")
            abstract = item.get("abstract", "")
            
            # Check if any query term appears in title or abstract
            text = f"{title} {abstract}".lower()
            if any(term in text for term in query_terms):
                doi = item.get("doi", "")
                paper = BiorxivPaper(
                    doi=doi,
                    title=title,
                    authors=item.get("authors", ""),
                    abstract=abstract,
                    date=item.get("date", ""),
                    category=item.get("category", ""),
                    biorxiv_url=f"https://www.biorxiv.org/content/{doi}",
                    pdf_url=f"https://www.biorxiv.org/content/{doi}.full.pdf",
                    version=item.get("version", "1")
                )
                papers.append(paper)
        
        return papers
    
    async def get_paper_details(self, doi: str) -> ToolResult:
        """Get detailed information about a specific paper.
        
        Args:
            doi: The paper's DOI
            
        Returns:
            ToolResult with paper details
        """
        try:
            # Clean DOI
            doi = doi.replace("https://doi.org/", "").strip()
            
            url = f"{BIORXIV_API_URL}/details/biorxiv/{doi}"
            
            response = await self._request_with_retry("GET", url)
            data = response.json()
            
            collection = data.get("collection", [])
            if not collection:
                return self._error_result(
                    error=f"Paper not found: {doi}",
                    doi=doi
                )
            
            # Get the latest version
            item = collection[-1]
            
            paper = BiorxivPaper(
                doi=item.get("doi", doi),
                title=item.get("title", ""),
                authors=item.get("authors", ""),
                abstract=item.get("abstract", ""),
                date=item.get("date", ""),
                category=item.get("category", ""),
                biorxiv_url=f"https://www.biorxiv.org/content/{doi}",
                pdf_url=f"https://www.biorxiv.org/content/{doi}.full.pdf",
                version=item.get("version", "1")
            )
            
            return self._success_result(
                data=paper.to_dict(),
                doi=doi
            )
            
        except Exception as e:
            logger.error(f"Failed to get paper details: {e}")
            return self._error_result(
                error=str(e),
                doi=doi
            )
    
    async def search_by_category(
        self,
        category: str,
        max_results: int = 10,
        days_back: int = 30
    ) -> ToolResult:
        """Search bioRxiv papers by category.
        
        Categories include: bioinformatics, biochemistry, cell-biology,
        genomics, molecular-biology, neuroscience, etc.
        
        Args:
            category: bioRxiv category name
            max_results: Maximum results
            days_back: Days to look back
            
        Returns:
            ToolResult with papers in category
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            url = f"{BIORXIV_API_URL}/details/biorxiv/{start_str}/{end_str}/0/500"
            
            response = await self._request_with_retry("GET", url)
            data = response.json()
            
            papers = []
            for item in data.get("collection", []):
                if len(papers) >= max_results:
                    break
                    
                if item.get("category", "").lower() == category.lower():
                    doi = item.get("doi", "")
                    paper = BiorxivPaper(
                        doi=doi,
                        title=item.get("title", ""),
                        authors=item.get("authors", ""),
                        abstract=item.get("abstract", ""),
                        date=item.get("date", ""),
                        category=item.get("category", ""),
                        biorxiv_url=f"https://www.biorxiv.org/content/{doi}",
                        pdf_url=f"https://www.biorxiv.org/content/{doi}.full.pdf",
                        version=item.get("version", "1")
                    )
                    papers.append(paper)
            
            return self._success_result(
                data=[p.to_dict() for p in papers],
                category=category,
                total_results=len(papers)
            )
            
        except Exception as e:
            logger.error(f"bioRxiv category search failed: {e}")
            return self._error_result(
                error=str(e),
                category=category
            )
