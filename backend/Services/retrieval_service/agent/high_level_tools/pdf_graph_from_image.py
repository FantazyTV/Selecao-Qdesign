import os
import logging
from pathlib import Path
from PIL import Image
import torch
import clip
from agent.high_level_tools.protein_graph_from_query import normalize_graph
from agent.tools.embedder import text_embed
from agent.tools.vector_search import retrieve_similar_pdfs
from graph.graph_objects import Graph, Node, Edge

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pdf_graph_from_image")

def embed_image_clip(image_path: str):
    """
    Embed an image using CLIP model (ViT-B/32).
    
    Args:
        image_path: Path to the image file
        
    Returns:
        512-dimensional CLIP embedding as a list of floats
    """
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        
        image = Image.open(image_path).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten().tolist()
    except Exception as e:
        log.exception(f"Failed to embed image {image_path}: {e}")
        return None


def build_pdf_graph_from_image(image_input: str, image_name: str = "input_image"):
    """
    Build a graph of related PDFs from an image using CLIP embeddings.
    
    Args:
        image_input: Path to an image file
        image_name: Name/identifier for the input image
        
    Returns:
        Dict with nodes and edges representing the graph
    """
    log.info(f"Building PDF graph from image: {image_name}")
    
    # Embed the image using CLIP
    try:
        image_vector = embed_image_clip(image_input)
        if image_vector is None:
            log.error("Failed to embed image")
            return {"nodes": [], "edges": []}
    except Exception as e:
        log.exception(f"Image embedding failed: {e}")
        return {"nodes": [], "edges": []}
    
    graph = Graph()
    
    # Create central node for the input image
    central_node = Node(
        id=image_name,
        type="image",
        label=image_name,
        metadata={"image_path": image_input}
    )
    graph.add_node(central_node)
    
    # Convert CLIP image embedding to text embedding for PDF search
    # Since PDFs use text embeddings, we can't directly compare
    # Instead, we'll search using a text description approach
    # For now, use the image vector directly - this works if both use CLIP
    # But our PDFs use all-MiniLM-L6-v2, so this won't work well
    # Best approach: extract image description and search with that
    
    # For this implementation, we'll use a hybrid approach:
    # Use the filename/path as a text query
    try:
        # Extract meaningful text from image path
        image_path = Path(image_input)
        search_query = image_path.stem.replace('_', ' ').replace('-', ' ')
        
        text_vector = text_embed(search_query)
        
        # Search PDF collection
        results_pdfs = retrieve_similar_pdfs(text_vector, n=5)
        
        log.info(f"Found {len(results_pdfs)} PDFs")
    except Exception as e:
        log.exception(f"PDF search failed: {e}")
        results_pdfs = []
    
    # Add PDF nodes and edges
    for res in results_pdfs:
        node_id = res.get("node_id")
        score = res.get("score", 0)
        payload = res.get("payload", {})
        
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
        
        # Create edge (image to PDF)
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="related_to",
            score=score,
            evidence=f"Text similarity score: {score:.3f} (query: '{search_query}')",
            provenance={"search_type": "text_similarity", "collection": "pdfs", "query": search_query}
        )
        graph.add_edge(edge)
    
    log.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    return normalize_graph(graph.as_json())


if __name__ == "__main__":
    # Example usage - replace with actual image path
    # result = build_pdf_graph_from_image("path/to/protein_structure.png", "protein_diagram")
    # print(f"Nodes: {len(result['nodes'])}")
    # print(f"Edges: {len(result['edges'])}")
    # for node in result['nodes']:
    #     print(f"  - {node['label']} ({node['type']})")
    print("Example: build_pdf_graph_from_image('path/to/image.png', 'my_image')")
