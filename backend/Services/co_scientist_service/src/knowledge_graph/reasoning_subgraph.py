"""
Reasoning Subgraph - Data structure for extracted subgraphs.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import KGNode, KGEdge
    from .path_result import PathResult


@dataclass
class ReasoningSubgraph:
    """A focused subgraph extracted for agent reasoning."""
    path_result: "PathResult"
    context_nodes: list["KGNode"] = field(default_factory=list)
    context_edges: list["KGEdge"] = field(default_factory=list)
    hub_nodes: list["KGNode"] = field(default_factory=list)
    all_nodes: list["KGNode"] = field(default_factory=list)
    all_edges: list["KGEdge"] = field(default_factory=list)
    node_types_present: set = field(default_factory=set)
    biological_features: set = field(default_factory=set)
    total_nodes: int = 0
    total_edges: int = 0

    def to_dict(self) -> dict:
        return {
            "path": {
                "source": self.path_result.source,
                "target": self.path_result.target,
                "node_ids": self.path_result.path,
                "path_string": self.path_result.path_string,
                "total_strength": self.path_result.total_strength,
                "rationale": self.path_result.rationale,
            },
            "nodes": [{"id": n.id, "type": n.type, "label": n.label,
                      "biological_features": n.biological_features} for n in self.all_nodes],
            "edges": [{"id": e.id, "source": e.source, "target": e.target,
                      "label": e.label, "strength": e.strength} for e in self.all_edges],
            "metadata": {"total_nodes": self.total_nodes, "total_edges": self.total_edges,
                        "node_types": list(self.node_types_present)},
        }

    def to_natural_language(self) -> str:
        lines = [f"## Knowledge Graph Subgraph",
                 f"**Path**: {self.path_result.path_string}",
                 f"**Confidence Score**: {self.path_result.total_strength:.4f}", "",
                 "### Path Selection Rationale"]
        lines.extend(f"- {r}" for r in self.path_result.rationale)
        lines.append("\n### Concepts (Nodes)")
        for n in self.all_nodes:
            hub = " [HUB]" if any(h.id == n.id for h in self.hub_nodes) else ""
            path = " *" if n.id in self.path_result.path else ""
            lines.append(f"- **{n.label}** ({n.type}){hub}{path}")
            if n.biological_features:
                lines.append(f"  - Features: {', '.join(n.biological_features)}")
            if n.pdb_id:
                lines.append(f"  - PDB: {n.pdb_id}")
        lines.append("\n### Relationships (Edges)")
        for e in self.all_edges:
            src = next((n.label for n in self.all_nodes if n.id == e.source), e.source)
            tgt = next((n.label for n in self.all_nodes if n.id == e.target), e.target)
            lines.append(f"- {src} --[{e.label}]--> {tgt} (confidence: {e.strength:.2f})")
        lines.append(f"\n### Summary\n- Nodes: {self.total_nodes}, Edges: {self.total_edges}")
        return "\n".join(lines)
