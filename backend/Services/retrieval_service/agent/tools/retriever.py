import hashlib
from typing import List, Dict, Any, Optional
from agent.tools.vector_search import retrieve_similar_cif, retrieve_similar_fasta

def retrieve_candidates(
    seed_vector: List[float], 
    collections: List[str] = None, 
    n: int = 50, 
    feature_mask: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve similar candidates from specified collections.
    
    Args:
        seed_vector: Embedding vector to search with
        collections: List of collections to search (structures, uniprot_sequences)
        n: Max results per collection
        feature_mask: Optional feature mask for search
        
    Returns:
        List of raw Qdrant results with collection and query_vector tags
    """
    if collections is None:
        collections = ["structures", "uniprot_sequences"]
    
    all_results = []
    
    # Create query vector hash for provenance
    query_hash = hashlib.md5(str(seed_vector[:10]).encode()).hexdigest()[:8]
    
    for collection in collections:
        try:
            if collection == "structures":
                results = retrieve_similar_cif(seed_vector, n=n, feature_mask=feature_mask)
            elif collection == "uniprot_sequences":
                results = retrieve_similar_fasta(seed_vector, n=n, feature_mask=feature_mask)
            else:
                continue
                
            # Tag results with collection and query info
            for result in results:
                result["collection"] = collection
                result["query_vector_hash"] = query_hash
                result["query_vector"] = seed_vector  # Store full vector for provenance
                
            all_results.extend(results[:n])  # Rate limit per collection
            
        except Exception as e:
            # Log error but continue with other collections
            print(f"Error retrieving from {collection}: {e}")
            continue
    
    return all_results
