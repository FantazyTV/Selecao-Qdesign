#!/usr/bin/env python3
"""Embed PETase PDB sequences with ESM-2 and upsert into Qdrant + Postgres.

Usage:
  /path/to/python embedding_pipeline.py \
    --data-dir /home/fantazy/qdesign/Data \
    --qdrant-url http://localhost:6333 \
    --pg-dsn "postgresql://qdesign:qdesign@localhost:5432/qdesign"
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import torch
from Bio.PDB import PDBParser, PPBuilder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm

try:
    import esm  # ESM C (EvolutionaryScale) package
except Exception:
    esm = None

try:
    import fair_esm as fair_esm_pkg
except Exception:
    fair_esm_pkg = None


@dataclass
class ChainRecord:
    pdb_id: str
    chain_id: str
    sequence: str
    source_file: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed PDB sequences with ESM-2")
    parser.add_argument("--data-dir", required=True, help="Folder containing .pdb or .pdb.gz files")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument(
        "--pg-dsn",
        default="postgresql://qdesign:qdesign@localhost:5432/qdesign",
        help="PostgreSQL DSN",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Qdrant collection name (defaults to model-based name)",
    )
    parser.add_argument(
        "--encoder",
        choices=["esm2", "esmc"],
        default="esmc",
        help="Embedding backend to use",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device to run embeddings on (cpu or cuda)",
    )
    parser.add_argument(
        "--model-name",
        default="esmc_300m",
        help="Model name for selected encoder (e.g., esmc_300m or esm2_t12_35M_UR50D)",
    )
    parser.add_argument("--max-length", type=int, default=1000, help="Max sequence length")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of structures to embed")
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Drop and recreate the Qdrant collection if dimensions differ",
    )
    return parser.parse_args()


def iter_pdb_files(data_dir: Path) -> Iterable[Path]:
    for path in sorted(data_dir.glob("*.pdb")):
        yield path
    for path in sorted(data_dir.glob("*.pdb.gz")):
        yield path


def read_structure(path: Path):
    parser = PDBParser(QUIET=True)
    if path.suffix == ".gz":
        with gzip.open(path, "rt") as handle:
            return parser.get_structure(path.stem.replace(".pdb", ""), handle)
    return parser.get_structure(path.stem.replace(".pdb", ""), str(path))


def extract_longest_chain(structure) -> Optional[ChainRecord]:
    ppb = PPBuilder()
    chains = []
    for model in structure:
        for chain in model:
            peptides = ppb.build_peptides(chain)
            if not peptides:
                continue
            seq = max(peptides, key=lambda p: len(p)).get_sequence()
            chains.append((chain.id, str(seq)))
    if not chains:
        return None
    chain_id, sequence = max(chains, key=lambda item: len(item[1]))
    pdb_id = structure.id
    return ChainRecord(pdb_id=pdb_id.lower(), chain_id=chain_id, sequence=sequence, source_file="")


def build_model(encoder: str, model_name: str, device: str):
    device_obj = torch.device(device)
    if encoder == "esmc":
        if esm is None:
            raise SystemExit("Missing package 'esm'. Install it with pip.")
        from esm.models.esmc import ESMC

        model = ESMC.from_pretrained(model_name, device=device_obj).to(device_obj)
        model.eval()
        return model, None
    if fair_esm_pkg is None:
        raise SystemExit("Missing package 'fair-esm'. Install it with pip.")
    if not hasattr(fair_esm_pkg.pretrained, model_name):
        raise SystemExit(f"Unknown ESM-2 model name: {model_name}")
    model_fn = getattr(fair_esm_pkg.pretrained, model_name)
    model, alphabet = model_fn()
    model = model.to(device_obj)
    model.eval()
    return model, alphabet


def embed_sequences_esm2(model, alphabet, sequences: List[str], device: str) -> torch.Tensor:
    device_obj = torch.device(device)
    batch_converter = alphabet.get_batch_converter()
    data = [(f"seq_{i}", seq) for i, seq in enumerate(sequences)]
    _, _, tokens = batch_converter(data)
    tokens = tokens.to(device_obj)
    with torch.no_grad():
        results = model(tokens, repr_layers=[model.num_layers])
        reps = results["representations"][model.num_layers]
    embeddings = []
    for i, (_, seq) in enumerate(data):
        seq_len = len(seq)
        token_reps = reps[i, 1 : seq_len + 1]
        embeddings.append(token_reps.mean(0))
    return torch.stack(embeddings)


def embed_sequences_esmc(model, sequences: List[str], device: str) -> torch.Tensor:
    device_obj = torch.device(device)
    from esm.sdk.api import ESMProtein, LogitsConfig

    embeddings = []
    for seq in tqdm(sequences, desc="Embedding (ESM C)"):
        protein = ESMProtein(sequence=seq)
        protein_tensor = model.encode(protein)
        logits_output = model.logits(
            protein_tensor, LogitsConfig(sequence=True, return_embeddings=True)
        )
        emb = logits_output.embeddings
        if emb.dim() == 3:
            emb = emb.mean(dim=1)
        if emb.dim() == 2:
            emb = emb.mean(dim=0)
        embeddings.append(emb.to(device_obj))
    return torch.stack(embeddings)


def ensure_collection(
    client: QdrantClient, name: str, vector_size: int, recreate: bool
) -> None:
    existing = client.get_collections().collections
    if any(c.name == name for c in existing):
        info = client.get_collection(name)
        current_size = info.config.params.vectors.size
        if current_size == vector_size:
            return
        if recreate:
            client.delete_collection(name)
        else:
            raise SystemExit(
                f"Collection '{name}' expects dim {current_size}, got {vector_size}. "
                "Use --recreate-collection or a new --collection name."
            )
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def init_postgres(pg_dsn: str):
    import psycopg

    conn = psycopg.connect(pg_dsn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS proteins (
            pdb_id TEXT PRIMARY KEY,
            chain_id TEXT,
            sequence TEXT,
            source_file TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB
        )
        """
    )
    conn.commit()
    return conn


