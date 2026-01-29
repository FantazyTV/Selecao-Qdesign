import hashlib
from typing import Dict, Any, List

def edge_id(source, target, label):
    s = f"{source}::{target}::{label}"
    return hashlib.md5(s.encode()).hexdigest()

def merge_graphs(graphs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple graph dicts (with 'nodes' and 'edges') into one, handling deduplication and unique edge ids.
    """
    node_map = {}  # id -> node (first occurrence)
    edge_id_count = {}
    merged_nodes = []
    merged_edges = []
    for graph in graphs:
        for node in graph.get("nodes", []):
            node_id = node.get("id")
            if node_id not in node_map:
                node_map[node_id] = node
                merged_nodes.append(node)
        for edge in graph.get("edges", []):
            src = edge.get("from_id") or edge.get("source")
            tgt = edge.get("to_id") or edge.get("target")
            label = edge.get("type") or edge.get("label") or "custom"
            eid = edge.get("id") or edge_id(src, tgt, label)
            # Ensure uniqueness
            if eid in edge_id_count:
                edge_id_count[eid] += 1
                eid_unique = f"{eid}_{edge_id_count[eid]}"
                edge["id"] = eid_unique
            else:
                edge_id_count[eid] = 1
                edge["id"] = eid
            if "correlationType" not in edge:
                if edge.get("type") in {"query_to_pdb", "query_to_sequence"}:
                    edge["correlationType"] = "derived"
                elif edge.get("type") and "similar" in edge.get("type").lower():
                    edge["correlationType"] = "similar"
                else:
                    edge["correlationType"] = "custom"
            merged_edges.append(edge)
    return {"nodes": merged_nodes, "edges": merged_edges}
