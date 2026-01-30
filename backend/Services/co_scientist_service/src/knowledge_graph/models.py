"""
Knowledge Graph Data Models

Dataclasses for nodes, edges, and the knowledge graph structure.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KGNode:
    """Represents a node in the knowledge graph."""
    id: str
    type: str
    label: str
    description: Optional[str] = None
    content: Optional[str] = None
    file_url: Optional[str] = None
    trust_level: str = "high"
    group_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    position: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    @property
    def biological_features(self) -> list[str]:
        return self.metadata.get("biological_features", [])

    @property
    def pdb_id(self) -> Optional[str]:
        return self.metadata.get("pdb_id")

    @property
    def sequence(self) -> Optional[str]:
        return self.metadata.get("sequence") or self.content

    @property
    def uniprot_id(self) -> Optional[str]:
        return self.metadata.get("uniprot_id")


@dataclass
class KGEdge:
    """Represents an edge (relationship) in the knowledge graph."""
    id: str
    source: str
    target: str
    label: str
    correlation_type: str
    strength: float
    explanation: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def provenance(self) -> dict:
        return self.metadata.get("provenance", {})

    @property
    def is_high_confidence(self) -> bool:
        return self.strength >= 0.9


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph with project context."""
    name: str
    main_objective: str
    secondary_objectives: list[str]
    description: str
    nodes: list[KGNode]
    edges: list[KGEdge]
    groups: list[dict]
    data_pool: list[dict]
    constraints: list[dict]
    notes: list[str]
    node_count: int = 0
    edge_count: int = 0
    node_types: dict = field(default_factory=dict)
    edge_types: dict = field(default_factory=dict)