def upsert_postgres(conn, record: ChainRecord) -> None:
    metadata = {
        "sequence_length": len(record.sequence),
        "source_file": record.source_file,
    }
    conn.execute(
        """
        INSERT INTO proteins (pdb_id, chain_id, sequence, source_file, metadata)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (pdb_id) DO UPDATE
        SET chain_id = EXCLUDED.chain_id,
            sequence = EXCLUDED.sequence,
            source_file = EXCLUDED.source_file,
            metadata = EXCLUDED.metadata
        """,
        (record.pdb_id, record.chain_id, record.sequence, record.source_file, json.dumps(metadata)),
    )


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"Data dir not found: {data_dir}")

    model, alphabet = build_model(args.encoder, args.model_name, args.device)
    if not args.collection:
        normalized_model = args.model_name.replace("/", "_")
        args.collection = f"petase_sequences_{args.encoder}_{normalized_model}"

    qdrant = QdrantClient(url=args.qdrant_url)

    pg_conn = init_postgres(args.pg_dsn)

    points: List[PointStruct] = []
    records: List[ChainRecord] = []

    for path in tqdm(list(iter_pdb_files(data_dir)), desc="Parsing PDBs"):
        structure = read_structure(path)
        record = extract_longest_chain(structure)
        if not record:
            continue
        record.source_file = path.name
        if len(record.sequence) > args.max_length:
            record.sequence = record.sequence[: args.max_length]
        records.append(record)

    if not records:
        raise SystemExit("No sequences parsed from PDB files.")

    if args.limit and args.limit > 0:
        records = records[: args.limit]

    sequences = [r.sequence for r in records]
    if args.encoder == "esmc":
        embeddings = embed_sequences_esmc(model, sequences, args.device)
    else:
        embeddings = embed_sequences_esm2(model, alphabet, sequences, args.device)
    vector_size = embeddings.shape[1]
    ensure_collection(qdrant, args.collection, vector_size, args.recreate_collection)

    for idx, record in enumerate(records):
        vector = embeddings[idx].cpu().numpy().tolist()
        payload = {
            "pdb_id": record.pdb_id,
            "chain_id": record.chain_id,
            "sequence_length": len(record.sequence),
            "source_file": record.source_file,
        }
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, record.pdb_id))
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        upsert_postgres(pg_conn, record)

    qdrant.upsert(collection_name=args.collection, points=points)
    pg_conn.commit()
    pg_conn.close()

    print(f"Embedded {len(points)} structures into Qdrant collection '{args.collection}'.")


if __name__ == "__main__":
    main()
