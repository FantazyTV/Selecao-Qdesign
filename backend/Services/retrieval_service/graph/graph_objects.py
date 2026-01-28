from typing import Any, Dict, List, Optional, Set, Union
import json

class Node:
    def __init__(self, id: str, type: str, label: str = "", embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.type = type  # e.g., protein, paper, image, pathway
        self.label = label
        self.embedding = embedding
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

class Edge:
    def __init__(self, from_id: str, to_id: str, type: str, score: Optional[float] = None, evidence: Optional[str] = None, provenance: Optional[Dict[str, Any]] = None):
        self.from_id = from_id
        self.to_id = to_id
        self.type = type  # e.g., similarity, mentioned_in, reports, cites, experimental_support
        self.score = score
        self.evidence = evidence
        self.provenance = provenance or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "type": self.type,
            "score": self.score,
            "evidence": self.evidence,
            "provenance": self.provenance,
        }
    
    def __str__(self) -> str:
        return f"Edge({self.from_id} --[{self.type}]--> {self.to_id}, score={self.score}) \n Evidence: {self.evidence} \n Provenance: {json.dumps(self.provenance)}"

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_node(self, node: Node):
        """Add or update a node by id."""
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        """Add an edge. Does not deduplicate."""
        self.edges.append(edge)

    def merge_subgraph(self, subgraph: 'Graph'):
        """Merge another graph into this one, preserving all nodes and edges."""
        for node in subgraph.nodes.values():
            self.add_node(node)
        for edge in subgraph.edges:
            self.add_edge(edge)

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None, node_type: Optional[str] = None) -> List[Node]:
        """
        Return nodes connected to node_id, filtered by edge_type and/or node_type.
        Only outgoing edges are considered (from_id == node_id).
        """
        neighbors = []
        for edge in self.edges:
            if edge.from_id == node_id:
                if edge_type and edge.type != edge_type:
                    continue
                neighbor = self.nodes.get(edge.to_id)
                if neighbor is None:
                    continue
                if node_type and neighbor.type != node_type:
                    continue
                neighbors.append(neighbor)
        return neighbors

    def as_json(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict of the graph."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def __repr__(self):
        return f"<Graph nodes={len(self.nodes)} edges={len(self.edges)}>"