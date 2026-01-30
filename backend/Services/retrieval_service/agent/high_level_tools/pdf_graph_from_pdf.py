import os
import logging
from agent.high_level_tools.protein_graph_from_query import normalize_graph
from agent.tools.embedder import text_embed
from agent.tools.vector_search import retrieve_similar_pdfs
from graph.graph_objects import Graph, Node, Edge

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pdf_graph_from_pdf")

def build_pdf_graph_from_pdf(pdf_content: str, pdf_name: str = "input_pdf"):
    """
    Build a graph of similar PDFs from a given PDF content or text.
    
    Args:
        pdf_content: Text content from PDF or any text to search against
        pdf_name: Name/identifier for the input PDF
        
    Returns:
        Dict with nodes and edges representing the graph
    """
    log.info(f"Building PDF graph from: {pdf_name}")
    
    # Embed the input text
    try:
        vector = text_embed(pdf_content)
    except Exception as e:
        log.exception(f"Embedding failed for PDF content: {e}")
        return {"nodes": [], "edges": []}
    
    graph = Graph()
    
    # Create central node for the input PDF
    central_node = Node(
        id=pdf_name,
        type="pdf",
        label=pdf_name,
        metadata={"content_preview": pdf_content[:200] if pdf_content else ""}
    )
    graph.add_node(central_node)
    
    # Search for similar PDFs
    try:
        results_pdfs = retrieve_similar_pdfs(vector, n=5)
        log.info(f"Found {len(results_pdfs)} similar PDFs")
    except Exception as e:
        log.exception(f"PDF similarity search failed: {e}")
        results_pdfs = []
    
    # Add nodes and edges for similar PDFs
    for res in results_pdfs:
        node_id = res.get("node_id")
        score = res.get("score", 0)
        payload = res.get("payload", {})
        
        # Extract metadata
        path = payload.get("path", "")
        node_metadata = {
            "path": path,
            "source": "qdrant_pdfs"
        }
        
        node_label = node_id
        
        node = Node(
            id=node_id,
            type="pdf",
            label=node_label,
            metadata=node_metadata
        )
        graph.add_node(node)
        
        # Create edge with "similar_to" type (PDF similar to PDF)
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="references",
            score=score,
            evidence=f"Similarity score: {score:.3f}",
            provenance={"search_type": "pdf_similarity", "collection": "pdfs"}
        )
        graph.add_edge(edge)
    
    log.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    return normalize_graph(graph.as_json())


if __name__ == "__main__":
    # Example usage
    sample_text = "This paper discusses protein folding and molecular dynamics simulations"
    result = build_pdf_graph_from_pdf(sample_text, "test_pdf.pdf")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Edges: {len(result['edges'])}")
    for node in result['nodes']:
        print(f"  - {node['label']} ({node['type']})")
