import os
import logging
import json
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from agent.high_level_tools.protein_graph_from_query import normalize_graph
from agent.tools.web_search import resolve_protein_name
from agent.tools.qdrant_retrieval import get_cif_by_pdb_id, get_fasta_by_uniprot_id
from graph.graph_objects import Graph, Node, Edge

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("protein_graph_from_pdf")

def extract_proteins_from_text(pdf_text: str) -> List[Dict[str, str]]:
    """
    Use LLM to extract protein names, IDs, and mentions from PDF text.
    
    Args:
        pdf_text: The text content from the PDF
        
    Returns:
        List of dicts with protein information: [{"name": "...", "id": "...", "context": "..."}]
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = f"""Extract all protein mentions from the following text. For each protein, identify:
1. The protein name (e.g., 'hemoglobin', 'insulin')
2. Any PDB ID (4-character codes like '4HHB', '1EZA')
3. Any UniProt ID (e.g., 'P69905', 'P01308')
4. A brief context of how it's mentioned

Return ONLY a JSON array with this exact format:
[
  {{"name": "hemoglobin", "pdb_id": "4HHB", "uniprot_id": "", "context": "structure determination"}},
  {{"name": "insulin", "pdb_id": "1EZA", "uniprot_id": "P01308", "context": "diabetes treatment"}}
]

If no proteins are found, return an empty array: []

Text to analyze:

{pdf_text[:3000]}

JSON array:"""

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            extra_body={},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        result_text = response.choices[0].message.content.strip()
        # Try to extract JSON from the response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```", 1)[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```", 1)[1].split("```", 1)[0].strip()
        proteins = json.loads(result_text)
        if not isinstance(proteins, list):
            log.warning("LLM response was not a list, returning empty")
            return []
        return proteins
    except Exception as e:
        log.exception(f"Error extracting proteins with LLM: {e}")
        return []


def build_protein_graph_from_pdf(pdf_text: str, pdf_name: str = "input_pdf"):
    """
    Build a graph of proteins mentioned in a PDF.
    
    Args:
        pdf_text: Text content from the PDF
        pdf_name: Name/identifier for the PDF
        
    Returns:
        Dict with nodes and edges representing the graph
    """
    log.info(f"Building protein graph from PDF: {pdf_name}")
    
    graph = Graph()
    
    # Create central PDF node
    central_node = Node(
        id=pdf_name,
        type="pdf",
        label=pdf_name,
        metadata={"content_preview": pdf_text[:200] if pdf_text else ""}
    )
    graph.add_node(central_node)
    
    # Extract proteins using LLM
    proteins = extract_proteins_from_text(pdf_text)
    log.info(f"Extracted {len(proteins)} protein mentions")
    
    if not proteins:
        log.warning("No proteins found in PDF")
        return graph.as_json()
    
    # Limit to top 5 proteins to keep graph manageable
    proteins = proteins[:5]
    
    # For each protein, try to resolve and add to graph
    for protein_info in proteins:
        protein_name = protein_info.get("name", "")
        pdb_id = protein_info.get("pdb_id", "")
        uniprot_id = protein_info.get("uniprot_id", "")
        context = protein_info.get("context", "")
        
        if not protein_name and not pdb_id and not uniprot_id:
            continue
        
        # Try to get protein data from Qdrant
        protein_node_id = None
        protein_metadata = {
            "mentioned_as": protein_name,
            "context": context
        }
        
        try:
            # Try PDB ID first
            if pdb_id:
                vec, payload = get_cif_by_pdb_id(pdb_id.upper())
                if payload:
                    protein_node_id = pdb_id.upper()
                    protein_metadata.update({
                        "pdb_id": pdb_id.upper(),
                        "source": "rcsb",
                        **payload
                    })
                    node_type = "pdb"
                    node_label = pdb_id.upper()
                    
            # Try UniProt ID if PDB didn't work
            if not protein_node_id and uniprot_id:
                vec, payload = get_fasta_by_uniprot_id(uniprot_id.upper())
                if payload:
                    protein_node_id = uniprot_id.upper()
                    protein_metadata.update({
                        "uniprot_id": uniprot_id.upper(),
                        "source": "uniprot",
                        **payload
                    })
                    node_type = "sequence"
                    node_label = uniprot_id.upper()
            
            # If still no match, try resolving by name
            if not protein_node_id and protein_name:
                resolved = resolve_protein_name(protein_name)
                
                if resolved.get("pdb_ids"):
                    pdb_id = resolved["pdb_ids"][0]
                    vec, payload = get_cif_by_pdb_id(pdb_id)
                    if payload:
                        protein_node_id = pdb_id
                        protein_metadata.update({
                            "pdb_id": pdb_id,
                            "source": "rcsb",
                            **payload
                        })
                        node_type = "pdb"
                        node_label = pdb_id
                        
                elif resolved.get("uniprot_ids"):
                    uniprot_id = resolved["uniprot_ids"][0]
                    vec, payload = get_fasta_by_uniprot_id(uniprot_id)
                    if payload:
                        protein_node_id = uniprot_id
                        protein_metadata.update({
                            "uniprot_id": uniprot_id,
                            "source": "uniprot",
                            **payload
                        })
                        node_type = "sequence"
                        node_label = uniprot_id
            
            # If we still don't have a node, create a generic one
            if not protein_node_id:
                protein_node_id = f"protein_{protein_name.replace(' ', '_')}"
                node_type = "annotation"
                node_label = protein_name
                protein_metadata["unresolved"] = True
            
            # Create protein node
            protein_node = Node(
                id=protein_node_id,
                type=node_type,
                label=node_label,
                metadata=protein_metadata
            )
            graph.add_node(protein_node)
            
            # Create edge from PDF to protein (PDF contains protein)
            edge = Edge(
                from_id=central_node.id,
                to_id=protein_node.id,
                type="mentions",
                score=1.0,
                evidence=f"Mentioned as '{protein_name}' in context: {context}",
                provenance={"extraction_method": "llm", "protein_mention": protein_name}
            )
            graph.add_edge(edge)
            
        except Exception as e:
            log.exception(f"Error processing protein {protein_name}: {e}")
            continue
    
    log.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    return normalize_graph(graph.as_json())


if __name__ == "__main__":
    # Example usage
    sample_pdf = """
    This study investigates the structure of hemoglobin (PDB: 4HHB) and its role in oxygen transport.
    We also compare it with myoglobin (PDB: 1MBO) and analyze insulin (UniProt: P01308) signaling.
    The crystal structure shows similarities to other heme proteins.
    """
    
    result = build_protein_graph_from_pdf(sample_pdf, "test_paper.pdf")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Edges: {len(result['edges'])}")
    for node in result['nodes']:
        print(f"  - {node['label']} ({node['type']})")
