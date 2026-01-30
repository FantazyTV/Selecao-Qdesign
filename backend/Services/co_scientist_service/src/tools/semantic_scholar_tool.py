"""
Semantic Scholar Search Tool

Searches Semantic Scholar for academic papers and citation data.
API Documentation: https://api.semanticscholar.org/
"""

import logging
from dataclasses import dataclass
from typing import Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Semantic Scholar API base URL
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"


@dataclass
class SemanticScholarPaper:
    """Represents a Semantic Scholar paper."""
    paper_id: str
    title: str
    authors: list[str]
    abstract: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    citation_count: int
    influential_citation_count: int
    url: str
    open_access_pdf: Optional[str]
    fields_of_study: list[str]
    
    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "influential_citation_count": self.influential_citation_count,
            "url": self.url,
            "open_access_pdf": self.open_access_pdf,
            "fields_of_study": self.fields_of_study
        }
    
    def to_citation(self) -> str:
        """Generate a citation string."""
        author_str = self.authors[0] if self.authors else "Unknown"
        if len(self.authors) > 1:
            author_str += " et al."
        year = self.year or "n.d."
        return f"{author_str}. \"{self.title}\" ({year}). {self.url}"


@dataclass
class NoveltyAssessment:
    """Assessment of hypothesis novelty against literature."""
    novelty_score: int  # 1-10
    feasibility_score: int  # 1-10
    similar_papers: list[dict]
    gaps_identified: list[str]
    recommendations: list[str]
    summary: str
    
    def to_dict(self) -> dict:
        return {
            "novelty_score": self.novelty_score,
            "feasibility_score": self.feasibility_score,
            "similar_papers": self.similar_papers,
            "gaps_identified": self.gaps_identified,
            "recommendations": self.recommendations,
            "summary": self.summary
        }


