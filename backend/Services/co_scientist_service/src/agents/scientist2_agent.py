"""
Scientist2 Agent (Expander)

Takes the initial hypothesis from Scientist1 and expands it with:
- Quantitative details (chemical formulas, numerical values)
- Specific simulation/modeling approaches
- Experimental protocols and methods
- Protein sequences and processing conditions
- References from literature search

Inspired by the SciAgents Scientist_2 role which adds scientific depth.
"""

import json
import logging
from typing import AsyncIterator, Optional

from .base_agent import BaseAgent, AgentResult
from ..tools import get_tool_registry, ToolResult

logger = logging.getLogger(__name__)


class Scientist2Agent(BaseAgent):
    """Scientist2 Agent - Hypothesis Expansion and Enrichment.
    
    Expands the initial hypothesis with:
    1. Quantitative scientific details
    2. Specific methodologies and protocols
    3. Literature references via web search
    4. Detailed mechanistic explanations
    """
    
    name = "scientist2"
    
    def __init__(self, enable_literature_search: bool = True):
        """Initialize Scientist2 agent.
        
        Args:
            enable_literature_search: Whether to search literature for references
        """
        self.enable_literature_search = enable_literature_search
        self._tool_registry = None
    
    @property
    def tool_registry(self):
        """Lazy-load tool registry."""
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
        return self._tool_registry
    
    async def run(self, state: dict) -> AgentResult:
        """Expand and enrich the initial hypothesis.
        
        Args:
            state: Contains:
                - hypothesis: Initial hypothesis from Scientist1
                - planner_output: Subgraph and KG metadata
                - ontologist_output: Concept definitions (optional)
                - user_query: Original research question
                
        Returns:
            AgentResult with expanded hypothesis
        """
        hypothesis = state.get("hypothesis", {})
        if not hypothesis:
            return self._result({"error": "No hypothesis provided"}, confidence=0.0)
        
        planner_output = state.get("planner_output", {})
        ontologist_output = state.get("ontologist_output", {})
        user_query = state.get("user_query", "")
        
        # Step 1: Search literature for relevant references
        literature_results = None
        if self.enable_literature_search:
            literature_results = await self._search_literature(hypothesis, user_query)
        
        # Step 2: Prepare input with all context
        scientist2_input = self._prepare_input(
            hypothesis=hypothesis,
            planner_output=planner_output,
            ontologist_output=ontologist_output,
            literature=literature_results,
            user_query=user_query
        )
        
        try:
            response = await self._ask("scientist2", scientist2_input)
            expanded = self._validate_and_enhance(response, hypothesis, literature_results)
        except Exception as e:
            logger.error(f"Hypothesis expansion failed: {e}")
            return self._result({"error": f"Expansion failed: {e}"}, confidence=0.0)
        
        confidence = self._calculate_confidence(expanded, hypothesis)
        return self._result(expanded, confidence=confidence)
    
    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        """Stream hypothesis expansion in real-time."""
        hypothesis = state.get("hypothesis", {})
        if not hypothesis:
            yield json.dumps({"error": "No hypothesis provided"})
            return
        
        # Search literature first (non-streaming part)
        literature_results = None
        if self.enable_literature_search:
            literature_results = await self._search_literature(
                hypothesis, 
                state.get("user_query", "")
            )
        
        scientist2_input = self._prepare_input(
            hypothesis=hypothesis,
            planner_output=state.get("planner_output", {}),
            ontologist_output=state.get("ontologist_output", {}),
            literature=literature_results,
            user_query=state.get("user_query", "")
        )
        
        async for chunk in self._ask_stream("scientist2", scientist2_input):
            yield chunk
    
    async def _search_literature(
        self,
        hypothesis: dict,
        user_query: str
    ) -> Optional[dict]:
        """Search literature for relevant references.
        
        Args:
            hypothesis: The initial hypothesis
            user_query: User's research question
            
        Returns:
            Literature search results or None
        """
        try:
            # Extract keywords from hypothesis
            keywords = self._extract_keywords(hypothesis, user_query)
            
            if not keywords:
                logger.warning("No keywords extracted for literature search")
                return None
            
            search_query = " ".join(keywords[:5])  # Use top 5 keywords
            logger.info(f"Searching literature: {search_query}")
            
            all_papers = []
            
            # Search arXiv
            arxiv = self.tool_registry.get_arxiv()
            arxiv_result = await arxiv.search(search_query, max_results=3)
            if arxiv_result.success:
                for paper in arxiv_result.data:
                    paper["source"] = "arxiv"
                    all_papers.append(paper)
            
            # Search Semantic Scholar
            ss = self.tool_registry.get_semantic_scholar()
            ss_result = await ss.search(search_query, max_results=3)
            if ss_result.success:
                for paper in ss_result.data:
                    paper["source"] = "semantic_scholar"
                    all_papers.append(paper)
            
            # Search bioRxiv
            biorxiv = self.tool_registry.get_biorxiv()
            biorxiv_result = await biorxiv.search(search_query, max_results=3)
            if biorxiv_result.success:
                for paper in biorxiv_result.data:
                    paper["source"] = "biorxiv"
                    all_papers.append(paper)
            
            logger.info(f"Found {len(all_papers)} papers across sources")
            
            return {
                "papers": all_papers,
                "search_query": search_query,
                "keywords_used": keywords[:5]
            }
            
        except Exception as e:
            logger.error(f"Literature search failed: {e}")
            return None
    
    def _extract_keywords(self, hypothesis: dict, user_query: str) -> list[str]:
        """Extract relevant keywords from hypothesis for literature search.
        
        Args:
            hypothesis: The hypothesis dictionary
            user_query: User's research question
            
        Returns:
            List of keywords
        """
        keywords = set()
        
        # From user query
        if user_query:
            # Simple tokenization - could be enhanced with NLP
            words = user_query.lower().split()
            keywords.update(w for w in words if len(w) > 3)
        
        # From hypothesis title
        hyp_data = hypothesis.get("hypothesis", {})
        if isinstance(hyp_data, dict):
            title = hyp_data.get("title", "")
            if title:
                keywords.update(w.lower() for w in title.split() if len(w) > 3)
        
        # From mechanisms
        mechanisms = hypothesis.get("mechanisms", {})
        if isinstance(mechanisms, dict):
            overview = mechanisms.get("overview", "")
            if overview:
                words = overview.lower().split()
                keywords.update(w for w in words if len(w) > 4)
        
        # Filter common words
        stop_words = {"that", "this", "with", "from", "have", "will", "would", "could", "should", "their", "these", "those"}
        keywords = [k for k in keywords if k not in stop_words]
        
        return list(keywords)[:10]
    
    def _prepare_input(
        self,
        hypothesis: dict,
        planner_output: dict,
        ontologist_output: dict,
        literature: Optional[dict],
        user_query: str
    ) -> dict:
        """Prepare structured input for Scientist2 prompt.
        
        Args:
            hypothesis: Initial hypothesis from Scientist1
            planner_output: Subgraph and metadata
            ontologist_output: Concept definitions
            literature: Literature search results
            user_query: Research question
            
        Returns:
            Structured input dictionary
        """
        input_data = {
            "initial_hypothesis": hypothesis,
            "user_query": user_query,
            "subgraph": planner_output.get("subgraph", {}),
            "kg_metadata": planner_output.get("kg_metadata", {})
        }
        
        # Add ontologist interpretation if available
        if ontologist_output:
            input_data["concept_definitions"] = ontologist_output.get("concept_definitions", [])
            input_data["relationship_explanations"] = ontologist_output.get("relationship_explanations", [])
        
        # Add literature references
        if literature and literature.get("papers"):
            input_data["literature_references"] = [
                {
                    "title": p.get("title", ""),
                    "authors": p.get("authors", [])[:3] if isinstance(p.get("authors"), list) else p.get("authors", ""),
                    "abstract": p.get("abstract", "")[:500] if p.get("abstract") else "",
                    "year": p.get("year") or p.get("published", "")[:4] or p.get("date", "")[:4],
                    "url": p.get("url") or p.get("arxiv_url") or p.get("biorxiv_url", ""),
                    "source": p.get("source", "unknown")
                }
                for p in literature["papers"][:8]  # Limit to 8 papers
            ]
        
        return input_data
    
    def _validate_and_enhance(
        self,
        response: dict,
        original_hypothesis: dict,
        literature: Optional[dict]
    ) -> dict:
        """Validate and enhance the expanded hypothesis.
        
        Args:
            response: LLM response
            original_hypothesis: Original hypothesis for reference
            literature: Literature search results
            
        Returns:
            Enhanced expanded hypothesis
        """
        # Ensure all expansion sections exist
        required_sections = [
            "expanded_hypothesis",
            "quantitative_details",
            "methodologies",
            "experimental_protocols",
            "simulation_approaches",
            "literature_integration"
        ]
        
        for section in required_sections:
            if section not in response:
                response[section] = {"note": "Section not generated"}
        
        # Add literature citations if available
        if literature and literature.get("papers"):
            citations = []
            for paper in literature["papers"]:
                citation = self._format_citation(paper)
                if citation:
                    citations.append(citation)
            response["citations"] = citations
        
        # Preserve original hypothesis structure
        response["original_hypothesis_summary"] = {
            "title": original_hypothesis.get("hypothesis", {}).get("title", ""),
            "statement": original_hypothesis.get("hypothesis", {}).get("statement", "")
        }
        
        # Add metadata
        response["_metadata"] = {
            "agent": "scientist2",
            "literature_papers_used": len(literature["papers"]) if literature else 0,
            "expansion_complete": True
        }
        
        return response
    
    def _format_citation(self, paper: dict) -> Optional[dict]:
        """Format a paper as a citation.
        
        Args:
            paper: Paper data from search
            
        Returns:
            Formatted citation or None
        """
        title = paper.get("title")
        if not title:
            return None
        
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            author_str = authors[0] if authors else "Unknown"
            if len(authors) > 1:
                author_str += " et al."
        else:
            author_str = str(authors).split(";")[0] if authors else "Unknown"
        
        year = paper.get("year") or paper.get("published", "")[:4] or paper.get("date", "")[:4] or "n.d."
        
        url = paper.get("url") or paper.get("arxiv_url") or paper.get("biorxiv_url", "")
        
        return {
            "author": author_str,
            "title": title,
            "year": str(year),
            "url": url,
            "source": paper.get("source", "unknown"),
            "formatted": f"{author_str}. \"{title}\" ({year}). {url}"
        }
    
    def _calculate_confidence(self, expanded: dict, original: dict) -> float:
        """Calculate confidence score for the expansion.
        
        Args:
            expanded: Expanded hypothesis
            original: Original hypothesis
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.5  # Base score
        
        # Quantitative details present
        quant = expanded.get("quantitative_details", {})
        if quant and len(str(quant)) > 100:
            score += 0.15
        
        # Methodologies defined
        methods = expanded.get("methodologies", {})
        if methods and len(str(methods)) > 100:
            score += 0.15
        
        # Literature integrated
        citations = expanded.get("citations", [])
        if citations:
            score += min(0.2, len(citations) * 0.04)
        
        return min(score, 1.0)
    
    async def expand_hypothesis(
        self,
        hypothesis: dict,
        kg_context: Optional[dict] = None,
        ontology_context: Optional[dict] = None,
        enable_literature_search: Optional[bool] = None
    ) -> AgentResult:
        """High-level interface for hypothesis expansion.
        
        Args:
            hypothesis: Initial hypothesis dictionary
            kg_context: Knowledge graph subgraph context
            ontology_context: Ontologist output for additional context
            enable_literature_search: Override instance setting
            
        Returns:
            AgentResult with expanded hypothesis
        """
        # Handle enable_literature_search override
        original_setting = self.enable_literature_search
        if enable_literature_search is not None:
            self.enable_literature_search = enable_literature_search
        
        state = {
            "hypothesis": hypothesis,
            "planner_output": {"subgraph": kg_context or {}},
            "ontologist_output": ontology_context,
            "user_query": hypothesis.get("core_hypothesis", "")
        }
        
        try:
            result = await self.run(state)
        finally:
            # Restore original setting
            self.enable_literature_search = original_setting
        
        return result
    
    def _format_hypothesis(self, hypothesis: dict) -> str:
        """Format hypothesis into string representation.
        
        Args:
            hypothesis: Hypothesis dictionary
            
        Returns:
            Formatted string
        """
        lines = []
        
        if "title" in hypothesis:
            lines.append(f"Title: {hypothesis['title']}")
        
        if "core_hypothesis" in hypothesis:
            lines.append(f"Core Hypothesis: {hypothesis['core_hypothesis']}")
        
        if "supporting_rationale" in hypothesis:
            lines.append("Supporting Rationale:")
            for r in hypothesis.get("supporting_rationale", []):
                lines.append(f"  - {r}")
        
        if "potential_applications" in hypothesis:
            lines.append(f"Applications: {', '.join(hypothesis.get('potential_applications', []))}")
        
        return "\n".join(lines)
    
    def _build_search_queries(self, hypothesis: dict) -> list[str]:
        """Build search queries from hypothesis content.
        
        Args:
            hypothesis: Hypothesis dictionary
            
        Returns:
            List of search queries
        """
        queries = []
        
        # Extract from title
        title = hypothesis.get("title", "")
        if title:
            queries.append(title)
        
        # Extract from core hypothesis
        core = hypothesis.get("core_hypothesis", "")
        if core:
            # Extract key terms (simple approach)
            queries.append(core)
        
        # Build combined query from keywords
        keywords = self._extract_keywords(hypothesis, "")
        if keywords:
            queries.append(" ".join(keywords[:3]))
        
        return queries
