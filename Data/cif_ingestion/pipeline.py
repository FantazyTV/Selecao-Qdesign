import os
import torch
import esm
import numpy as np
from Bio.PDB import MMCIFParser, PPBuilder
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

cif_dir = "./pdbs"  # folder with .cif files
collection_name = "structures"
qdrant_url = "http://localhost:6333"

client = QdrantClient(url=qdrant_url)

client.recreate_collection(
    collection_name="structures",
    vectors_config=VectorParams(size=1280, distance=Distance.COSINE)
)

model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
model.eval()
batch_converter = alphabet.get_batch_converter()

parser = MMCIFParser(QUIET=True)
ppb = PPBuilder()

point_id = 0


counter = 0
for cif_file in os.listdir(cif_dir):
    if not cif_file.lower().endswith(".cif"):
        continue

    pdb_id = os.path.splitext(cif_file)[0].upper()
    path = os.path.join(cif_dir, cif_file)

    try:
        structure = parser.get_structure(pdb_id, path)
    except Exception as e:
        print(f"Failed to parse {pdb_id}: {e}")
        continue

    chains = []
    for model_ in structure:
        for chain in model_:
            peptides = ppb.build_peptides(chain)
            for pep in peptides:
                chains.append((chain.id, str(pep.get_sequence())))

    embeddings = {}
    for chain_id, seq in chains:
        data = [("chain", seq)]
        _, _, toks = batch_converter(data)

        with torch.no_grad():
            out = model(toks, repr_layers=[33])

        reps = out["representations"][33][0, 1:len(seq)+1]
        protein_vec = reps.mean(0)
        embeddings[chain_id] = protein_vec.numpy()

    points = []
    for chain_id, vec in embeddings.items():
        points.append({
            "id": point_id,
            "vector": vec.tolist(),
            "payload": {
                "pdb_id": pdb_id,
                "chain": chain_id,
                "type": "protein_structure"
            }
        })
        point_id += 1

    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Uploaded {len(points)} chains from {pdb_id}")

    counter += 1