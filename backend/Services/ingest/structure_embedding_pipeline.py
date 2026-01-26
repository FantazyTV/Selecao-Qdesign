#!/usr/bin/env python3
"""Create simple 3D structure embeddings from PDBs and upsert into Qdrant.

Embeddings are based on CA-atom pairwise distance histograms.
"""

from __future__ import annotations

import argparse
import gzip
import uuid
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import torch
from Bio.PDB import PDBParser
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed PDB structures via CA distance histograms")
    parser.add_argument("--data-dir", required=True, help="Folder containing .pdb or .pdb.gz files")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument(
        "--collection",
        default="petase_structures_hist_v1",
        help="Qdrant collection name",
    )
    parser.add_argument("--max-distance", type=float, default=30.0, help="Max distance for histogram")
    parser.add_argument("--bins", type=int, default=30, help="Number of histogram bins")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of structures")
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


def extract_ca_coords(structure) -> Optional[Tuple[str, str, torch.Tensor]]:
    coords = []
    chain_id = None
    for model in structure:
        for chain in model:
            chain_id = chain.id
            for residue in chain:
                if "CA" in residue:
                    coords.append(residue["CA"].coord)
            if coords:
                break
        if coords:
            break
    if not coords:
        return None
    pdb_id = structure.id.lower()
    return pdb_id, chain_id, torch.tensor(coords, dtype=torch.float32)


def histogram_embedding(coords: torch.Tensor, bins: int, max_distance: float) -> torch.Tensor:
    if coords.shape[0] < 2:
        return torch.zeros(bins + 2)
    diffs = coords.unsqueeze(1) - coords.unsqueeze(0)
    dists = torch.sqrt((diffs**2).sum(dim=-1))
    triu = torch.triu(dists, diagonal=1)
    values = triu[triu > 0]
    hist = torch.histc(values, bins=bins, min=0.0, max=max_distance)
    hist = hist / (hist.sum() + 1e-8)
    mean_dist = values.mean() / max_distance
    length = torch.tensor([coords.shape[0] / 1000.0])
    return torch.cat([hist, mean_dist.view(1), length])


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    existing = client.get_collections().collections
    if any(c.name == name for c in existing):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"Data dir not found: {data_dir}")

    qdrant = QdrantClient(url=args.qdrant_url)

    points: List[PointStruct] = []
    count = 0
    for path in tqdm(list(iter_pdb_files(data_dir)), desc="Parsing PDBs"):
        structure = read_structure(path)
        item = extract_ca_coords(structure)
        if not item:
            continue
        pdb_id, chain_id, coords = item
        vector = histogram_embedding(coords, args.bins, args.max_distance)
        payload = {
            "pdb_id": pdb_id,
            "chain_id": chain_id,
            "num_residues": int(coords.shape[0]),
            "source_file": path.name,
        }
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, pdb_id))
        points.append(PointStruct(id=point_id, vector=vector.tolist(), payload=payload))
        count += 1
        if args.limit and count >= args.limit:
            break

    if not points:
        raise SystemExit("No structures parsed.")

    ensure_collection(qdrant, args.collection, len(points[0].vector))
    qdrant.upsert(collection_name=args.collection, points=points)

    print(f"Embedded {len(points)} structures into Qdrant collection '{args.collection}'.")


if __name__ == "__main__":
    main()
