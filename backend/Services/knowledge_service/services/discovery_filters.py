"""Discovery service filtering and ranking operations"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def filter_and_rank(resources: List[Dict], min_relevance: float, top_k: int) -> List[Dict]:
    """Filter by relevance and rank by score"""
    min_score = min_relevance * 100
    filtered = [r for r in resources if r["relevance_score"] >= min_score]
    ranked = sorted(filtered, key=lambda x: x["relevance_score"], reverse=True)
    return ranked[:top_k]


def deduplicate_results(resources: List[Dict]) -> List[Dict]:
    """Remove duplicate resources by external_id"""
    seen = set()
    unique = []
    for r in resources:
        rid = r.get("external_id")
        if rid and rid not in seen:
            seen.add(rid)
            unique.append(r)
    return unique
