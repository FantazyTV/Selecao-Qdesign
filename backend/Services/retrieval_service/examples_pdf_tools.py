"""
Simple examples demonstrating how to use each PDF graph tool individually.
Use this as a quick reference for integrating these tools into your code.
"""

# ============================================================================
# Example 1: Find Similar PDFs (PDF → PDF)
# ============================================================================

def example_pdf_to_pdf():
    """Find PDFs similar to a given text or PDF content."""
    from agent.high_level_tools.pdf_graph_from_pdf import build_pdf_graph_from_pdf
    
    # Input: Any text or PDF content
    research_text = """
    Machine learning approaches for predicting protein-ligand binding affinity.
    Deep learning models trained on structural databases achieve high accuracy.
    Computational methods for drug discovery and molecular docking.
    """
    
    # Build graph of 5 similar PDFs
    graph = build_pdf_graph_from_pdf(
        pdf_content=research_text,
        pdf_name="ml_protein_binding.pdf"
    )
    
    print("Similar PDFs found:")
    for node in graph['nodes']:
        if node['type'] == 'pdf' and node['id'] != 'ml_protein_binding.pdf':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example1_pdf_to_pdf_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


# ============================================================================
# Example 2: Find PDFs about a Protein (Protein → PDF)
# ============================================================================

def example_protein_to_pdf_by_id():
    """Find PDFs that discuss a specific protein (using PDB ID)."""
    from agent.high_level_tools.pdf_graph_from_protein import build_pdf_graph_from_protein
    
    # Input: PDB ID
    graph = build_pdf_graph_from_protein(
        protein_input="4HHB",  # Hemoglobin
        input_type="id"
    )
    
    print("PDFs discussing 4HHB (Hemoglobin):")
    for node in graph['nodes']:
        if node['type'] == 'pdf':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example2a_protein_to_pdf_by_id_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


def example_protein_to_pdf_by_name():
    """Find PDFs that discuss a specific protein (using protein name)."""
    from agent.high_level_tools.pdf_graph_from_protein import build_pdf_graph_from_protein
    
    # Input: Protein name
    graph = build_pdf_graph_from_protein(
        protein_input="insulin",
        input_type="name"
    )
    
    print("PDFs discussing insulin:")
    for node in graph['nodes']:
        if node['type'] == 'pdf':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example2b_protein_to_pdf_by_name_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


def example_protein_to_pdf_from_sequence():
    """Find PDFs related to a protein sequence."""
    from agent.high_level_tools.pdf_graph_from_protein import build_pdf_graph_from_protein
    
    # Input: Protein sequence
    sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    graph = build_pdf_graph_from_protein(
        protein_input=sequence,
        input_type="sequence"
    )
    
    print("PDFs related to this protein sequence:")
    for node in graph['nodes']:
        if node['type'] == 'pdf':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example2c_protein_to_pdf_from_sequence_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


# ============================================================================
# Example 3: Extract Proteins from PDF (PDF → Protein)
# ============================================================================

