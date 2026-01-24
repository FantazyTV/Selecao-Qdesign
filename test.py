#!/usr/bin/env python3
"""Colab runner: embed sequences with ESM C, upsert to Qdrant, export Postgres CSV.

Usage (Colab):
  export QDRANT_URL="https://YOUR_NGROK_URL.ngrok-free.app"
  export COLLECTION="petase_sequences_esmc_esmc_300m"
  export DEVICE="cuda"
  python /content/test.py
"""

from __future__ import annotations

import gzip
import json
import os
import uuid
from pathlib import Path
import time

import torch
from Bio.PDB import PDBParser, PPBuilder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm
import requests

from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig


DATA_DIR = Path(os.getenv("DATA_DIR", "/content/Data"))
QDRANT_URL = os.environ.get("QDRANT_URL", "")
COLLECTION = os.environ.get("COLLECTION", "petase_sequences_esmc_esmc_300m")
DEVICE = os.environ.get("DEVICE", "cuda")
LIMIT = int(os.environ.get("LIMIT", "10"))
DISABLE_QDRANT = os.environ.get("DISABLE_QDRANT", "0") == "1"


def read_structure(path: Path):
	parser = PDBParser(QUIET=True)
	if path.suffix == ".gz":
		with gzip.open(path, "rt") as handle:
			return parser.get_structure(path.stem.replace(".pdb", ""), handle)
	return parser.get_structure(path.stem.replace(".pdb", ""), str(path))


def extract_longest_chain(structure):
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
	return structure.id.lower(), chain_id, sequence


def embed_esmc(model, seqs):
	embeddings = []
	for seq in tqdm(seqs, desc="Embedding (ESM C)"):
		protein = ESMProtein(sequence=seq)
		protein_tensor = model.encode(protein)
		out = model.logits(protein_tensor, LogitsConfig(sequence=True, return_embeddings=True))
		emb = out.embeddings
		if emb.dim() == 3:
			emb = emb.mean(dim=1)
		if emb.dim() == 2:
			emb = emb.mean(dim=0)
		embeddings.append(emb)
	return torch.stack(embeddings)


def main() -> None:
	if not QDRANT_URL and not DISABLE_QDRANT:
		raise SystemExit("QDRANT_URL is not set.")

	if not DATA_DIR.exists():
		raise SystemExit(f"Data directory not found: {DATA_DIR}")

	device = torch.device(DEVICE)
	model = ESMC.from_pretrained("esmc_300m", device=device).to(device)
	model.eval()

	records = []
	pdb_files = list(DATA_DIR.glob("*.pdb")) + list(DATA_DIR.glob("*.pdb.gz"))
	for path in sorted(pdb_files):
		structure = read_structure(path)
		row = extract_longest_chain(structure)
		if not row:
			continue
		pdb_id, chain_id, sequence = row
		records.append((pdb_id, chain_id, sequence, path.name))

	if not records:
		raise SystemExit(f"No PDB files found in {DATA_DIR}")

	if LIMIT > 0:
		records = records[:LIMIT]

	seqs = [r[2] for r in records]
	emb = embed_esmc(model, seqs).cpu().numpy()

	if DISABLE_QDRANT:
		out_path = Path("/content/structure_vectors.jsonl")
		with out_path.open("w") as f:
			for i, (pdb_id, chain_id, sequence, source_file) in enumerate(records):
				payload = {
					"pdb_id": pdb_id,
					"chain_id": chain_id,
					"sequence_length": len(sequence),
					"source_file": source_file,
				}
				f.write(
					json.dumps({"pdb_id": pdb_id, "vector": emb[i].tolist(), "payload": payload})
					+ "\n"
				)
		print(f"Wrote JSONL vectors: {out_path}")
		return

	# Preflight check
	r = requests.get(QDRANT_URL + "/readyz", timeout=30)
	r.raise_for_status()

	qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False, timeout=30)
	for attempt in range(5):
		try:
			collections = qdrant.get_collections().collections
			break
		except Exception:
			if attempt == 4:
				raise
			time.sleep(5)
	if COLLECTION not in [c.name for c in collections]:
		qdrant.create_collection(
			collection_name=COLLECTION,
			vectors_config=VectorParams(size=emb.shape[1], distance=Distance.COSINE),
		)

	points = []
	for i, (pdb_id, chain_id, sequence, source_file) in enumerate(records):
		payload = {
			"pdb_id": pdb_id,
			"chain_id": chain_id,
			"sequence_length": len(sequence),
			"source_file": source_file,
		}
		point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, pdb_id))
		points.append(PointStruct(id=point_id, vector=emb[i].tolist(), payload=payload))

	batch_size = 5
	for i in range(0, len(points), batch_size):
		batch = points[i : i + batch_size]
		print(f"Upserting batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}...")
		for attempt in range(5):
			try:
				qdrant.upsert(collection_name=COLLECTION, points=batch)
				break
			except Exception:
				if attempt == 4:
					raise
				time.sleep(5)
	print(f"Upserted {len(points)} vectors to {COLLECTION}")

	csv_path = Path("/content/postgres_proteins.csv")
	with csv_path.open("w") as f:
		f.write("pdb_id,chain_id,sequence,source_file,metadata_json\n")
		for pdb_id, chain_id, sequence, source_file in records:
			metadata = {"sequence_length": len(sequence), "source_file": source_file}
			row = [
				pdb_id,
				chain_id,
				sequence,
				source_file,
				json.dumps(metadata).replace('"', '""'),
			]
			f.write(",".join([f"\"{x}\"" for x in row]) + "\n")

	print(f"Wrote Postgres CSV: {csv_path}")


if __name__ == "__main__":
	main()
