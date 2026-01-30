"""
Co-Scientist Tools Package

Provides web search and research tools for agents to gather external knowledge.
"""

from .base_tool import BaseTool, ToolResult, RateLimiter
from .arxiv_tool import ArxivSearchTool
from .biorxiv_tool import BiorxivSearchTool
from .semantic_scholar_tool import SemanticScholarTool
from .tool_registry import ToolRegistry, get_tool_registry

__all__ = [
    # Base
    "BaseTool",
    "ToolResult",
    "RateLimiter",
    # Tools
    "ArxivSearchTool",
    "BiorxivSearchTool",
    "SemanticScholarTool",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
]
