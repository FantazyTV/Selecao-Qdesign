import requests
import numpy as np
import json
import os

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
FEATURE_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "esm2_dim_to_biological_property.json")

def _load_feature_map():
    with open(FEATURE_MAP_PATH, "r") as f:
        return json.load(f)

FEATURE_MAP = _load_feature_map()

# flip
DIM_TO_PROPERTY = {}
for prop, dims in FEATURE_MAP.items():
    for idx, d in enumerate(dims):
        DIM_TO_PROPERTY[int(d)] = DIM_TO_PROPERTY.get(int(d), [])
        DIM_TO_PROPERTY[int(d)].append(prop)

def _apply_feature_mask(vector, feature_mask):
    if feature_mask is None:
        return vector
    return np.multiply(vector, feature_mask).tolist()

def _search_qdrant(collection, seed_vector, n, feature_mask):
    vector = _apply_feature_mask(seed_vector, feature_mask)
    payload = {
        "vector": vector,
        "limit": n,
        "with_payload": True,
        "with_vector": False,
        "with_explanation": True
    }
    resp = requests.post(f"{QDRANT_URL}/collections/{collection}/points/search", json=payload)
    resp.raise_for_status()
    results = resp.json()["result"]
    out = []

    for r in results:
        node_id = r["id"]
        score = r["score"]
        score_explanation = r.get("score_explanation", {})
        mapped_features = {}

        for item in score_explanation.get("top_dimensions", []):
            dim = int(item["dimension"])
            contrib = item["contribution"]
            # Get biological features for this dim
            bio_feats = DIM_TO_PROPERTY.get(dim, [f"dim_{dim}"])
            # Pick at most top 2 features (closest to index 0)
            mapped_features[dim] = bio_feats[:2]
        
        out.append({
            "node_id": node_id,
            "score": score,
            # "score_explanation": score_explanation,
            "biological_features": list(mapped_features.values())[9], # 9 is arbitrary, didn't put 0 because for our small data it was too repetitive
        })

    return out

def retrieve_similar_cif(seed_vector, n=10, feature_mask=None):
    return _search_qdrant("structures", seed_vector, n, feature_mask)

def retrieve_similar_fasta(seed_vector, n=10, feature_mask=None):
    return _search_qdrant("uniprot_sequences", seed_vector, n, feature_mask)
