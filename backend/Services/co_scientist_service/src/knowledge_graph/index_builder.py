"""
Index Builder - Builds in-memory indexes for the knowledge graph.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from .models import KnowledgeGraph, KGNode, KGEdge

logger = logging.getLogger(__name__)


@dataclass
class NodeStats:
    """Statistics for a single node."""
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    avg_edge_strength: float = 0.0
    is_hub: bool = False
    connected_types: set = field(default_factory=set)


class IndexBuilder:
    """Builds the primary indexes for a knowledge graph."""

    HUB_THRESHOLD_PERCENTILE = 90

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.nodes_by_id: dict[str, KGNode] = {}
        self.edges_by_id: dict[str, KGEdge] = {}
        self.adjacency: dict[str, list[KGEdge]] = defaultdict(list)
        self.reverse_adjacency: dict[str, list[KGEdge]] = defaultdict(list)
        self.nodes_by_type: dict[str, list[KGNode]] = defaultdict(list)
        self.nodes_by_group: dict[str, list[KGNode]] = defaultdict(list)
        self.node_stats: dict[str, NodeStats] = {}
        self.hub_nodes: list[str] = []
        self.edge_strength_distribution: dict[str, float] = {}

    def build(self) -> "IndexBuilder":
        """Build all indexes."""
        self._build_node_indexes()
        self._build_edge_indexes()
        self._compute_statistics()
        logger.info(f"Built index: {len(self.nodes_by_id)} nodes, {len(self.hub_nodes)} hubs")
        return self

    def _build_node_indexes(self):
        for node in self.kg.nodes:
            self.nodes_by_id[node.id] = node
            self.nodes_by_type[node.type].append(node)
            if node.group_id:
                self.nodes_by_group[node.group_id].append(node)

    def _build_edge_indexes(self):
        for edge in self.kg.edges:
            self.edges_by_id[edge.id] = edge
            self.adjacency[edge.source].append(edge)
            self.reverse_adjacency[edge.target].append(edge)

    def _compute_statistics(self):
        degrees = []
        for node_id in self.nodes_by_id:
            stats = self._compute_node_stats(node_id)
            self.node_stats[node_id] = stats
            degrees.append((node_id, stats.total_degree))
        self._identify_hubs(degrees)
        self._compute_edge_distribution()

    def _compute_node_stats(self, node_id: str) -> NodeStats:
        out_edges = self.adjacency.get(node_id, [])
        in_edges = self.reverse_adjacency.get(node_id, [])
        all_edges = out_edges + in_edges
        connected_types = set()
        for e in out_edges:
            if t := self.nodes_by_id.get(e.target):
                connected_types.add(t.type)
        for e in in_edges:
            if s := self.nodes_by_id.get(e.source):
                connected_types.add(s.type)
        return NodeStats(
            in_degree=len(in_edges), out_degree=len(out_edges),
            total_degree=len(out_edges) + len(in_edges),
            avg_edge_strength=sum(e.strength for e in all_edges) / len(all_edges) if all_edges else 0.0,
            connected_types=connected_types,
        )

    def _identify_hubs(self, degrees: list):
        if not degrees:
            return
        degrees.sort(key=lambda x: x[1], reverse=True)
        idx = max(1, len(degrees) * (100 - self.HUB_THRESHOLD_PERCENTILE) // 100)
        threshold = degrees[idx - 1][1] if idx <= len(degrees) else 0
        for node_id, degree in degrees:
            if degree >= threshold and degree > 0:
                self.node_stats[node_id].is_hub = True
                self.hub_nodes.append(node_id)

    def _compute_edge_distribution(self):
        strength_sums = defaultdict(list)
        for edge in self.kg.edges:
            strength_sums[edge.correlation_type].append(edge.strength)
        for edge_type, strengths in strength_sums.items():
            self.edge_strength_distribution[edge_type] = sum(strengths) / len(strengths)
