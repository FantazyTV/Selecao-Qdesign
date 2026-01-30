"""
Tool Registry

Central registry for managing and accessing all research tools.
Provides a unified interface for agents to discover and use tools.
"""

import logging
from typing import Optional

from .base_tool import BaseTool, ToolResult
from .arxiv_tool import ArxivSearchTool
from .biorxiv_tool import BiorxivSearchTool
from .semantic_scholar_tool import SemanticScholarTool

logger = logging.getLogger(__name__)

# Singleton registry instance
_registry: Optional["ToolRegistry"] = None


class ToolRegistry:
    """Central registry for all research tools.
    
    Provides lazy initialization and unified access to tools.
    """
    
    def __init__(self, semantic_scholar_api_key: Optional[str] = None):
        """Initialize tool registry.
        
        Args:
            semantic_scholar_api_key: Optional API key for Semantic Scholar
        """
        self._tools: dict[str, BaseTool] = {}
        self._semantic_scholar_api_key = semantic_scholar_api_key
        self._initialized = False
    
    def _initialize_tools(self):
        """Lazy initialization of tools."""
        if self._initialized:
            return
        
        self._tools = {
            "arxiv": ArxivSearchTool(),
            "biorxiv": BiorxivSearchTool(),
            "semantic_scholar": SemanticScholarTool(api_key=self._semantic_scholar_api_key),
        }
        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name (arxiv, biorxiv, semantic_scholar)
            
        Returns:
            Tool instance or None if not found
        """
        self._initialize_tools()
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict]:
        """List all available tools with their descriptions.
        
        Returns:
            List of tool info dictionaries
        """
        self._initialize_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self._tools.values()
        ]
    
    async def search_all(self, query: str, max_results_per_source: int = 3) -> dict[str, ToolResult]:
        """Search all sources for a query.
        
        Args:
            query: Search query
            max_results_per_source: Max results from each source
            
        Returns:
            Dictionary of tool_name -> ToolResult
        """
        self._initialize_tools()
        results = {}
        
        for name, tool in self._tools.items():
            try:
                result = await tool.search(query, max_results=max_results_per_source)
                results[name] = result
            except Exception as e:
                logger.error(f"Error searching {name}: {e}")
                results[name] = tool._error_result(str(e))
        
        return results
    
    async def close_all(self):
        """Close all tool HTTP clients."""
        for tool in self._tools.values():
            await tool.close()
    
    def get_arxiv(self) -> ArxivSearchTool:
        """Get ArXiv search tool."""
        self._initialize_tools()
        return self._tools["arxiv"]
    
    def get_biorxiv(self) -> BiorxivSearchTool:
        """Get bioRxiv search tool."""
        self._initialize_tools()
        return self._tools["biorxiv"]
    
    def get_semantic_scholar(self) -> SemanticScholarTool:
        """Get Semantic Scholar tool."""
        self._initialize_tools()
        return self._tools["semantic_scholar"]


def get_tool_registry(semantic_scholar_api_key: Optional[str] = None) -> ToolRegistry:
    """Get or create the global tool registry.
    
    Args:
        semantic_scholar_api_key: Optional API key for Semantic Scholar
        
    Returns:
        ToolRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry(semantic_scholar_api_key)
    return _registry


async def search_literature(
    query: str,
    sources: Optional[list[str]] = None,
    max_results: int = 5
) -> dict:
    """Convenience function to search literature across sources.
    
    Args:
        query: Search query
        sources: List of sources to search (default: all)
        max_results: Max results per source
        
    Returns:
        Combined search results
    """
    registry = get_tool_registry()
    
    if sources is None:
        sources = ["arxiv", "biorxiv", "semantic_scholar"]
    
    results = {}
    all_papers = []
    
    for source in sources:
        tool = registry.get_tool(source)
        if tool:
            result = await tool.search(query, max_results=max_results)
            results[source] = result.to_dict()
            if result.success:
                for paper in result.data:
                    paper["source"] = source
                    all_papers.append(paper)
    
    return {
        "query": query,
        "sources_searched": sources,
        "papers": all_papers,
        "total_found": len(all_papers),
        "by_source": results
    }
