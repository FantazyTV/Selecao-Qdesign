"""
Knowledge Graph API Routes - Endpoints for KG operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from ..monitoring.metrics import REQUESTS
from ..knowledge_graph import KnowledgeGraphLoader, KnowledgeGraphIndex

router = APIRouter(prefix="/v2/knowledge-graph", tags=["knowledge-graph"])


@router.get("/load", summary="Load knowledge graph")
async def load_knowledge_graph(kg_path: str):
    """Load and analyze a knowledge graph JSON file."""
    REQUESTS.labels(endpoint="/v2/knowledge-graph/load", method="GET", status="success").inc()

    try:
        path = Path(kg_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Knowledge graph not found: {kg_path}")

        loader = KnowledgeGraphLoader(kg_path)
        kg = loader.load()
        index = KnowledgeGraphIndex(kg)

        stats = index.get_statistics()
        hub_nodes = index.get_hub_nodes(top_k=10)

        return {
            "status": "success", "kg_path": kg_path,
            "metadata": {
                "name": kg.name, "main_objective": kg.main_objective,
                "secondary_objectives": kg.secondary_objectives
            },
            "statistics": stats,
            "hub_nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in hub_nodes],
            "sample_nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in list(index.get_all_nodes())[:5]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes", summary="Get KG nodes")
async def get_kg_nodes(kg_path: str, node_type: Optional[str] = None, limit: int = Query(default=50, le=500)):
    """Get nodes from knowledge graph, optionally filtered by type."""
    REQUESTS.labels(endpoint="/v2/knowledge-graph/nodes", method="GET", status="success").inc()

    try:
        loader = KnowledgeGraphLoader(kg_path)
        kg = loader.load()
        index = KnowledgeGraphIndex(kg)

        nodes = index.get_nodes_by_type(node_type) if node_type else list(index.get_all_nodes())
        return {
            "count": len(nodes[:limit]), "total": len(nodes),
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.type,
                 "biological_features": n.metadata.get("biological_features", [])[:3],
                 "trust_level": n.trust_level}
                for n in nodes[:limit]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{node_id}", summary="Get node neighbors")
async def get_node_neighbors(kg_path: str, node_id: str):
    """Get neighbors of a specific node."""
    REQUESTS.labels(endpoint="/v2/knowledge-graph/neighbors", method="GET", status="success").inc()

    try:
        loader = KnowledgeGraphLoader(kg_path)
        kg = loader.load()
        index = KnowledgeGraphIndex(kg)

        neighbors = index.get_neighbors(node_id)
        edges = index.get_edges_for_node(node_id)

        return {
            "node_id": node_id, "neighbor_count": len(neighbors),
            "neighbors": [{"id": n.id, "label": n.label, "type": n.type} for n in neighbors],
            "edges": [
                {"id": e.id, "source": e.source, "target": e.target, "label": e.label,
                 "strength": e.strength, "correlation_type": e.correlation_type}
                for e in edges
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
