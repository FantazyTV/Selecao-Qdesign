"""
Test Qdrant queries using raw HTTP requests
- Fetch top 10 candidates for a zero vector from 'pdfs' and 'images' collections
- Print all returned results
"""

import requests
import os
import json

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
BASE_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

COLLECTIONS = ["pdfs", "images"]

# Vector sizes for each collection
VECTOR_SIZES = {
    "pdfs": 384,
    "images": 512,
}

def search_qdrant(collection: str, vector_size: int):
    url = f"{BASE_URL}/collections/{collection}/points/search"
    zero_vector = [0.0] * vector_size
    payload = {
        "vector": zero_vector,
        "limit": 10,
        "with_payload": True,
        "with_vector": False,
    }
    response = requests.post(url, json=payload)
    print(f"\nResults for collection '{collection}':")
    if response.status_code == 200:
        results = response.json()
        print(json.dumps(results, indent=2))
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    for collection in COLLECTIONS:
        search_qdrant(collection, VECTOR_SIZES[collection])
