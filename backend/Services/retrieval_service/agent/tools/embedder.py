
import torch
import esm
from typing import List, Callable, Any
from graph.graph_objects import Node

# Load ESM2 model once
_esm2_model = None
_esm2_alphabet = None
_esm2_batch_converter = None
def _load_esm2():
    global _esm2_model, _esm2_alphabet, _esm2_batch_converter
    if _esm2_model is None or _esm2_alphabet is None or _esm2_batch_converter is None:
        _esm2_model, _esm2_alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        _esm2_batch_converter = _esm2_alphabet.get_batch_converter()
        _esm2_model.eval()
    return _esm2_model, _esm2_batch_converter

def esm2_embed(sequence: str) -> List[float]:
    """
    Embed a protein sequence using ESM2.
    Returns a mean-pooled embedding as a list of floats.
    """
    model, batch_converter = _load_esm2()
    batch_labels, batch_strs, batch_tokens = batch_converter([("protein1", sequence)])
    with torch.no_grad():
        results = model(batch_tokens, repr_layers=[33], return_contacts=False)
    token_representations = results["representations"][33]
    embedding = token_representations[0, 1:len(sequence)+1].mean(0).cpu().numpy()
    return embedding.tolist()

def embed_if_missing(node: Node, embedder: Callable[[str], List[float]] = None) -> List[float]:
    """
    Embed node if embedding is missing, using ESM2 by default.
    """
    if node.embedding is not None:
        return node.embedding
    text_input = node.label or node.metadata.get("title", "") or str(node.id)
    if embedder is None:
        embedder = esm2_embed
    embedding = embedder(text_input)
    node.embedding = embedding
    node.metadata["embedding_source"] = {
        "method": embedder.__name__,
        "input_text": text_input,
    }
    return embedding
