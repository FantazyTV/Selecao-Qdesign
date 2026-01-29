"""
Knowledge Graph Module - SciAgents-Inspired Implementation

This module provides:
1. KG Loading - Parse and validate the provided JSON knowledge graph
2. KG Indexing - Build efficient in-memory indexes for traversal
3. Path Finding - Heuristic pathfinding with randomization (SciAgents-style)
4. Subgraph Extraction - Extract focused reasoning subgraphs
5. Multi-Path Exploration - Rich subgraphs using multiple strategies
"""

from .models import KGNode, KGEdge, KnowledgeGraph
from .loader import KnowledgeGraphLoader
from .index_builder import IndexBuilder, NodeStats
from .index import KnowledgeGraphIndex
from .path_result import PathResult
from .path_strategies import (
    ShortestPathStrategy,
    HighConfidenceStrategy,
    RandomWaypointStrategy,
    DiversePathStrategy,
)
from .pathfinding import PathFinder
from .reasoning_subgraph import ReasoningSubgraph
from .subgraph import SubgraphExtractor
from .multi_path import MultiPathSubgraph, MultiPathExtractor

__all__ = [
    # Models
    "KGNode",
    "KGEdge",
    "KnowledgeGraph",
    # Loader
    "KnowledgeGraphLoader",
    # Index
    "IndexBuilder",
    "NodeStats",
    "KnowledgeGraphIndex",
    # Pathfinding
    "PathResult",
    "ShortestPathStrategy",
    "HighConfidenceStrategy",
    "RandomWaypointStrategy",
    "DiversePathStrategy",
    "PathFinder",
    # Subgraph
    "ReasoningSubgraph",
    "SubgraphExtractor",
    # Multi-Path
    "MultiPathSubgraph",
    "MultiPathExtractor",
]
