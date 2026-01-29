import os
import logging
import numpy as np
from agent.tools.web_search import resolve_protein_name
from agent.tools.qdrant_retrieval import get_cif_by_pdb_id, get_fasta_by_uniprot_id
from agent.tools.remote_downloader import download_pdb_structure, download_uniprot_fasta
from agent.tools.embedder import esm2_embed
from agent.tools.vector_search import retrieve_similar_cif, retrieve_similar_fasta
from graph.graph_objects import Graph, Node, Edge
import hashlib

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("protein_graph_demo")

THREE_TO_ONE = {
    "ALA": "A","ARG": "R","ASN": "N","ASP": "D","CYS": "C","GLU": "E","GLN": "Q","GLY": "G",
    "HIS": "H","ILE": "I","LEU": "L","LYS": "K","MET": "M","PHE": "F","PRO": "P","SER": "S",
    "THR": "T","TRP": "W","TYR": "Y","VAL": "V",
    "SEC": "U", "PYL": "O"
}

def stable_pos(node_id):
    h = int(hashlib.md5(node_id.encode()).hexdigest(), 16)
    return {"x": (h % 1000) / 10.0, "y": ((h // 1000) % 1000) / 10.0}

def map_node_type(db_type, node_id):
    if db_type == "rcsb":
        return "pdb"
    if db_type == "uniprot":
        return "sequence"
    if node_id.endswith(".pdf"):
        return "pdf"
    if node_id.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    return "annotation"

def normalize_graph(graph_json):
    nodes = []
    edges = []

    for n in graph_json["nodes"]:
        node_type = map_node_type(n.get("type"), n.get("id"))

        content = None
        if node_type == "sequence":
            content = n.get("metadata", {}).get("sequence")
        elif node_type == "pdb":
            content = n.get("metadata", {}).get("structure")

        trust = "high"
        if n.get("metadata", {}).get("source") == "web":
            trust = "medium"

        nodes.append({
            "id": n["id"],
            "type": node_type,
            "label": n.get("label", n["id"]),
            "description": n.get("metadata", {}).get("description"),
            "content": content,
            "fileUrl": n.get("metadata", {}).get("file_url"),
            "position": stable_pos(n["id"]),
            "trustLevel": trust,
            "notes": [],
            "metadata": n.get("metadata"),
            "groupId": n.get("type")
        })

    for e in graph_json["edges"]:
        edges.append({
            "from": e["from_id"],
            "to": e["to_id"],
            "type": e["type"],
            "score": e.get("score"),
            "evidence": e.get("evidence", []),
            "provenance": e.get("provenance", {})
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
def clean_sequence(seq: str) -> str:
    allowed = set("ACDEFGHIKLMNPQRSTVWYUO")
    return "".join(c for c in seq.upper() if c in allowed)

def extract_sequence_from_pdb(pdb_text: str) -> str:
    seqres = {}
    lines = pdb_text.splitlines()
    for line in lines:
        if line.startswith("SEQRES"):
            parts = line.split()
            if len(parts) >= 5:
                chain = parts[2]
                residues = parts[4:]
                seqres.setdefault(chain, []).extend(residues)
    if seqres:
        chain = next(iter(seqres))
        aa = [THREE_TO_ONE.get(r.upper(), "") for r in seqres[chain] if THREE_TO_ONE.get(r.upper(), "")]
        return clean_sequence("".join(aa))

    residues_by_chain = {}
    seen = set()
    for line in lines:
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        resname = line[17:20].strip()
        chain = line[21].strip() if len(line) > 21 else ""
        resnum = line[22:26].strip() if len(line) > 26 else ""
        key = (chain, resnum)
        if key in seen:
            continue
        seen.add(key)
        residues_by_chain.setdefault(chain, []).append(resname)
    if residues_by_chain:
        chain = next(iter(residues_by_chain))
        aa = [THREE_TO_ONE.get(r.upper(), "") for r in residues_by_chain[chain] if THREE_TO_ONE.get(r.upper(), "")]
        return clean_sequence("".join(aa))
    return ""

def extract_sequence_from_cif(cif_text: str) -> str:
    lines = cif_text.splitlines()
    key = "_entity_poly.pdbx_seq_one_letter_code_can"
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line.startswith(key):
            continue
        rest = raw[len(key):].lstrip()
        if not rest:
            i = idx + 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and lines[i].lstrip().startswith(";"):
                seq_lines = []
                i += 1
                while i < len(lines) and not lines[i].lstrip().startswith(";"):
                    seq_lines.append(lines[i].rstrip("\n"))
                    i += 1
                return clean_sequence("".join(seq_lines))
            continue
        rest_stripped = rest.strip()
        if rest_stripped.startswith(";"):
            seq_lines = []
            i = idx + 1
            while i < len(lines) and not lines[i].lstrip().startswith(";"):
                seq_lines.append(lines[i].rstrip("\n"))
                i += 1
            return clean_sequence("".join(seq_lines))
        if rest_stripped.startswith(("'", '"')):
            quote = rest_stripped[0]
            if rest_stripped.endswith(quote) and len(rest_stripped) > 1:
                return clean_sequence(rest_stripped.strip(quote))
            seq_parts = [rest_stripped.lstrip(quote)]
            i = idx + 1
            while i < len(lines):
                l = lines[i]
                if l.rstrip().endswith(quote):
                    seq_parts.append(l.rstrip().rstrip(quote))
                    break
                seq_parts.append(l.rstrip("\n"))
                i += 1
            return clean_sequence("".join(seq_parts))
        return clean_sequence(rest_stripped.strip('"').strip("'"))
    return extract_sequence_from_pdb(cif_text)

def safe_embed(sequence: str):
    if not sequence or len(sequence) < 3:
        raise RuntimeError("Sequence too short or empty for embedding")
    seq = clean_sequence(sequence)
    if not seq:
        raise RuntimeError("Sequence empty after cleaning")
    vec = esm2_embed(seq)
    if isinstance(vec, np.ndarray):
        if not np.isfinite(vec).all():
            raise RuntimeError("Embedding contains NaN/Inf")
        return vec.astype(float).tolist()
    arr = np.array(vec, dtype=float)
    if not np.isfinite(arr).all():
        raise RuntimeError("Embedding contains NaN/Inf")
    return arr.tolist()

def build_protein_graph(query: str):
    log.info("Query: %s", query)
    resolved = resolve_protein_name(query)
    log.info("Resolved: %s", resolved)

    pdb_ids = resolved.get("pdb_ids", [])
    uniprot_ids = resolved.get("uniprot_ids", [])

    central_nodes = []
    if pdb_ids:
        central_nodes.append(("rcsb", pdb_ids[0].upper()))
    if uniprot_ids:
        central_nodes.append(("uniprot", uniprot_ids[0].upper()))
    if not central_nodes:
        log.error("No valid IDs found.")
        return None

    graph = Graph()

    for db, id_ in central_nodes:
        log.info("Processing %s ID: %s", db.upper(), id_)
        content, vector = None, None

        try:
            if db == "rcsb":
                vec, payload = get_cif_by_pdb_id(id_)
                content = payload.get("cif_content") or payload.get("content") if payload else None
                if vec is not None:
                    arr = np.array(vec, dtype=float)
                    if np.isfinite(arr).all():
                        vector = arr.tolist()
                if vector is None and content:
                    seq = extract_sequence_from_cif(content)
                    vector = safe_embed(seq)
            else:
                vec, payload = get_fasta_by_uniprot_id(id_)
                raw = payload.get("fasta_content") or payload.get("content") if payload else None
                content = "".join(l.strip() for l in raw.splitlines() if not l.startswith(">")) if raw else None
                if vec is not None:
                    arr = np.array(vec, dtype=float)
                    if np.isfinite(arr).all():
                        vector = arr.tolist()
                if vector is None and content:
                    vector = safe_embed(content)
        except Exception:
            log.exception("Qdrant lookup failed for %s %s", db, id_)

        if content is None or vector is None:
            log.info("Qdrant missing/invalid. Downloading from web for %s %s...", db, id_)
            try:
                if db == "rcsb":
                    path = download_pdb_structure(id_)
                    if path and os.path.exists(path):
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        seq = extract_sequence_from_cif(content)
                        vector = safe_embed(seq)
                else:
                    download_uniprot_fasta(id_)
                    fasta_path = os.path.join("fastas", f"{id_}.fasta")
                    if os.path.exists(fasta_path):
                        with open(fasta_path, "r", encoding="utf-8", errors="ignore") as f:
                            raw = f.read()
                        content = "".join(l.strip() for l in raw.splitlines() if not l.startswith(">"))
                        vector = safe_embed(content)
            except Exception:
                log.exception("Download/embed failed for %s %s", db, id_)

        central_node = Node(id=id_, type=db, label=id_)
        graph.add_node(central_node)
        if content is None or vector is None:
            continue

        try:
            results = retrieve_similar_cif(vector, n=5) if db == "rcsb" else retrieve_similar_fasta(vector, n=5)
        except Exception:
            log.exception("Similarity search failed for %s %s", db, id_)
            results = []

        for res in results:
            node_id = res.get("node_id")
            score = res.get("score")
            node_metadata = {"biological_features": res.get("biological_features")} if "biological_features" in res else {}
            node = Node(id=node_id, type=db, label=node_id, metadata=node_metadata)
            graph.add_node(node)
            edge_metadata = node_metadata.copy()
            edge = Edge(from_id=central_node.id, to_id=node.id, type="similarity", score=score, evidence=[], provenance=edge_metadata)
            graph.add_edge(edge)

    raw = graph.as_json()
    return normalize_graph(raw)

if __name__ == "__main__":
    import sys, json
    query = sys.argv[1] if len(sys.argv) > 1 else "1eza"
    graph_json = build_protein_graph(query)
    print(json.dumps(graph_json, indent=2))
