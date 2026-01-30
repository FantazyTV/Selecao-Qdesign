"""
Multi-Path Exploration - Enhanced subgraph extraction using multiple paths.

Implements the "Multiple Path Exploration" feature from README for richer hypotheses.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass, field

from .index import KnowledgeGraphIndex
from .models import KGNode, KGEdge
from .pathfinding import PathFinder
from .path_result import PathResult
from .reasoning_subgraph import ReasoningSubgraph

logger = logging.getLogger(__name__)


@dataclass
class MultiPathSubgraph:
    """Extended subgraph with multiple reasoning paths."""
    
    # Primary path (highest confidence)
    primary_path: PathResult
    
    # Alternative paths (sorted by confidence)
    alternative_paths: List[PathResult] = field(default_factory=list)
    
    # Combined subgraph data
    all_nodes: List[KGNode] = field(default_factory=list)
    all_edges: List[KGEdge] = field(default_factory=list)
    hub_nodes: List[KGNode] = field(default_factory=list)
    
    # Statistics
    total_paths: int = 1
    total_nodes: int = 0
    total_edges: int = 0
    node_types_present: set = field(default_factory=set)
    biological_features: set = field(default_factory=set)
    
    # Path diversity metrics
    path_overlap_ratio: float = 0.0
    unique_nodes_per_path: float = 0.0
    strategy_coverage: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "primary_path": {
                "source": self.primary_path.source,
                "target": self.primary_path.target,
                "node_ids": self.primary_path.path,
                "path_string": self.primary_path.path_string,
                "total_strength": self.primary_path.total_strength,
                "rationale": self.primary_path.rationale,
            },
            "alternative_paths": [
                {
                    "node_ids": p.path,
                    "path_string": p.path_string,
                    "total_strength": p.total_strength,
                    "strategy": getattr(p, 'strategy', 'unknown'),
                }
                for p in self.alternative_paths
            ],
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "biological_features": n.biological_features,
                    "is_hub": any(h.id == n.id for h in self.hub_nodes),
                    "in_primary_path": n.id in self.primary_path.path,
                }
                for n in self.all_nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "strength": e.strength,
                }
                for e in self.all_edges
            ],
            "metadata": {
                "total_paths": self.total_paths,
                "total_nodes": self.total_nodes,
                "total_edges": self.total_edges,
                "node_types": list(self.node_types_present),
                "path_overlap_ratio": self.path_overlap_ratio,
                "unique_nodes_per_path": self.unique_nodes_per_path,
                "strategies_used": self.strategy_coverage,
            },
        }
    
    def to_natural_language(self) -> str:
        """Generate natural language description of the multi-path subgraph."""
        lines = [
            "## Multi-Path Knowledge Graph Exploration",
            "",
            f"**Source**: {self.primary_path.source} → **Target**: {self.primary_path.target}",
            f"**Total Paths Explored**: {self.total_paths}",
            f"**Path Diversity**: {(1 - self.path_overlap_ratio) * 100:.1f}% unique coverage",
            "",
            "---",
            "",
            "### Primary Path (Highest Confidence)",
            f"**Path**: {self.primary_path.path_string}",
            f"**Confidence**: {self.primary_path.total_strength:.4f}",
            "",
            "**Selection Rationale**:",
        ]
        
        for r in self.primary_path.rationale:
            lines.append(f"- {r}")
        
        if self.alternative_paths:
            lines.extend([
                "",
                "### Alternative Paths",
                "",
            ])
            for i, path in enumerate(self.alternative_paths, 1):
                lines.append(
                    f"{i}. {path.path_string} "
                    f"(confidence: {path.total_strength:.4f})"
                )
        
        lines.extend([
            "",
            "---",
            "",
            "### All Concepts (Nodes)",
            "",
        ])
        
        for n in self.all_nodes:
            markers = []
            if any(h.id == n.id for h in self.hub_nodes):
                markers.append("HUB")
            if n.id in self.primary_path.path:
                markers.append("PRIMARY")
            marker_str = f" [{', '.join(markers)}]" if markers else ""
            
            lines.append(f"- **{n.label}** ({n.type}){marker_str}")
            if n.biological_features:
                lines.append(f"  - Features: {', '.join(n.biological_features[:5])}")
        
        lines.extend([
            "",
            "### Relationships (Edges)",
            "",
        ])
        
        for e in self.all_edges:
            src = next((n.label for n in self.all_nodes if n.id == e.source), e.source)
            tgt = next((n.label for n in self.all_nodes if n.id == e.target), e.target)
            lines.append(f"- {src} --[{e.label}]--> {tgt} (strength: {e.strength:.2f})")
        
        lines.extend([
            "",
            "### Statistics",
            f"- Total Nodes: {self.total_nodes}",
            f"- Total Edges: {self.total_edges}",
            f"- Node Types: {', '.join(self.node_types_present)}",
            f"- Strategies Used: {', '.join(self.strategy_coverage)}",
        ])
        
        return "\n".join(lines)


class MultiPathExtractor:
    """
    Extracts rich subgraphs using multiple path-finding strategies.
    
    Inspired by SciAgents methodology for comprehensive knowledge exploration.
    """
    
    def __init__(self, index: KnowledgeGraphIndex):
        self.index = index
        self.path_finder = PathFinder(index)
    
    def extract_multi_path(
        self,
        concept_a: str,
        concept_b: str,
        max_paths: int = 3,
        strategies: Optional[List[str]] = None,
        context_hops: int = 1,
        include_hubs: bool = True,
        max_context_nodes: int = 30,
    ) -> Optional[MultiPathSubgraph]:
        """
        Extract a rich subgraph using multiple path-finding strategies.
        
        Args:
            concept_a: Source concept ID or label
            concept_b: Target concept ID or label
            max_paths: Maximum number of paths to include
            strategies: List of strategies to use (default: all)
            context_hops: Number of hops for context expansion
            include_hubs: Whether to include hub nodes
            max_context_nodes: Maximum context nodes to include
            
        Returns:
            MultiPathSubgraph with multiple paths and combined context
        """
        # Resolve concepts
        node_a = self._resolve_concept(concept_a)
        node_b = self._resolve_concept(concept_b)
        
        if not node_a or not node_b:
            logger.warning(f"Could not resolve concepts: {concept_a}, {concept_b}")
            return None
        
        # Default strategies for comprehensive exploration
        if strategies is None:
            strategies = ["shortest", "high_confidence", "random", "diverse"]
        
        # Find all paths using different strategies
        all_paths = self.path_finder.find_all_paths(
            node_a.id, node_b.id,
            max_length=10,
            max_paths=max_paths + 2  # Get extra for filtering
        )
        
        if not all_paths:
            logger.warning(f"No paths found between {concept_a} and {concept_b}")
            return None
        
        # Sort by confidence and select top paths
        sorted_paths = sorted(all_paths, key=lambda p: p.total_strength, reverse=True)
        primary_path = sorted_paths[0]
        alternative_paths = sorted_paths[1:max_paths]
        
        # Collect all nodes and edges from all paths
        all_node_ids = set()
        all_edge_ids = set()
        strategies_used = set()
        
        for path in sorted_paths[:max_paths]:
            all_node_ids.update(path.path)
            for edge in path.edges:
                all_edge_ids.add(edge.id if edge.id else f"{edge.source}_{edge.target}")
            strategies_used.add(getattr(path, 'strategy', 'unknown'))
        
        # Expand context around the paths
        context_nodes, context_edges = self._expand_context(
            list(all_node_ids), context_hops, max_context_nodes
        )
        
        for n in context_nodes:
            all_node_ids.add(n.id)
        
        # Get hub nodes
        hub_nodes = []
        if include_hubs:
            hub_nodes = self._get_relevant_hubs(all_node_ids, max_hubs=3)
            for h in hub_nodes:
                all_node_ids.add(h.id)
        
        # Collect all node and edge objects
        all_nodes = [n for nid in all_node_ids if (n := self.index.get_node(nid))]
        all_edges = self._collect_edges(all_node_ids, sorted_paths[:max_paths], context_edges)
        
        # Calculate diversity metrics
        path_overlap_ratio = self._calculate_overlap(sorted_paths[:max_paths])
        unique_per_path = self._calculate_unique_per_path(sorted_paths[:max_paths])
        
        # Collect node types and features
        node_types = set(n.type for n in all_nodes)
        bio_features = set()
        for n in all_nodes:
            bio_features.update(n.biological_features)
        
        return MultiPathSubgraph(
            primary_path=primary_path,
            alternative_paths=alternative_paths,
            all_nodes=all_nodes,
            all_edges=all_edges,
            hub_nodes=hub_nodes,
            total_paths=len(sorted_paths[:max_paths]),
            total_nodes=len(all_nodes),
            total_edges=len(all_edges),
            node_types_present=node_types,
            biological_features=bio_features,
            path_overlap_ratio=path_overlap_ratio,
            unique_nodes_per_path=unique_per_path,
            strategy_coverage=list(strategies_used),
        )
    
    def _resolve_concept(self, concept: str) -> Optional[KGNode]:
        """Resolve a concept ID or label to a node."""
        if node := self.index.get_node(concept):
            return node
        if node := self.index.find_node_by_label(concept, fuzzy=True):
            return node
        # Try metadata keys
        for key in ["pdb_id", "uniprot_id", "gene_symbol"]:
            if nodes := self.index.find_nodes_by_metadata(key, concept):
                return nodes[0]
        return None
    
    def _expand_context(
        self,
        path_nodes: List[str],
        hops: int,
        max_nodes: int
    ) -> tuple[List[KGNode], List[KGEdge]]:
        """Expand context around path nodes."""
        context_nodes = []
        context_edges = []
        visited = set(path_nodes)
        frontier = set(path_nodes)
        
        for _ in range(hops):
            new_frontier = set()
            for nid in frontier:
                if len(context_nodes) >= max_nodes:
                    break
                for neighbor in self.index.get_neighbor_ids(nid, direction="both"):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_frontier.add(neighbor)
                        if node := self.index.get_node(neighbor):
                            context_nodes.append(node)
                        # Get connecting edges
                        for edge in self.index.get_edges_from(nid):
                            if edge.target == neighbor:
                                context_edges.append(edge)
                        for edge in self.index.get_edges_to(nid):
                            if edge.source == neighbor:
                                context_edges.append(edge)
            frontier = new_frontier
            if len(context_nodes) >= max_nodes:
                break
        
        return context_nodes[:max_nodes], context_edges
    
    def _get_relevant_hubs(
        self,
        node_ids: set,
        max_hubs: int = 3
    ) -> List[KGNode]:
        """Get hub nodes relevant to the subgraph."""
        hubs = []
        for hub_id in self.index.hub_nodes:
            if hub_id in node_ids:
                continue
            # Check if hub is connected to any node in subgraph
            hub_neighbors = set(self.index.get_neighbor_ids(hub_id, direction="both"))
            if hub_neighbors & node_ids:
                if hub := self.index.get_node(hub_id):
                    hubs.append(hub)
            if len(hubs) >= max_hubs:
                break
        return hubs
    
    def _collect_edges(
        self,
        node_ids: set,
        paths: List[PathResult],
        context_edges: List[KGEdge]
    ) -> List[KGEdge]:
        """Collect all edges between nodes in the subgraph."""
        edge_set = set()
        edges = []
        
        # Add edges from paths
        for path in paths:
            for edge in path.edges:
                edge_key = (edge.source, edge.target, edge.label)
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append(edge)
        
        # Add context edges
        for edge in context_edges:
            edge_key = (edge.source, edge.target, edge.label)
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append(edge)
        
        return edges
    
    def _calculate_overlap(self, paths: List[PathResult]) -> float:
        """Calculate the overlap ratio between paths."""
        if len(paths) <= 1:
            return 1.0
        
        # Get all unique nodes across paths
        all_nodes = set()
        for path in paths:
            all_nodes.update(path.path)
        
        # Calculate overlap (nodes appearing in multiple paths)
        node_counts = {}
        for path in paths:
            for node in path.path:
                node_counts[node] = node_counts.get(node, 0) + 1
        
        overlapping = sum(1 for count in node_counts.values() if count > 1)
        return overlapping / len(all_nodes) if all_nodes else 0.0
    
    def _calculate_unique_per_path(self, paths: List[PathResult]) -> float:
        """Calculate average unique nodes per path."""
        if not paths:
            return 0.0
        
        total_unique = 0
        seen = set()
        
        for path in paths:
            unique = sum(1 for n in path.path if n not in seen)
            total_unique += unique
            seen.update(path.path)
        
        return total_unique / len(paths)
