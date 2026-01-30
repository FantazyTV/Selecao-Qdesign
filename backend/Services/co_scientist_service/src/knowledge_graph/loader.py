"""
Knowledge Graph Loader - Loads and validates KG JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import KGNode, KGEdge, KnowledgeGraph

logger = logging.getLogger(__name__)


class KnowledgeGraphLoader:
    """Loads and validates knowledge graph JSON files."""

    REQUIRED_NODE_FIELDS = {"id", "type", "label"}
    REQUIRED_EDGE_FIELDS = {"id", "source", "target", "label"}

    def __init__(self, file_path: str | Path | None = None):
        self._cached_graph: Optional[KnowledgeGraph] = None
        self._cache_path: Optional[str] = None
        self._default_path: Optional[str] = str(file_path) if file_path else None

    def load(self, file_path: str | Path | None = None) -> KnowledgeGraph:
        """Load knowledge graph from JSON file."""
        path = file_path or self._default_path
        if not path:
            raise ValueError("No file path provided")

        file_path = Path(path)
        if self._cache_path == str(file_path) and self._cached_graph:
            return self._cached_graph

        if not file_path.exists():
            raise FileNotFoundError(f"KG file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        kg = self._parse_graph(data)
        self._cached_graph = kg
        self._cache_path = str(file_path)
        logger.info(f"Loaded KG '{kg.name}': {kg.node_count} nodes, {kg.edge_count} edges")
        return kg

    def load_from_dict(self, data: dict) -> KnowledgeGraph:
        """Load knowledge graph from dictionary."""
        return self._parse_graph(data)

    def _parse_graph(self, data: dict) -> KnowledgeGraph:
        """Parse and validate the knowledge graph data."""
        kg_data = data.get("knowledgeGraph", {})
        nodes = [self._parse_node(n) for n in kg_data.get("nodes", []) 
                 if self._validate(n, self.REQUIRED_NODE_FIELDS)]
        edges = self._dedupe_edges([
            self._parse_edge(e) for e in kg_data.get("edges", [])
            if self._validate(e, self.REQUIRED_EDGE_FIELDS)
        ])
        return KnowledgeGraph(
            name=data.get("name", "Unknown"),
            main_objective=data.get("mainObjective", ""),
            secondary_objectives=data.get("secondaryObjectives", []),
            description=data.get("description", ""),
            nodes=nodes, edges=edges,
            groups=kg_data.get("groups", []),
            data_pool=data.get("dataPool", []),
            constraints=data.get("constraints", []),
            notes=data.get("notes", []),
            node_count=len(nodes), edge_count=len(edges),
            node_types=self._count_types(nodes, "type"),
            edge_types=self._count_types(edges, "correlation_type"),
        )

    def _validate(self, item: dict, required: set) -> bool:
        return required <= set(item.keys())

    def _dedupe_edges(self, edges: list[KGEdge]) -> list[KGEdge]:
        seen, unique = set(), []
        for e in edges:
            if e.id not in seen:
                seen.add(e.id)
                unique.append(e)
        return unique

    def _count_types(self, items: list, attr: str) -> dict:
        counts = {}
        for item in items:
            t = getattr(item, attr)
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _parse_node(self, data: dict) -> KGNode:
        return KGNode(
            id=data["id"], type=data["type"], label=data["label"],
            description=data.get("description"), content=data.get("content"),
            file_url=data.get("fileUrl"), trust_level=data.get("trustLevel", "high"),
            group_id=data.get("groupId"), metadata=data.get("metadata", {}),
            position=data.get("position", {}), notes=data.get("notes", []),
        )

    def _parse_edge(self, data: dict) -> KGEdge:
        return KGEdge(
            id=data["id"], source=data["source"], target=data["target"],
            label=data["label"], correlation_type=data.get("correlationType", "unknown"),
            strength=float(data.get("strength", data.get("confidence", 0.0))),
            explanation=data.get("explanation"), metadata=data.get("metadata", {}),
        )