class SemanticScholarTool(BaseTool):
    """Tool for searching Semantic Scholar and assessing novelty.
    
    Rate limit: 100 requests per 5 minutes for unauthenticated.
    We use a conservative 0.3 req/sec.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            requests_per_second=0.3,
            burst_size=5,
            max_retries=3,
            timeout=30.0
        )
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "semantic_scholar"
    
    @property
    def description(self) -> str:
        return "Search Semantic Scholar for academic papers and assess novelty"
    
    def _get_headers(self) -> dict:
        """Get request headers, including API key if available."""
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        year_range: Optional[tuple[int, int]] = None,
        fields_of_study: Optional[list[str]] = None,
        open_access_only: bool = False
    ) -> ToolResult:
        """Search Semantic Scholar for papers.
        
        Args:
            query: Search query
            max_results: Maximum results (max 100)
            year_range: Optional (start_year, end_year) tuple
            fields_of_study: Filter by fields (e.g., ["Biology", "Chemistry"])
            open_access_only: Only return open access papers
            
        Returns:
            ToolResult with papers
        """
        try:
            # Build query parameters
            fields = "paperId,title,authors,abstract,year,venue,citationCount,influentialCitationCount,url,openAccessPdf,fieldsOfStudy"
            
            params = {
                "query": query,
                "limit": min(max_results, 100),
                "fields": fields
            }
            
            if year_range:
                params["year"] = f"{year_range[0]}-{year_range[1]}"
            
            if fields_of_study:
                params["fieldsOfStudy"] = ",".join(fields_of_study)
            
            if open_access_only:
                params["openAccessPdf"] = ""
            
            # Build URL with query params
            url = f"{SEMANTIC_SCHOLAR_API}/paper/search"
            
            logger.info(f"Searching Semantic Scholar: {query[:50]}...")
            
            response = await self._request_with_retry(
                "GET", url, 
                params=params,
                headers=self._get_headers()
            )
            data = response.json()
            
            papers = self._parse_papers(data.get("data", []))
            
            logger.info(f"Found {len(papers)} papers on Semantic Scholar")
            
            return self._success_result(
                data=[p.to_dict() for p in papers],
                query=query,
                total_results=data.get("total", len(papers)),
                offset=data.get("offset", 0)
            )
            
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return self._error_result(
                error=str(e),
                query=query
            )
    
    def _parse_papers(self, data: list[dict]) -> list[SemanticScholarPaper]:
        """Parse API response into paper objects."""
        papers = []
        
        for item in data:
            authors = []
            for author in item.get("authors", []):
                name = author.get("name", "")
                if name:
                    authors.append(name)
            
            fields = [f.get("category", "") for f in item.get("fieldsOfStudy", []) if f]
            
            open_access_pdf = None
            if item.get("openAccessPdf"):
                open_access_pdf = item["openAccessPdf"].get("url")
            
            paper = SemanticScholarPaper(
                paper_id=item.get("paperId", ""),
                title=item.get("title", ""),
                authors=authors,
                abstract=item.get("abstract"),
                year=item.get("year"),
                venue=item.get("venue"),
                citation_count=item.get("citationCount", 0),
                influential_citation_count=item.get("influentialCitationCount", 0),
                url=item.get("url", f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"),
                open_access_pdf=open_access_pdf,
                fields_of_study=fields
            )
            papers.append(paper)
        
        return papers
    
    async def assess_novelty(
        self,
        hypothesis: str,
        keywords: list[str],
        max_papers_per_search: int = 10
    ) -> ToolResult:
        """Assess the novelty of a hypothesis against existing literature.
        
        This mimics the SciAgents approach of searching multiple keyword
        combinations and analyzing overlap with existing research.
        
        Args:
            hypothesis: The hypothesis text to assess
            keywords: Key terms from the hypothesis
            max_papers_per_search: Papers to retrieve per search
            
        Returns:
            ToolResult with NoveltyAssessment
        """
        try:
            all_papers = []
            seen_ids = set()
            
            # Search with different keyword combinations
            search_queries = [
                " ".join(keywords),  # All keywords
                " ".join(keywords[:3]) if len(keywords) >= 3 else keywords[0],  # First 3
                " ".join(keywords[-3:]) if len(keywords) >= 3 else keywords[-1],  # Last 3
            ]
            
            for query in search_queries:
                result = await self.search(query, max_results=max_papers_per_search)
                if result.success:
                    for paper in result.data:
                        if paper["paper_id"] not in seen_ids:
                            seen_ids.add(paper["paper_id"])
                            all_papers.append(paper)
            
            # Analyze papers for similarity
            similar_papers = []
            for paper in all_papers:
                # Simple keyword overlap scoring
                paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                keyword_matches = sum(1 for kw in keywords if kw.lower() in paper_text)
                
                if keyword_matches >= len(keywords) * 0.3:  # 30% keyword overlap
                    similar_papers.append({
                        "title": paper["title"],
                        "year": paper["year"],
                        "citations": paper["citation_count"],
                        "url": paper["url"],
                        "relevance": f"{keyword_matches}/{len(keywords)} keywords matched"
                    })
            
            # Sort by citations and take top matches
            similar_papers.sort(key=lambda x: x.get("citations", 0), reverse=True)
            similar_papers = similar_papers[:10]
            
            # Calculate novelty score
            novelty_score = self._calculate_novelty_score(similar_papers, keywords)
            feasibility_score = self._calculate_feasibility_score(similar_papers)
            
            # Identify gaps
            gaps = self._identify_gaps(hypothesis, similar_papers, keywords)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(similar_papers, novelty_score)
            
            assessment = NoveltyAssessment(
                novelty_score=novelty_score,
                feasibility_score=feasibility_score,
                similar_papers=similar_papers,
                gaps_identified=gaps,
                recommendations=recommendations,
                summary=self._generate_summary(novelty_score, feasibility_score, len(similar_papers))
            )
            
            logger.info(f"Novelty assessment complete: {novelty_score}/10")
            
            return self._success_result(
                data=assessment.to_dict(),
                papers_analyzed=len(all_papers),
                similar_found=len(similar_papers)
            )
            
        except Exception as e:
            logger.error(f"Novelty assessment failed: {e}")
            return self._error_result(
                error=str(e),
                hypothesis=hypothesis[:100]
            )
    
    def _calculate_novelty_score(
        self,
        similar_papers: list[dict],
        keywords: list[str]
    ) -> int:
        """Calculate novelty score based on similar papers.
        
        Higher score = more novel (fewer/less relevant similar papers).
        """
        if not similar_papers:
            return 9  # Very novel - nothing similar found
        
        # Factor 1: Number of similar papers (fewer = more novel)
        count_score = max(1, 10 - len(similar_papers))
        
        # Factor 2: Citation impact of similar papers
        max_citations = max(p.get("citations", 0) for p in similar_papers) if similar_papers else 0
        if max_citations > 1000:
            citation_score = 3  # Well-established field
        elif max_citations > 100:
            citation_score = 5
        else:
            citation_score = 7  # Emerging area
        
        # Factor 3: Recency (newer similar papers = less novel)
        recent_papers = sum(1 for p in similar_papers if p.get("year", 0) >= 2023)
        recency_score = max(1, 8 - recent_papers)
        
        # Weighted average
        novelty = int((count_score * 0.4 + citation_score * 0.3 + recency_score * 0.3))
        return max(1, min(10, novelty))
    
    def _calculate_feasibility_score(self, similar_papers: list[dict]) -> int:
        """Calculate feasibility based on similar work existence.
        
        Some similar work actually increases feasibility (proven approaches).
        """
        if not similar_papers:
            return 5  # Unknown - no similar work to reference
        
        # Factor 1: Existence of methodological precedents
        if len(similar_papers) >= 5:
            method_score = 8  # Good precedent
        elif len(similar_papers) >= 2:
            method_score = 6
        else:
            method_score = 4  # Limited precedent
        
        # Factor 2: High-citation papers suggest proven approaches
        high_citation = sum(1 for p in similar_papers if p.get("citations", 0) > 50)
        if high_citation >= 3:
            citation_score = 8
        elif high_citation >= 1:
            citation_score = 6
        else:
            citation_score = 4
        
        feasibility = int((method_score * 0.5 + citation_score * 0.5))
        return max(1, min(10, feasibility))
    
    def _identify_gaps(
        self,
        hypothesis: str,
        similar_papers: list[dict],
        keywords: list[str]
    ) -> list[str]:
        """Identify research gaps based on analysis."""
        gaps = []
        
        if not similar_papers:
            gaps.append("No directly related prior work found - this may be a truly novel research direction")
        else:
            # Check for recent work
            recent = [p for p in similar_papers if p.get("year", 0) >= 2023]
            if not recent:
                gaps.append("No recent work (2023+) on this topic - may need updating with latest findings")
            
            # Check citation distribution
            low_citation = [p for p in similar_papers if p.get("citations", 0) < 10]
            if len(low_citation) == len(similar_papers):
                gaps.append("All similar papers have low citations - emerging/underexplored area")
        
        # Generic gaps based on keyword coverage
        if len(keywords) > 3:
            gaps.append(f"Hypothesis combines {len(keywords)} concepts - interdisciplinary potential")
        
        return gaps if gaps else ["No significant gaps identified"]
    
    def _generate_recommendations(
        self,
        similar_papers: list[dict],
        novelty_score: int
    ) -> list[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if novelty_score >= 8:
            recommendations.append("High novelty - consider pilot studies to validate core assumptions")
            recommendations.append("Document methodology carefully as this may establish new approaches")
        elif novelty_score >= 5:
            recommendations.append("Moderate novelty - clearly differentiate from existing work")
            recommendations.append("Review similar papers for methodological insights")
        else:
            recommendations.append("Lower novelty - focus on unique angle or improved methodology")
            recommendations.append("Consider how to extend or challenge existing findings")
        
        if similar_papers:
            top_paper = similar_papers[0]
            recommendations.append(f"Key reference to engage: {top_paper['title'][:50]}...")
        
        return recommendations
    
    def _generate_summary(
        self,
        novelty_score: int,
        feasibility_score: int,
        similar_count: int
    ) -> str:
        """Generate overall summary."""
        novelty_desc = "highly novel" if novelty_score >= 8 else "moderately novel" if novelty_score >= 5 else "incremental"
        feasibility_desc = "highly feasible" if feasibility_score >= 8 else "feasible" if feasibility_score >= 5 else "challenging"
        
        return (
            f"This hypothesis is {novelty_desc} (score: {novelty_score}/10) and "
            f"{feasibility_desc} (score: {feasibility_score}/10). "
            f"Found {similar_count} related papers in the literature."
        )
    
    async def get_paper_by_id(self, paper_id: str) -> ToolResult:
        """Get detailed information about a specific paper.
        
        Args:
            paper_id: Semantic Scholar paper ID, DOI, or arXiv ID
            
        Returns:
            ToolResult with paper details
        """
        try:
            fields = "paperId,title,authors,abstract,year,venue,citationCount,influentialCitationCount,url,openAccessPdf,fieldsOfStudy,references,citations"
            
            url = f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}"
            
            response = await self._request_with_retry(
                "GET", url,
                params={"fields": fields},
                headers=self._get_headers()
            )
            data = response.json()
            
            # Parse single paper
            papers = self._parse_papers([data])
            if papers:
                return self._success_result(
                    data=papers[0].to_dict(),
                    paper_id=paper_id
                )
            
            return self._error_result(
                error="Paper not found",
                paper_id=paper_id
            )
            
        except Exception as e:
            logger.error(f"Failed to get paper: {e}")
            return self._error_result(
                error=str(e),
                paper_id=paper_id
            )