def example_pdf_to_proteins():
    """Extract proteins mentioned in a PDF."""
    from agent.high_level_tools.protein_graph_from_pdf import build_protein_graph_from_pdf
    
    # Input: PDF text content
    pdf_content = """
    Abstract: This research investigates the crystal structure of hemoglobin 
    (PDB: 4HHB) at 2.1 Å resolution. We compare it with myoglobin (PDB: 1MBO)
    and analyze the oxygen-binding mechanisms. 
    
    Additionally, we examined insulin (UniProt: P01308) for its role in 
    glucose metabolism and signaling pathways. The study reveals conserved 
    structural motifs across these proteins.
    
    Methods: We used X-ray crystallography and molecular dynamics simulations.
    Lysozyme was used as a control in our experiments.
    """
    
    graph = build_protein_graph_from_pdf(
        pdf_text=pdf_content,
        pdf_name="structural_biology_2024.pdf"
    )
    
    print("Proteins mentioned in the PDF:")
    for node in graph['nodes']:
        if node['type'] in ['pdb', 'sequence', 'annotation']:
            mentioned_as = node.get('metadata', {}).get('mentioned_as', node['label'])
            print(f"  - {mentioned_as} (ID: {node['id']}, Type: {node['type']})")

    # Write graph to JSON file
    import json
    with open("example3_pdf_to_proteins_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


# ============================================================================
# Example 4: Advanced Usage - Combining Multiple Tools
# ============================================================================

def example_combined_workflow():
    """
    Advanced example: Start with a protein, find related PDFs, 
    then find more PDFs similar to those.
    """
    from agent.high_level_tools.pdf_graph_from_protein import build_pdf_graph_from_protein
    from agent.high_level_tools.pdf_graph_from_pdf import build_pdf_graph_from_pdf
    from graph.graph_merge_utils import merge_graphs
    
    # Step 1: Find PDFs about hemoglobin
    print("\n🔍 Step 1: Finding PDFs about hemoglobin...")
    graph1 = build_pdf_graph_from_protein("hemoglobin", input_type="name")
    
    # Step 2: For each PDF found, find similar PDFs
    print("\n🔍 Step 2: Finding PDFs similar to those about hemoglobin...")
    graphs = [graph1]
    
    for node in graph1['nodes']:
        if node['type'] == 'pdf':
            # Get preview text from metadata
            preview = node.get('metadata', {}).get('chunk_text', '')
            if preview:
                similar_graph = build_pdf_graph_from_pdf(preview, node['id'])
                graphs.append(similar_graph)
    
    # Step 3: Merge all graphs
    print("\n🔗 Step 3: Merging graphs...")
    merged = merge_graphs(graphs)
    
    print(f"\n✅ Final graph: {len(merged['nodes'])} nodes, {len(merged['edges'])} edges")

    # Write merged graph to JSON file
    import json
    with open("example4_combined_workflow_graph.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    return merged


# ============================================================================
# Example 5: Find Related Images from PDF (PDF → Image)
# ============================================================================

def example_pdf_to_images():
    """Find images related to PDF content using CLIP embeddings."""
    from agent.high_level_tools.image_graph_from_pdf import build_image_graph_from_pdf
    
    # Input: PDF text content
    pdf_content = """
    Protein crystal structure visualization shows alpha helices in red 
    and beta sheets in yellow. The 3D molecular structure reveals the 
    active site pocket with bound ligand. Electron density maps confirm 
    the atomic coordinates at 2.0 Angstrom resolution.
    """
    
    graph = build_image_graph_from_pdf(
        pdf_content=pdf_content,
        pdf_name="structure_paper.pdf"
    )
    
    print("Related images found:")
    for node in graph['nodes']:
        if node['type'] == 'image':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example5_pdf_to_images_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


# ============================================================================
# Example 6: Find PDFs Related to Image (Image → PDF)
# ============================================================================

def example_image_to_pdfs():
    """Find PDFs related to an image using CLIP embeddings."""
    from agent.high_level_tools.pdf_graph_from_image import build_pdf_graph_from_image
    import os
    
    # Input: Path to an image file
    # Replace with actual image path from your Data/images folder
    # Example: "C:\\\\Users\\\\Moetez\\\\Desktop\\\\Vectors in Orbit\\\\_Ndhif\\\\Data\\\\images\\\\diagrams\\\\6vsb_structure.png"
    
    # For demonstration, using a placeholder
    image_path = "path/to/protein_structure.png"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"⚠️  Image not found: {image_path}")
        print("Please update the path to an actual image file.")
        return {"nodes": [], "edges": []}

    graph = build_pdf_graph_from_image(
        image_input=image_path,
        image_name="protein_structure_diagram"
    )

    print(f"PDFs related to image '{os.path.basename(image_path)}':")
    for node in graph['nodes']:
        if node['type'] == 'pdf':
            print(f"  - {node['label']}")

    # Write graph to JSON file
    import json
    with open("example6_image_to_pdfs_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return graph


# ============================================================================
# Main Runner
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PDF Graph Tools - Usage Examples")
    print("=" * 80)
    
    # Uncomment the examples you want to run:
    
    # Example 1: PDF → PDF
    print("\n\n📄 Example 1: Find Similar PDFs")
    print("-" * 80)
    example_pdf_to_pdf()
    
    # Example 2a: Protein → PDF (by ID)
    print("\n\n🧬 Example 2a: Find PDFs about a Protein (PDB ID)")
    print("-" * 80)
    example_protein_to_pdf_by_id()
    
    # Example 2b: Protein → PDF (by name)
    print("\n\n🧬 Example 2b: Find PDFs about a Protein (Name)")
    print("-" * 80)
    example_protein_to_pdf_by_name()
    
    # Example 2c: Protein → PDF (from sequence)
    # print("\n\n🧬 Example 2c: Find PDFs for a Protein Sequence")
    # print("-" * 80)
    # example_protein_to_pdf_from_sequence()
    
    # Example 3: PDF → Proteins
    print("\n\n📄 Example 3: Extract Proteins from PDF")
    print("-" * 80)
    example_pdf_to_proteins()
    
    # Example 4: Combined workflow
    # print("\n\n🔄 Example 4: Combined Workflow")
    # print("-" * 80)
    # example_combined_workflow()
    
    # Example 5: PDF → Images (NEW!)
    print("\n\n🖼️  Example 5: Find Images Related to PDF")
    print("-" * 80)
    example_pdf_to_images()
    
    # Example 6: Image → PDFs (NEW!)
    print("\n\n🖼️  Example 6: Find PDFs Related to Image")
    print("-" * 80)
    example_image_to_pdfs()
    
    print("\n\n✅ Examples completed!")
