import requests

QDRANT_URL = "http://localhost:6333"

def get_cif_by_pdb_id(pdb_id: str, collection_name="structures"):
    url = f"{QDRANT_URL}/collections/{collection_name}/points/search"
    payload = {
        "limit": 1,
        "with_vector": True,
        "with_payload": True,
        "vector": [0.0]*1280,  # dummy vector, ignored due to filter
        "filter": {
            "must": [
                {"key": "pdb_id", "match": {"value": pdb_id}}
            ]
        }
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if not results:
        return None, None
    point = results[0]
    return point.get("vector"), point.get("payload")

def get_fasta_by_uniprot_id(uniprot_id: str, collection_name="uniprot_sequences"):
    url = f"{QDRANT_URL}/collections/{collection_name}/points/search"
    payload = {
        "limit": 1,
        "with_vector": True,
        "with_payload": True,
        "vector": [0.0]*1280,
        "filter": {
            "must": [
                {"key": "uniprot_id", "match": {"value": uniprot_id}}
            ]
        }
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if not results:
        return None, None
    point = results[0]
    return point.get("vector"), point.get("payload")
