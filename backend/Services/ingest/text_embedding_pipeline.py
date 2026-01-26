#!/usr/bin/env python3
"""Embed text (abstracts/notes) with Gemini and upsert into Qdrant.

Input format: JSONL with one object per line:
  {"pdb_id": "5xjh", "text": "Abstract or notes..."}

Usage:
  /path/to/python text_embedding_pipeline.py \
    --input /home/fantazy/qdesign/Data/abstracts.jsonl \
    --qdrant-url http://localhost:6333 \
    --collection petase_text_gemini
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import List

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed text with Gemini")
    parser.add_argument("--input", required=True, help="Path to abstracts.jsonl")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--collection", default="petase_text_gemini")
    parser.add_argument("--model", default="gemini-embedding-001")
    return parser.parse_args()


def gemini_embed(text: str, api_key: str, model: str) -> List[float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    payload = {
        "content": {
            "parts": [{"text": text}],
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["embedding"]["values"]


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    existing = client.get_collections().collections
    if any(c.name == name for c in existing):
        info = client.get_collection(name)
        if info.config.params.vectors.size != vector_size:
            raise SystemExit(
                f"Collection '{name}' has dim {info.config.params.vectors.size}, got {vector_size}."
            )
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def main() -> None:
    args = parse_args()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set.")

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    qdrant = QdrantClient(url=args.qdrant_url)

    records = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    if not records:
        raise SystemExit("No records found in input.")

    first_vector = gemini_embed(records[0]["text"], api_key, args.model)
    ensure_collection(qdrant, args.collection, len(first_vector))

    points: List[PointStruct] = []
    for record in tqdm(records, desc="Embedding text"):
        vector = gemini_embed(record["text"], api_key, args.model)
        payload = {
            "pdb_id": record["pdb_id"].lower(),
            "text_preview": record["text"][:200],
        }
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, record["pdb_id"].lower()))
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    qdrant.upsert(collection_name=args.collection, points=points)
    print(f"Embedded {len(points)} texts into Qdrant collection '{args.collection}'.")


if __name__ == "__main__":
    main()
