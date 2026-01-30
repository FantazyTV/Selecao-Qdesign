"""
Knowledge Graph Index - Query interface for the indexed graph.
"""

from collections import defaultdict
from typing import Optional

from .models import KnowledgeGraph, KGNode, KGEdge
from .index_builder import IndexBuilder, NodeStats


class KnowledgeGraphIndex:
    """Query interface for an indexed knowledge graph."""

    def __init__(self, kg: KnowledgeGraph):
        builder = IndexBuilder(kg).build()
        self.kg = kg
        self.nodes_by_id = builder.nodes_by_id
        self.edges_by_id = builder.edges_by_id
        self.adjacency = builder.adjacency
        self.reverse_adjacency = builder.reverse_adjacency
        self.nodes_by_type = builder.nodes_by_type
        self.node_stats = builder.node_stats
        self.hub_nodes = builder.hub_nodes
        self.edge_strength_distribution = builder.edge_strength_distribution

    def get_node(self, node_id: str) -> Optional[KGNode]:
        return self.nodes_by_id.get(node_id)

    def get_neighbors(self, node_id: str, direction: str = "both") -> list[KGNode]:
        ids = self.get_neighbor_ids(node_id, direction)
        return [self.nodes_by_id[i] for i in ids if i in self.nodes_by_id]

    def get_neighbor_ids(self, node_id: str, direction: str = "both") -> list[str]:
        neighbors = set()
        if direction in ("out", "both"):
            neighbors.update(e.target for e in self.adjacency.get(node_id, []))
        if direction in ("in", "both"):
            neighbors.update(e.source for e in self.reverse_adjacency.get(node_id, []))
        return list(neighbors)

    def get_edges_between(self, source: str, target: str) -> list[KGEdge]:
        return [e for e in self.adjacency.get(source, []) if e.target == target]

    def get_edges_from(self, node_id: str) -> list[KGEdge]:
        return self.adjacency.get(node_id, [])

    def get_edges_to(self, node_id: str) -> list[KGEdge]:
        return self.reverse_adjacency.get(node_id, [])

    def get_edges_for_node(self, node_id: str) -> list[KGEdge]:
        return list(self.adjacency.get(node_id, [])) + list(self.reverse_adjacency.get(node_id, []))

    def get_nodes_by_type(self, node_type: str) -> list[KGNode]:
        return self.nodes_by_type.get(node_type, [])

    def get_all_nodes(self) -> list[KGNode]:
        return list(self.nodes_by_id.values())

    def get_hub_nodes(self, top_k: int = 10) -> list[KGNode]:
        return [self.nodes_by_id[nid] for nid in self.hub_nodes[:top_k]]

    def get_statistics(self) -> dict:
        return {
            "total_nodes": len(self.nodes_by_id),
            "total_edges": len(self.edges_by_id),
            "types": {t: len(n) for t, n in self.nodes_by_type.items()},
            "hub_count": len(self.hub_nodes),
            "avg_edge_strength": self.edge_strength_distribution,
        }

    def find_node_by_label(self, label: str, fuzzy: bool = True) -> Optional[KGNode]:
        label_lower = label.lower()
        for node in self.kg.nodes:
            if fuzzy and (label_lower in node.label.lower() or label_lower in node.id.lower()):
                return node
            elif not fuzzy and (node.label == label or node.id == label):
                return node
        return None

    def find_nodes_by_metadata(self, key: str, value: str) -> list[KGNode]:
        results, val = [], value.lower()
        for node in self.kg.nodes:
            mv = node.metadata.get(key)
            if isinstance(mv, str) and val in mv.lower():
                results.append(node)
            elif isinstance(mv, list) and any(val in str(v).lower() for v in mv):
                results.append(node)
        return results

    def get_path_edges(self, path: list[str]) -> list[KGEdge]:
        edges = []
        for i in range(len(path) - 1):
            connecting = self.get_edges_between(path[i], path[i + 1])
            if connecting:
                edges.append(max(connecting, key=lambda e: e.strength))
        return edges
