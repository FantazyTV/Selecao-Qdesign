
import httpx
import json
import time
from graph.graph_merge_utils import merge_graphs


def post_protein_graph(payload, label, aggregate):
    url = "http://localhost:8000/protein-graph"
    headers = {"Content-Type": "application/json"}
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=None)
    try:
        start = time.time()
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            print(f"\n--- {label} ---")
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                output = response.json()
                aggregate["nodes"].extend(output.get("nodes", []))
                aggregate["edges"].extend(output.get("edges", []))
                print("Response:")
                print(json.dumps(output, indent=2))
            else:
                print("Error Response:")
                print(response.text)
    except Exception as e:
        print(f"Error: {e}")
    end = time.time()
    print(f"Request completed in {end - start:.2f} seconds\n")




if __name__ == "__main__":
    # Collect each graph separately
    query = "1EZA"
    query_payload = {"query": query}
    query_graph = {"nodes": [], "edges": []}
    post_protein_graph(query_payload, "query", query_graph)

    sequence = "MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPDWQNYTPGPGIRYPLKF"
    sequence_payload = {"sequence": sequence}
    sequence_graph = {"nodes": [], "edges": []}
    post_protein_graph(sequence_payload, "sequence", sequence_graph)

    cif_file_path = "tests/data/1E2A.cif"
    with open(cif_file_path, "r", encoding="utf-8", errors="ignore") as f:
        cif_content = f.read()
    cif_payload = {"cif": cif_content}
    cif_graph = {"nodes": [], "edges": []}
    post_protein_graph(cif_payload, "cif", cif_graph)

    # Merge all three graphs using the utility
    merged_graph = merge_graphs([query_graph, sequence_graph, cif_graph])
    with open("response_merged.json", "w") as f:
        json.dump(merged_graph, f, indent=2)
    print("Saved merged graph to response_merged.json")

    # Optionally, save the old aggregate for comparison
    # from graph.graph_merge_utils import finalize_graph_output
    # aggregate = finalize_graph_output([query_graph, sequence_graph, cif_graph], query, sequence)
    # with open("response_all.json", "w") as f:
    #     json.dump(aggregate, f, indent=2)
    # print("Saved all nodes and edges to response_all.json")