#!/usr/bin/env python3
"""FastAPI search service for PETase embeddings.

Run:
  /home/fantazy/qdesign/.venv/bin/python -m uvicorn backend.Services.ingest.search_api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import torch
from Bio import pairwise2
from Bio.PDB import PDBParser
import requests

from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig
import psycopg


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
PG_DSN = os.getenv("PG_DSN", "postgresql://qdesign:qdesign@localhost:5432/qdesign")
COLLECTION = os.getenv("QDRANT_COLLECTION", "petase_sequences_esmc_esmc_300m")
TEXT_COLLECTION = os.getenv("QDRANT_TEXT_COLLECTION", "petase_text_gemini")
STRUCTURE_COLLECTION = os.getenv("QDRANT_STRUCTURE_COLLECTION", "petase_structures_hist_v1")
MODEL_NAME = os.getenv("ESMC_MODEL", "esmc_300m")
DEVICE = os.getenv("EMBED_DEVICE", "cpu")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
DATA_DIR = os.getenv("DATA_DIR", "/home/fantazy/qdesign/Data")

app = FastAPI(title="QDesign Search API", version="0.1.0")


class SearchRequest(BaseModel):
    pdb_id: Optional[str] = None
    sequence: Optional[str] = None
    top_k: int = 10
    text_query: Optional[str] = None
    alpha: float = 0.7
    beta: float = 0.3
    gamma: float = 0.2
    use_structure: bool = True
    include_mutations: bool = False


class SearchResult(BaseModel):
    pdb_id: str
    chain_id: Optional[str] = None
    score: float
    sequence_length: Optional[int] = None
    source_file: Optional[str] = None


class MutationSuggestion(BaseModel):
    pdb_id: str
    mutation: str
    position: int
    from_residue: str
    to_residue: str


def get_pg_conn():
    return psycopg.connect(PG_DSN)


def load_sequence_from_db(pdb_id: str) -> Optional[str]:
    with get_pg_conn() as conn:
        row = conn.execute(
            "SELECT sequence FROM proteins WHERE pdb_id = %s",
            (pdb_id.lower(),),
        ).fetchone()
    return row[0] if row else None


def load_sequence_and_chain(pdb_id: str) -> Optional[Tuple[str, str]]:
    with get_pg_conn() as conn:
        row = conn.execute(
            "SELECT sequence, chain_id FROM proteins WHERE pdb_id = %s",
            (pdb_id.lower(),),
        ).fetchone()
    return (row[0], row[1]) if row else None


def find_pdb_file(pdb_id: str) -> Optional[str]:
    candidates = [
        f"{pdb_id.lower()}.pdb",
        f"{pdb_id.lower()}.pdb.gz",
        f"{pdb_id.upper()}.pdb",
        f"{pdb_id.upper()}.pdb.gz",
    ]
    for name in candidates:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    return None


def structure_histogram_vector(pdb_path: str, bins: int = 30, max_distance: float = 30.0) -> List[float]:
    parser = PDBParser(QUIET=True)
    if pdb_path.endswith(".gz"):
        import gzip

        with gzip.open(pdb_path, "rt") as handle:
            structure = parser.get_structure("query", handle)
    else:
        structure = parser.get_structure("query", pdb_path)

    coords = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" in residue:
                    coords.append(residue["CA"].coord)
            if coords:
                break
        if coords:
            break
    if len(coords) < 2:
        return [0.0] * (bins + 2)
    coords = torch.tensor(coords, dtype=torch.float32)
    diffs = coords.unsqueeze(1) - coords.unsqueeze(0)
    dists = torch.sqrt((diffs**2).sum(dim=-1))
    triu = torch.triu(dists, diagonal=1)
    values = triu[triu > 0]
    hist = torch.histc(values, bins=bins, min=0.0, max=max_distance)
    hist = hist / (hist.sum() + 1e-8)
    mean_dist = (values.mean() / max_distance).view(1)
    length = torch.tensor([coords.shape[0] / 1000.0])
    vec = torch.cat([hist, mean_dist, length])
    return vec.cpu().numpy().tolist()


def build_model():
    device_obj = torch.device(DEVICE)
    model = ESMC.from_pretrained(MODEL_NAME, device=device_obj).to(device_obj)
    model.eval()
    return model, device_obj


def embed_sequence(model, device_obj, sequence: str):
    protein = ESMProtein(sequence=sequence)
    protein_tensor = model.encode(protein)
    logits_output = model.logits(
        protein_tensor, LogitsConfig(sequence=True, return_embeddings=True)
    )
    emb = logits_output.embeddings
    if emb.dim() == 3:
        emb = emb.mean(dim=1)
    if emb.dim() == 2:
        emb = emb.mean(dim=0)
    return emb.to(device_obj).cpu().numpy().tolist()


def embed_text_gemini(text: str) -> List[float]:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_EMBED_MODEL}:embedContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }
    payload = {
        "content": {
            "parts": [{"text": text}],
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if not resp.ok:
        raise HTTPException(status_code=500, detail=f"Gemini embed error: {resp.text}")
    data = resp.json()
    return data["embedding"]["values"]


def propose_mutations(query_seq: str, neighbor_seq: str, neighbor_id: str) -> List[MutationSuggestion]:
    suggestions: List[MutationSuggestion] = []
    aln = pairwise2.align.globalxx(query_seq, neighbor_seq, one_alignment_only=True)
    if not aln:
        return suggestions
    aligned_q, aligned_n, *_ = aln[0]
    pos = 0
    for q_res, n_res in zip(aligned_q, aligned_n):
        if q_res != "-":
            pos += 1
        if q_res != n_res and q_res != "-" and n_res != "-":
            suggestions.append(
                MutationSuggestion(
                    pdb_id=neighbor_id,
                    mutation=f"{q_res}{pos}{n_res}",
                    position=pos,
                    from_residue=q_res,
                    to_residue=n_res,
                )
            )
        if len(suggestions) >= 3:
            break
    return suggestions


qdrant = QdrantClient(url=QDRANT_URL)
model, device_obj = build_model()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "qdrant": QDRANT_URL,
        "collection": COLLECTION,
        "device": DEVICE,
    }


@app.post("/search", response_model=List[SearchResult])
def search(req: SearchRequest):
    if not req.pdb_id and not req.sequence:
        raise HTTPException(status_code=400, detail="Provide pdb_id or sequence.")

    sequence = req.sequence
    if req.pdb_id:
        sequence = load_sequence_from_db(req.pdb_id)
        if not sequence:
            raise HTTPException(status_code=404, detail="pdb_id not found in Postgres.")

    vector = embed_sequence(model, device_obj, sequence)

    response = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=req.top_k,
    )

    items = []
    for r in response.points:
        payload = r.payload or {}
        items.append(
            SearchResult(
                pdb_id=payload.get("pdb_id"),
                chain_id=payload.get("chain_id"),
                score=r.score,
                sequence_length=payload.get("sequence_length"),
                source_file=payload.get("source_file"),
            )
        )
    return items


@app.post("/search_hybrid")
def search_hybrid(req: SearchRequest):
    if not req.pdb_id and not req.sequence and not req.text_query:
        raise HTTPException(status_code=400, detail="Provide pdb_id, sequence, or text_query.")

    seq_vector = None
    query_sequence = None
    if req.pdb_id or req.sequence:
        query_sequence = req.sequence
        if req.pdb_id:
            query_sequence = load_sequence_from_db(req.pdb_id)
            if not query_sequence:
                raise HTTPException(status_code=404, detail="pdb_id not found in Postgres.")
        seq_vector = embed_sequence(model, device_obj, query_sequence)

    text_vector = None
    if req.text_query:
        try:
            text_vector = embed_text_gemini(req.text_query)
        except Exception:
            text_vector = None

    structure_vector = None
    if req.use_structure and req.pdb_id:
        pdb_path = find_pdb_file(req.pdb_id)
        if pdb_path:
            structure_vector = structure_histogram_vector(pdb_path)

    scores: Dict[str, float] = {}
    payloads: Dict[str, Dict] = {}

    if seq_vector is not None:
        seq_res = qdrant.query_points(
            collection_name=COLLECTION,
            query=seq_vector,
            limit=req.top_k,
        )
        max_score = max((p.score for p in seq_res.points), default=1.0)
        for p in seq_res.points:
            pid = (p.payload or {}).get("pdb_id")
            if not pid:
                continue
            payloads[pid] = p.payload or {}
            scores[pid] = scores.get(pid, 0.0) + req.alpha * (p.score / max_score)

    if text_vector is not None:
        text_res = qdrant.query_points(
            collection_name=TEXT_COLLECTION,
            query=text_vector,
            limit=req.top_k,
        )
        max_score = max((p.score for p in text_res.points), default=1.0)
        for p in text_res.points:
            pid = (p.payload or {}).get("pdb_id")
            if not pid:
                continue
            payloads.setdefault(pid, p.payload or {})
            scores[pid] = scores.get(pid, 0.0) + req.beta * (p.score / max_score)

    if structure_vector is not None:
        struct_res = qdrant.query_points(
            collection_name=STRUCTURE_COLLECTION,
            query=structure_vector,
            limit=req.top_k,
        )
        max_score = max((p.score for p in struct_res.points), default=1.0)
        for p in struct_res.points:
            pid = (p.payload or {}).get("pdb_id")
            if not pid:
                continue
            payloads.setdefault(pid, p.payload or {})
            scores[pid] = scores.get(pid, 0.0) + req.gamma * (p.score / max_score)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[: req.top_k]

    results = []
    for pid, score in ranked:
        payload = payloads.get(pid, {})
        results.append(
            {
                "pdb_id": pid,
                "chain_id": payload.get("chain_id"),
                "score": score,
                "sequence_length": payload.get("sequence_length"),
                "source_file": payload.get("source_file"),
            }
        )

    mutations: List[MutationSuggestion] = []
    if req.include_mutations and query_sequence and results:
        top_id = results[0]["pdb_id"]
        neighbor = load_sequence_from_db(top_id)
        if neighbor:
            mutations = propose_mutations(query_sequence, neighbor, top_id)

    return {"results": results, "mutations": mutations}
