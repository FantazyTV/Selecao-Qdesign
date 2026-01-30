"""
Path Finder - Main interface for finding paths in the knowledge graph.
"""

import logging
from typing import Optional

from .index import KnowledgeGraphIndex
from .models import KGNode, KGEdge
from .path_result import PathResult
from .path_strategies import (
    ShortestPathStrategy,
    HighConfidenceStrategy,
    RandomWaypointStrategy,
    DiversePathStrategy,
)

logger = logging.getLogger(__name__)


class PathFinder:
    """SciAgents-inspired path finder with multiple strategies."""

    def __init__(self, index: KnowledgeGraphIndex, randomness_factor: float = 0.2):
        self.index = index
        self.randomness_factor = randomness_factor
        self._shortest = ShortestPathStrategy(index)
        self._high_conf = HighConfidenceStrategy(index)
        self._random = RandomWaypointStrategy(index, self._shortest)
        self._diverse = DiversePathStrategy(index)

    def find_path(self, source_id: str, target_id: str, strategy: str = "random",
                  max_length: int = 10, num_waypoints: int = 2) -> Optional[PathResult]:
        if not self.index.get_node(source_id) or not self.index.get_node(target_id):
            return None
        strategies = {
            "shortest": lambda: self._shortest.find(source_id, target_id, max_length),
            "random": lambda: self._random.find(source_id, target_id, max_length, num_waypoints),
            "high_confidence": lambda: self._high_conf.find(source_id, target_id, max_length),
            "diverse": lambda: self._diverse.find(source_id, target_id, max_length),
        }
        path = strategies.get(strategy, strategies["shortest"])()
        return self._build_result(path, source_id, target_id, strategy) if path else None

    def find_all_paths(self, source_id: str, target_id: str,
                       max_length: int = 6, max_paths: int = 5) -> list[PathResult]:
        paths, seen = [], set()
        for strat, kw in [("shortest", {}), ("high_confidence", {}),
                          ("random", {"num_waypoints": 1}), ("diverse", {})]:
            if len(paths) >= max_paths:
                break
            r = self.find_path(source_id, target_id, strategy=strat, max_length=max_length, **kw)
            if r and tuple(r.path) not in seen:
                seen.add(tuple(r.path))
                paths.append(r)
        return sorted(paths, key=lambda p: p.total_strength, reverse=True)

    def _build_result(self, path: list[str], source: str, target: str, strategy: str) -> PathResult:
        nodes = [n for nid in path if (n := self.index.get_node(nid))]
        edges = self.index.get_path_edges(path)
        total = 1.0
        for e in edges:
            total *= max(e.strength, 0.01)
        parts = []
        for i, nid in enumerate(path):
            n = self.index.get_node(nid)
            parts.append(n.label if n else nid)
            if i < len(edges):
                parts.append(f"--[{edges[i].label}:{edges[i].strength:.2f}]-->")
        return PathResult(
            source=source, target=target, path=path, edges=edges, nodes=nodes,
            total_strength=total, path_length=len(path), path_string=" ".join(parts),
            rationale=self._rationale(nodes, edges, strategy),
        )

    def _rationale(self, nodes: list[KGNode], edges: list[KGEdge], strategy: str) -> list[str]:
        types = set(n.type for n in nodes)
        r = [f"Path covers {len(types)} concept types: {', '.join(types)}"]
        if edges:
            avg = sum(e.strength for e in edges) / len(edges)
            hi = sum(1 for e in edges if e.strength >= 0.9)
            r.append(f"Average edge confidence: {avg:.2f} ({hi}/{len(edges)} high-confidence)")
        feats = set()
        for n in nodes:
            feats.update(n.biological_features)
        if feats:
            r.append(f"Biological features: {', '.join(list(feats)[:5])}")
        notes = {"shortest": "Minimal path length", "random": "SciAgents waypoint diversity",
                 "high_confidence": "High-confidence edges", "diverse": "Node type diversity"}
        r.append(notes.get(strategy, strategy))
        return r
