import os
import logging
from agent.tools.embedder import clip_embed
from agent.tools.vector_search import retrieve_similar_images
from graph.graph_objects import Graph, Node, Edge

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("image_graph_from_pdf")

def build_image_graph_from_pdf(pdf_content: str, pdf_name: str = "input_pdf"):
    """
    Build a graph of similar images from a given PDF content or text using CLIP embeddings.
    
    Args:
        pdf_content: Text content from PDF or any text to search against
        pdf_name: Name/identifier for the input PDF
        
    Returns:
        Dict with nodes and edges representing the graph
    """
    log.info(f"Building image graph from PDF: {pdf_name}")
    
    # Embed the input text using CLIP
    try:
        vector = clip_embed(pdf_content[:200])  # CLIP has token limits, use preview
    except Exception as e:
        log.exception(f"CLIP embedding failed for PDF content: {e}")
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
    
    # Search for similar images
    try:
        results_images = retrieve_similar_images(vector, n=5)
        log.info(f"Found {len(results_images)} similar images")
    except Exception as e:
        log.exception(f"Image similarity search failed: {e}")
        results_images = []
    
    # Add nodes and edges for similar images
    for res in results_images:
        node_id = res.get("node_id")
        score = res.get("score", 0)
        payload = res.get("payload", {})
        
        # Extract metadata
        path = payload.get("path", "")
        node_metadata = {
            "path": path,
            "source": "qdrant_images"
        }
        
        node_label = node_id
        
        node = Node(
            id=node_id,
            type="image",
            label=node_label,
            metadata=node_metadata
        )
        graph.add_node(node)
        
        # Create edge with "related_to" type (PDF related to image)
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="related_to",
            score=score,
            evidence=f"CLIP similarity score: {score:.3f}",
            provenance={"search_type": "clip_similarity", "collection": "images"}
        )
        graph.add_edge(edge)
    
    log.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    return graph.as_json()


if __name__ == "__main__":
    # Example usage
    sample_text = "Protein crystal structure diagram showing alpha helices and beta sheets"
    result = build_image_graph_from_pdf(sample_text, "structure_paper.pdf")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Edges: {len(result['edges'])}")
    for node in result['nodes']:
        print(f"  - {node['label']} ({node['type']})")
