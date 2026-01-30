"""
Scientist Input Preparation - Prepare input for Scientist LLM prompt.
"""


def prepare_scientist_input(
    subgraph: dict,
    natural_language: str,
    kg_metadata: dict,
    enriched: dict,
    user_query: str
) -> dict:
    """Prepare comprehensive input for the Scientist LLM prompt."""
    paths = subgraph.get("paths", [])
    primary_path = paths[0] if paths else {}

    edge_analysis = _build_edge_analysis(subgraph.get("edges", []))
    node_descriptions = _build_node_descriptions(subgraph.get("nodes", []))

    return {
        "main_objective": kg_metadata.get("main_objective", ""),
        "secondary_objectives": kg_metadata.get("secondary_objectives", []),
        "user_query": user_query,
        "natural_language_context": natural_language,
        "nodes": node_descriptions,
        "edges": edge_analysis,
        "primary_path": primary_path,
        "num_paths": len(paths),
        "planner_rationale": enriched.get("rationale", []),
        "key_concepts": enriched.get("key_concepts_identified", []),
        "graph_statistics": {
            "total_nodes": len(node_descriptions),
            "total_edges": len(edge_analysis),
            "avg_confidence": (
                sum(e.get("confidence", 0.5) for e in edge_analysis) /
                max(len(edge_analysis), 1)
            )
        }
    }


def _build_edge_analysis(edges: list) -> list[dict]:
    """Build edge-by-edge analysis structure."""
    return [
        {
            "from": e.get("source"),
            "to": e.get("target"),
            "relationship": e.get("label", e.get("correlationType", "related")),
            "confidence": e.get("strength", 0.5),
            "explanation": e.get("explanation", "No explanation provided")
        }
        for e in edges
    ]


def _build_node_descriptions(nodes: list) -> list[dict]:
    """Build node descriptions."""
    result = []
    for node in nodes:
        bio_features = node.get("biological_features", [])
        if isinstance(bio_features, str):
            bio_features = [bio_features]
        result.append({
            "id": node.get("id"),
            "label": node.get("label"),
            "type": node.get("type"),
            "biological_features": bio_features[:5],
            "trust_level": node.get("trustLevel", 0.5)
        })
    return result
