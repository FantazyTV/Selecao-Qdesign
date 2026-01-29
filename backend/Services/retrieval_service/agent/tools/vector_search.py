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
        "with_vector": True,
        "with_explanation": True
    }
    resp = requests.post(f"{QDRANT_URL}/collections/{collection}/points/search", json=payload)
    resp.raise_for_status()
    results = resp.json().get("result", [])
    out = []

    for r in results:
        raw_id = r.get("id")
        score = r.get("score")
        score_explanation = r.get("score_explanation", {})
        r_payload = r.get("payload") or {}
        r_vector = r.get("vector")
        r_chain = r_payload.get("chain")

        mapped_features = {}
        for item in score_explanation.get("top_dimensions", []):
            dim = int(item["dimension"])
            bio_feats = DIM_TO_PROPERTY.get(dim, [f"dim_{dim}"])
            mapped_features[dim] = bio_feats[:2]

        # flatten, preserve order and dedupe, limit to reasonable number
        bio_list = []
        for dim in sorted(mapped_features.keys()):
            for f in mapped_features[dim]:
                if f not in bio_list:
                    bio_list.append(f)
                if len(bio_list) >= 20:
                    break
            if len(bio_list) >= 20:
                break

        node_id = r_payload.get("pdb_id") + "_" + r_chain if r_payload.get("pdb_id") else r_payload.get("uniprot_id") or str(raw_id)

        

        out.append({
            "node_id": node_id,
            "score": score,
            "payload": {
                **r_payload,
                "sequence": r_payload.get("sequence"),   # ensures sequences are available
                "cif_path": r_payload.get("cif_path")    # ensures PDB file URLs are available
            },
            "vector": r_vector,
            "biological_features": bio_list,
            "score_explanation": score_explanation
        })

    return out

def retrieve_similar_cif(seed_vector, n=10, feature_mask=None):
    return _search_qdrant("structures", seed_vector, n, feature_mask)

def retrieve_similar_fasta(seed_vector, n=10, feature_mask=None):
    return _search_qdrant("uniprot_sequences", seed_vector, n, feature_mask)


if __name__ == "__main__":
    # Example usage
    example_vector = [0.0] * 1280  # Replace with actual vector
    results = retrieve_similar_cif(example_vector, n=5)
    for res in results:
        print(res["node_id"])

    results = retrieve_similar_fasta(example_vector, n=5)
    for res in results:
        print(res["node_id"])