import os
import logging
from agent.tools.embedder import text_embed
from agent.tools.vector_search import retrieve_similar_pdfs
from agent.tools.web_search import resolve_protein_name
from agent.tools.qdrant_retrieval import get_cif_by_pdb_id, get_fasta_by_uniprot_id
from agent.high_level_tools.protein_graph_from_query import extract_sequence_from_cif, safe_embed
from graph.graph_objects import Graph, Node, Edge

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pdf_graph_from_protein")

def build_pdf_graph_from_protein(protein_input: str, input_type: str = "auto"):
    """
    Build a graph of related PDFs from a protein (CIF, sequence, or name/ID).
    
    Args:
        protein_input: Can be a PDB ID, UniProt ID, protein name, CIF content, or sequence
        input_type: "auto", "cif", "sequence", "name", or "id"
        
    Returns:
        Dict with nodes and edges representing the graph
    """
    log.info(f"Building PDF graph from protein: {protein_input[:50]}... (type: {input_type})")
    
    graph = Graph()
    protein_name = None
    protein_id = None
    
    # Determine input type and extract sequence/vector
    if input_type == "auto":
        # Auto-detect based on content
        if len(protein_input.strip()) <= 10 and not "\n" in protein_input:
            input_type = "id"
        elif "data_" in protein_input or "_entity_poly" in protein_input:
            input_type = "cif"
        elif all(c in "ACDEFGHIKLMNPQRSTVWYUO \n" for c in protein_input.upper()):
            input_type = "sequence"
        else:
            input_type = "name"
    
    try:
        if input_type == "cif":
            # Extract sequence from CIF
            sequence = extract_sequence_from_cif(protein_input)
            if sequence:
                protein_name = "CIF_structure"
                protein_id = "cif_input"
            else:
                log.error("Could not extract sequence from CIF")
                return {"nodes": [], "edges": []}
                
        elif input_type == "sequence":
            # Use the sequence directly
            protein_name = "Protein_sequence"
            protein_id = "sequence_input"
            
        elif input_type in ["id", "name"]:
            # Resolve protein name/ID to get actual protein data
            resolved = resolve_protein_name(protein_input.strip())
            
            # Try PDB first
            pdb_ids = resolved.get("pdb_ids", [])
            uniprot_ids = resolved.get("uniprot_ids", [])
            
            if pdb_ids:
                protein_id = pdb_ids[0].upper()
                protein_name = protein_id
                        
            elif uniprot_ids:
                protein_id = uniprot_ids[0].upper()
                protein_name = protein_id
            else:
                # Use input as name directly
                protein_name = protein_input.strip()
                protein_id = protein_input.strip()
            
            if not protein_name:
                log.error(f"Could not resolve protein: {protein_input}")
                return {"nodes": [], "edges": []}
                
    except Exception as e:
        log.exception(f"Error processing protein input: {e}")
        return {"nodes": [], "edges": []}
    
    # Create search query using protein name/ID
    search_query = protein_name or protein_id or protein_input.strip()[:50]
    
    # Create central protein node
    central_node = Node(
        id=protein_id or "protein_input",
        type="pdb" if protein_id and len(protein_id) == 4 else "sequence",
        label=protein_name or protein_input[:20],
        metadata={
            "protein_id": protein_id,
            "search_query": search_query
        }
    )
    graph.add_node(central_node)
    
    # Search for related PDFs using text embedding of the protein name/ID
    try:
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
        
        # Create edge (protein to PDF)
        edge = Edge(
            from_id=central_node.id,
            to_id=node.id,
            type="related_to",
            score=score,
            evidence=f"Text similarity score: {score:.3f}",
            provenance={"search_type": "text_similarity", "collection": "pdfs", "query": search_query}
        )
        graph.add_edge(edge)
    
    log.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    return graph.as_json()


if __name__ == "__main__":
    # Example usage
    result = build_pdf_graph_from_protein("hemoglobin", input_type="name")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Edges: {len(result['edges'])}")
    for node in result['nodes']:
        print(f"  - {node['label']} ({node['type']})")
