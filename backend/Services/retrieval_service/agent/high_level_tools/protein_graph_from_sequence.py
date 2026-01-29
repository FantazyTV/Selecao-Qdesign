import os
import logging
import numpy as np
from agent.tools.embedder import esm2_embed
from agent.tools.vector_search import retrieve_similar_fasta, retrieve_similar_cif
from graph.graph_objects import Graph, Node, Edge
from agent.high_level_tools.protein_graph_from_query import normalize_graph, clean_sequence, safe_embed

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("protein_graph_from_sequence")

def build_protein_graph_from_sequence(sequence: str):
    log.info("Building protein graph from sequence input.")
    seq = clean_sequence(sequence)
    if not seq:
        log.error("Input sequence is empty or invalid.")
        return {"nodes": [], "edges": [], "groups": []}
    try:
        vector = safe_embed(seq)
    except Exception:
        log.exception("Embedding failed for input sequence.")
        return {"nodes": [], "edges": [], "groups": []}

    graph = Graph()
    central_node = Node(
        id="input_sequence",
        type="annotation",
        label="Input Sequence",
        metadata={"sequence": seq}
    )
    graph.add_node(central_node)

    # Search both structures and uniprot_sequences
    try:
        results_struct = retrieve_similar_cif(vector, n=3)
    except Exception:
        log.exception("Similarity search failed for sequence input (structures).")
        results_struct = []
    try:
        results_seq = retrieve_similar_fasta(vector, n=3)
    except Exception:
        log.exception("Similarity search failed for sequence input (uniprot_sequences).")
        results_seq = []

    # Add structure nodes/edges
    for res in results_struct:
        node_id = res.get("node_id")
        score = res.get("score", res.get("distance", None))
        node_metadata = {}
        if "biological_features" in res:
            node_metadata["biological_features"] = res.get("biological_features")
        if "payload" in res and isinstance(res["payload"], dict):
            node_metadata.update(res["payload"])
        node_label = node_metadata.get("pdb_id") or node_id
        # Always set type to 'pdb' for structure nodes
        node_type = "pdb"
        node = Node(
            id=node_id,
            type=node_type,
            label=node_label,
            metadata=node_metadata,
        )
        graph.add_node(node)
        edge_metadata = node_metadata.copy()
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="similarity",
            score=score,
            evidence=res.get("evidence", []),
            provenance=edge_metadata
        )
        graph.add_edge(edge)

    # Add uniprot sequence nodes/edges
    for res in results_seq:
        node_id = res.get("node_id")
        score = res.get("score", res.get("distance", None))
        node_metadata = {}
        if "biological_features" in res:
            node_metadata["biological_features"] = res.get("biological_features")
        if "payload" in res and isinstance(res["payload"], dict):
            node_metadata.update(res["payload"])
        node_label = node_metadata.get("uniprot_id") or node_id
        # Always set type to 'sequence' for sequence nodes
        node_type = "sequence"
        node = Node(
            id=node_id,
            type=node_type,
            label=node_label,
            metadata=node_metadata,
        )
        graph.add_node(node)
        edge_metadata = node_metadata.copy()
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="similarity",
            score=score,
            evidence=res.get("evidence", []),
            provenance=edge_metadata
        )
        graph.add_edge(edge)
        # print(graph.as_json())

    raw = graph.as_json()
    # Patch content and fileUrl fields for nodes, following protein_graph_from_query logic
    for n in raw.get("nodes", []):
        print("node:", n)
        node_type = n.get("type")
        metadata = n.get("metadata") or {}
        # If it's a sequence, store sequence in content
        if node_type == "sequence" and metadata.get("sequence"):
            n["content"] = metadata["sequence"]
        # If it's PDB, store fileUrl from cif_path
        if node_type == "pdb" and metadata.get("cif_path"):
            n["fileUrl"] = metadata["cif_path"]
    return normalize_graph(raw)

if __name__ == "__main__":
    test_sequence = "MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPDWQNYTPGPGIRYPLKF"
    graph = build_protein_graph_from_sequence(test_sequence)