import torch
import esm
from Bio import SeqIO
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import argparse
import torch.serialization

torch.serialization.add_safe_globals([argparse.Namespace])

fasta_file = "uniprot_sprot.fasta\\uniprot_sprot.fasta" # fasta file location
collection_name = "uniprot_sequences"
qdrant_url = "http://localhost:6333"

client = QdrantClient(qdrant_url)

if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=1280,
        distance=Distance.COSINE
    )
)

model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
model.eval()
batch_converter = alphabet.get_batch_converter()

point_id = 0
for record in SeqIO.parse(fasta_file, "fasta"):
    uid = record.id
    seq = str(record.seq)
    try:
        data = [(uid, seq)]
        _, _, toks = batch_converter(data)

        with torch.no_grad():
            out = model(toks, repr_layers=[33])

        reps = out["representations"][33][0, 1:len(seq)+1]
        protein_vec = reps.mean(0).numpy()

        client.upsert(
            collection_name=collection_name,
            points=[{
                "id": point_id,
                "vector": protein_vec.tolist(),
                "payload": {"uniprot_id": uid, "type": "uniprot_sequence"}
            }]
        )
        point_id += 1

        if point_id >= 3600:
            break # stop early because it takes too much time

        if point_id % 100 == 0:
            print(f"Uploaded {point_id} sequences")
    except Exception as e:
        print(f"Failed {uid}: {e}")

print("All sequences uploaded to Qdrant")
