"""
Path Result Data Structure
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import KGEdge, KGNode


@dataclass
class PathResult:
    """Result of a path finding operation."""
    source: str
    target: str
    path: list[str]
    edges: list["KGEdge"]
    nodes: list["KGNode"]
    total_strength: float
    path_length: int
    path_string: str
    rationale: list[str]

    @property
    def average_strength(self) -> float:
        return self.total_strength ** (1 / max(len(self.edges), 1))
