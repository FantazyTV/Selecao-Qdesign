"""
Subgraph Extractor - Extracts focused subgraphs for reasoning.
"""

import logging
from typing import Optional

from .index import KnowledgeGraphIndex
from .models import KGNode, KGEdge
from .pathfinding import PathFinder
from .reasoning_subgraph import ReasoningSubgraph

logger = logging.getLogger(__name__)


class SubgraphExtractor:
    """Extracts reasoning subgraphs from the knowledge graph."""

    def __init__(self, index: KnowledgeGraphIndex):
        self.index = index
        self.path_finder = PathFinder(index)

    def extract_for_concepts(self, concept_a: str, concept_b: str, strategy: str = "random",
                             context_hops: int = 1, include_hubs: bool = True,
                             max_context_nodes: int = 20) -> Optional[ReasoningSubgraph]:
        node_a, node_b = self._resolve(concept_a), self._resolve(concept_b)
        if not node_a or not node_b:
            return None
        path_result = self.path_finder.find_path(node_a.id, node_b.id, strategy=strategy)
        if not path_result:
            return None
        ctx_nodes, ctx_edges = self._expand_context(path_result.path, context_hops, max_context_nodes)
        hubs = self._get_hubs(path_result.path, ctx_nodes) if include_hubs else []
        all_ids = set(path_result.path) | {n.id for n in ctx_nodes} | {n.id for n in hubs}
        all_nodes = [n for nid in all_ids if (n := self.index.get_node(nid))]
        all_edges = list(path_result.edges) + [e for e in ctx_edges if e not in path_result.edges]
        types = set(n.type for n in all_nodes)
        feats = set()
        for n in all_nodes:
            feats.update(n.biological_features)
        return ReasoningSubgraph(path_result=path_result, context_nodes=ctx_nodes,
                                 context_edges=ctx_edges, hub_nodes=hubs, all_nodes=all_nodes,
                                 all_edges=all_edges, node_types_present=types,
                                 biological_features=feats, total_nodes=len(all_nodes),
                                 total_edges=len(all_edges))

    def _resolve(self, concept: str) -> Optional[KGNode]:
        if n := self.index.get_node(concept):
            return n
        if n := self.index.find_node_by_label(concept, fuzzy=True):
            return n
        for key in ["pdb_id", "uniprot_id"]:
            if nodes := self.index.find_nodes_by_metadata(key, concept):
                return nodes[0]
        return None

    def _expand_context(self, path: list[str], hops: int, max_nodes: int):
        ctx_nodes, ctx_edges, visited = [], [], set(path)
        frontier = set(path)
        for _ in range(hops):
            new_frontier = set()
            for nid in frontier:
                if len(ctx_nodes) >= max_nodes:
                    break
                for neighbor in self.index.get_neighbor_ids(nid, direction="both"):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_frontier.add(neighbor)
                        if node := self.index.get_node(neighbor):
                            ctx_nodes.append(node)
                        ctx_edges.extend(e for e in self.index.get_edges_from(nid) if e.target == neighbor)
                        ctx_edges.extend(e for e in self.index.get_edges_to(nid) if e.source == neighbor)
            frontier = new_frontier
            if len(ctx_nodes) >= max_nodes:
                break
        return ctx_nodes[:max_nodes], ctx_edges

    def _get_hubs(self, path: list[str], ctx: list[KGNode], max_hubs: int = 3) -> list[KGNode]:
        hubs, path_set, ctx_ids = [], set(path), {n.id for n in ctx}
        for hub_id in self.index.hub_nodes:
            if hub_id in path_set or hub_id in ctx_ids:
                continue
            if set(self.index.get_neighbor_ids(hub_id)) & (path_set | ctx_ids):
                if hub := self.index.get_node(hub_id):
                    hubs.append(hub)
            if len(hubs) >= max_hubs:
                break
        return hubs
