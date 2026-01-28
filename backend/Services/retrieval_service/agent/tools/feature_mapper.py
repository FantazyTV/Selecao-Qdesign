import json
import os
from typing import List, Dict, Any, Tuple

# Load feature map
FEATURE_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "esm2_dim_to_biological_property.json")
with open(FEATURE_MAP_PATH, "r") as f:
    FEATURE_MAP = json.load(f)

# Create reverse mapping
DIM_TO_PROPERTY = {}
for prop, dims in FEATURE_MAP.items():
    for dim in dims:
        if dim not in DIM_TO_PROPERTY:
            DIM_TO_PROPERTY[dim] = []
        DIM_TO_PROPERTY[dim].append(prop)

def map_score_explanation_to_features(qdrant_result: Dict[str, Any], feature_map: Dict[str, List[int]] = None) -> List[Tuple[str, int, float]]:
    """
    Map Qdrant score explanation dimensions to biological features.
    
    Args:
        qdrant_result: Single Qdrant result dict with score_explanation
        feature_map: Optional feature mapping dict
        
    Returns:
        List of (feature_name, dimension, contribution) tuples
    """
    if feature_map is None:
        feature_map = FEATURE_MAP
    
    score_explanation = qdrant_result.get("score_explanation", {})
    top_dimensions = score_explanation.get("top_dimensions", [])
    
    mapped_features = []
    
    for dim_info in top_dimensions:
        dim = dim_info.get("dimension")
        contribution = dim_info.get("contribution", 0.0)
        
        # Get biological features for this dimension
        bio_features = DIM_TO_PROPERTY.get(dim, [f"dim_{dim}"])
        
        # Take the first (most relevant) feature
        feature_name = bio_features[0] if bio_features else f"dim_{dim}"
        
        mapped_features.append((feature_name, dim, contribution))
    
    return mapped_features
