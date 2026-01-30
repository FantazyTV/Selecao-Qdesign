"""
Path Strategies - Different algorithms for finding paths.
"""

import heapq
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .index import KnowledgeGraphIndex


class ShortestPathStrategy:
    """BFS shortest path."""

    def __init__(self, index: "KnowledgeGraphIndex"):
        self.index = index

    def find(self, source: str, target: str, max_length: int) -> Optional[list[str]]:
        if source == target:
            return [source]
        visited, queue = {source}, [(source, [source])]
        while queue:
            node, path = queue.pop(0)
            if len(path) > max_length:
                continue
            for neighbor in self.index.get_neighbor_ids(node, direction="out"):
                if neighbor == target:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return self._bidirectional(source, target, max_length)

    def _bidirectional(self, source: str, target: str, max_length: int) -> Optional[list[str]]:
        forward, backward = {source: [source]}, {target: [target]}
        for _ in range(max_length // 2 + 1):
            new_fwd = {}
            for node, path in forward.items():
                for n in self.index.get_neighbor_ids(node, direction="out"):
                    if n in backward:
                        return path + backward[n][::-1]
                    if n not in forward and n not in new_fwd:
                        new_fwd[n] = path + [n]
            forward.update(new_fwd)
            new_bwd = {}
            for node, path in backward.items():
                for n in self.index.get_neighbor_ids(node, direction="in"):
                    if n in forward:
                        return forward[n] + path[::-1]
                    if n not in backward and n not in new_bwd:
                        new_bwd[n] = path + [n]
            backward.update(new_bwd)
        return None


class HighConfidenceStrategy:
    """Dijkstra prioritizing high-strength edges."""

    def __init__(self, index: "KnowledgeGraphIndex"):
        self.index = index

    def find(self, source: str, target: str, max_length: int) -> Optional[list[str]]:
        if source == target:
            return [source]
        heap, visited = [(0.0, 0, source, [source])], set()
        while heap:
            neg_str, length, node, path = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            if node == target:
                return path
            if length >= max_length:
                continue
            for edge in self.index.get_edges_from(node):
                if edge.target not in visited:
                    heapq.heappush(heap, (-(-neg_str + edge.strength), length + 1, edge.target, path + [edge.target]))
        return None


class RandomWaypointStrategy:
    """SciAgents-style random path with waypoints."""

    def __init__(self, index: "KnowledgeGraphIndex", shortest: ShortestPathStrategy):
        self.index = index
        self.shortest = shortest

    def find(self, source: str, target: str, max_length: int, num_waypoints: int = 2) -> Optional[list[str]]:
        base = self.shortest.find(source, target, max_length)
        if not base or len(base) <= 3:
            return base
        path_set = set(base)
        candidates = []
        for node in base[1:-1]:
            for n in self.index.get_neighbor_ids(node, direction="both"):
                if n not in path_set:
                    candidates.append((node, n))
        if not candidates:
            return base
        random.shuffle(candidates)
        extended = list(base)
        for anchor, wp in candidates[:num_waypoints]:
            try:
                idx = extended.index(anchor)
                extended.insert(idx + 1, wp)
            except ValueError:
                pass
        return extended[:max_length]


class DiversePathStrategy:
    """Path maximizing node type diversity."""

    def __init__(self, index: "KnowledgeGraphIndex"):
        self.index = index

    def find(self, source: str, target: str, max_length: int) -> Optional[list[str]]:
        if source == target:
            return [source]
        src = self.index.get_node(source)
        if not src:
            return None
        visited, queue = {source}, [(source, [source], {src.type})]
        best_path, best_div = None, 0
        while queue:
            node, path, types = queue.pop(0)
            if node == target and len(types) > best_div:
                best_path, best_div = path, len(types)
                continue
            if len(path) >= max_length:
                continue
            neighbors = [(n, self.index.get_node(n)) for n in self.index.get_neighbor_ids(node, direction="out")]
            neighbors.sort(key=lambda x: (x[1].type in types if x[1] else True, random.random()))
            for n, nn in neighbors:
                if n not in visited:
                    visited.add(n)
                    new_types = types | ({nn.type} if nn else set())
                    queue.append((n, path + [n], new_types))
        return best_path
