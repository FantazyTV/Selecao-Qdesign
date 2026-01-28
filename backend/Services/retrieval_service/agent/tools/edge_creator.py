import hashlib
from typing import Dict, Any, List, Tuple
from graph.graph_objects import Edge

def create_edge_with_evidence(
    from_node_id: str, 
    to_node_id: str, 
    score: float, 
    evidence: List[Tuple[str, int, float]], 
    provenance: Dict[str, Any]
) -> Edge:
    """
    Create a similarity edge with evidence and provenance.
    
    Args:
        from_node_id: Source node ID
        to_node_id: Target node ID  
        score: Similarity score
        evidence: List of (feature_name, dimension, contribution) tuples
        provenance: Dict with collection, id, query_vector_hash etc.
        
    Returns:
        Edge object with evidence and provenance
    """
    # Format evidence as readable string
    evidence_str = "; ".join([
        f"{feature} (dim {dim}, contrib {contrib:.3f})" 
        for feature, dim, contrib in evidence
    ])
    
    # Create edge
    edge = Edge(
        from_id=from_node_id,
        to_id=to_node_id,
        type="similarity",
        score=score,
        evidence=evidence_str,
        provenance={
            **provenance,
            "evidence_features": evidence,  # Store raw evidence too
        }
    )
    
    return edge