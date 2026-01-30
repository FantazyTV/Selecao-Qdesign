import datetime
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
    h = int(hashlib.md5(str(node_id).encode()).hexdigest(), 16)
    return {"x": float((h % 1000) / 10.0), "y": float(((h // 1000) % 1000) / 10.0)}

def map_node_type(db_type, node_id):
    if db_type == "rcsb" or db_type == "pdb":
        return "pdb"
    if db_type == "uniprot" or db_type == "sequence" or db_type == "fasta":
        return "sequence"
    if node_id.endswith(".pdf"):
        return "pdf"
    if node_id.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    if node_id.endswith(".txt"):
        return "text"
    return "annotation"

def _color_for_group(group_id: str) -> str:
    h = hashlib.md5(group_id.encode()).hexdigest()
    return f"#{h[:6]}"

def _edge_id(source: str, target: str, score) -> str:
    s = f"{source}::{target}::{score}"
    return hashlib.md5(s.encode()).hexdigest()

def _normalize_strength(score):
    try:
        val = float(score)
    except Exception:
        return 0.0
    if np.isfinite(val):
        if val < 0:
            return 0.0
        if val > 1:
            return 1.0
        return float(val)
    return 0.0

def normalize_graph(graph_json):
    nodes = []
    edges = []
    group_map = {}

    for n in graph_json.get("nodes", []):
        print("node raw:", n)
        node_id = str(n.get("id"))
        raw_type = n.get("type")
        node_type = map_node_type(raw_type, node_id)
        metadata = n.get("metadata") or {}
        content = n.get("content")
        file_url = n.get("fileUrl")
        # If it's a sequence, store sequence in content
        if node_type == "sequence" and metadata.get("sequence"):
            content = metadata["sequence"]
        # If it's PDB, store fileUrl from cif_path
        if node_type == "pdb" and metadata.get("cif_path"):
            file_url = metadata["cif_path"]
        
        if node_type == "pdf":
            file_url = metadata.get("path", file_url)

        trust = "high"
        if metadata.get("source") == "web":
            trust = "medium"

        label = metadata.get("pdb_id") or metadata.get("uniprot_id") or n.get("label") or node_id

        node_obj = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "description": metadata.get("description"),
            "content": content,
            "fileUrl": file_url,
            "position": stable_pos(node_id),
            "trustLevel": trust,
            "notes": n.get("notes", []),
            "metadata": metadata,
            "groupId": raw_type
        }
        nodes.append(node_obj)

        gid = raw_type or "default"
        if gid not in group_map:
            friendly = {"rcsb": "PDB structures", "uniprot": "UniProt sequences", "default": "Misc"}.get(gid, gid)
            group_map[gid] = {"id": gid, "name": friendly, "color": _color_for_group(str(gid))}

    for e in graph_json.get("edges", []):
        source = str(e.get("from_id") or e.get("from") or "")
        target = str(e.get("to_id") or e.get("to") or "")
        raw_type = e.get("type") or e.get("label") or "custom"
        score = e.get("score")
        strength = _normalize_strength(score)
        corr = "custom"
        if raw_type and "similar" in raw_type.lower():
            corr = "similar"
        elif raw_type and raw_type.lower() in {"cites", "contradicts", "supports", "derived"}:
            corr = raw_type.lower()
        label = raw_type
        evidence = e.get("evidence") or []
        prov = e.get("provenance") or {}
        explanation = None
        if evidence:
            explanation = "; ".join(str(x) for x in evidence) if isinstance(evidence, list) else str(evidence)
        if not explanation and prov:
            explanation = "; ".join(f"{k}={v}" for k, v in prov.items())
        edge_id = _edge_id(source, target, score)
        edge_obj = {
            "id": edge_id,
            "source": source,
            "target": target,
            "label": label,
            "correlationType": corr,
            "strength": strength,
            "explanation": explanation,
            "metadata": {"provenance": prov}
        }
        edges.append(edge_obj)

    return {"nodes": nodes, "edges": edges}

def clean_sequence(seq: str) -> str:
    allowed = set("ACDEFGHIKLMNPQRSTVWYUO")
    return "".join(c for c in seq.upper() if c in allowed)

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
    return ""

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

def build_protein_graph_from_query(query: str):
    log.info("Query: %s", query)
    resolved = resolve_protein_name(query)
    log.info("Resolved: %s", resolved)

    pdb_ids = resolved.get("pdb_ids", []) or []
    uniprot_ids = resolved.get("uniprot_ids", []) or []

    central_nodes = []
    if pdb_ids:
        central_nodes.append(("rcsb", pdb_ids[0].upper()))
    if uniprot_ids:
        central_nodes.append(("uniprot", uniprot_ids[0].upper()))
    if not central_nodes:
        log.error("No valid IDs found.")
        return {"nodes": [], "edges": []}

    graph = Graph()

    query_node = Node(
        id=query + str(datetime.datetime.utcnow().timestamp()),
        type="annotation",
        label=query,
    )
    graph.add_node(query_node)

    for db, id_ in central_nodes:
        log.info("Processing %s ID: %s", db.upper(), id_)
        content, vector = None, None

        try:
            if db == "rcsb":
                vec, payload = get_cif_by_pdb_id(id_)
                # log.debug("Qdrant CIF result for %s: vec=%s, payload=%s", id_, vec, payload)
                content = (payload.get("cif_path")) if payload else None
                if vec is not None:
                    arr = np.array(vec, dtype=float)
                    if np.isfinite(arr).all():
                        vector = arr.tolist()
                if vector is None and content:
                    seq = extract_sequence_from_cif(content)
                    if seq:
                        vector = safe_embed(seq)
            else:
                vec, payload = get_fasta_by_uniprot_id(id_)
                # log.debug("Qdrant CIF result for %s: vec=%s, payload=%s", id_, vec, payload)
                raw = (payload.get("fasta_content") or payload.get("content")) if payload else None
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
                        if seq:
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

        central_node = Node(
            id=id_,
            type=db,
            label=id_,
            metadata={
                "pdb_id": id_,
                "cif_path": payload.get("cif_path") if db == "rcsb" else None,
                "sequence": content if db == "uniprot" else None
            }
        )
        
        graph.add_node(central_node)

        derived_edge = Edge(
            from_id=query_node.id,
            to_id=central_node.id,
            type="derived"
        )
        graph.add_edge(derived_edge)

        if content is None or vector is None:
            continue

        try:
            results = retrieve_similar_cif(vector, n=50) if db == "rcsb" else retrieve_similar_fasta(vector, n=5)
        except Exception:
            log.exception("Similarity search failed for %s %s", db, id_)
            results = []

        for res in results:
            node_id = res.get("node_id")
            score = res.get("score", res.get("distance", None))
            node_metadata = {}
            if "biological_features" in res:
                node_metadata["biological_features"] = res.get("biological_features")
            if "payload" in res and isinstance(res["payload"], dict):
                node_metadata.update(res["payload"])

            node_label = node_metadata.get("pdb_id") or node_metadata.get("uniprot_id") or node_id
            content_field = node_metadata.get("sequence") if db == "uniprot" else None
            file_url = node_metadata.get("cif_path") if db == "rcsb" else None

            print(node_id)

            node = Node(
                id=node_id,
                type=db,
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

    raw = graph.as_json()
    return normalize_graph(raw)


if __name__ == "__main__":
    import sys, json
    query = sys.argv[1] if len(sys.argv) > 1 else "1eza"
    graph_json = build_protein_graph_from_query(query)

    # Save to file
    with open("graph_output.json", "w", encoding="utf-8") as f:
        json.dump(graph_json, f, indent=2)

    # Print to console
    print(json.dumps(graph_json, indent=2))