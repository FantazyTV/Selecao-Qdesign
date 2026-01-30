"""
Test script for the three new PDF-related high-level tools:
1. pdf_graph_from_pdf: Find similar PDFs to a given PDF/text
2. pdf_graph_from_protein: Find PDFs related to a protein
3. protein_graph_from_pdf: Extract proteins mentioned in a PDF

Run this script to test all three tools.
"""

import json
import sys
from agent.high_level_tools.pdf_graph_from_pdf import build_pdf_graph_from_pdf
from agent.high_level_tools.pdf_graph_from_protein import build_pdf_graph_from_protein
from agent.high_level_tools.protein_graph_from_pdf import build_protein_graph_from_pdf


def print_graph_summary(graph_data, title):
    """Pretty print a graph summary."""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)
    
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    print(f"\n📊 Summary: {len(nodes)} nodes, {len(edges)} edges\n")
    
    if nodes:
        print("🔹 Nodes:")
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_label = node.get("label", "unnamed")
            node_id = node.get("id", "no-id")
            metadata = node.get("metadata", {})
            
            # Extract key metadata
            info = []
            if metadata.get("pdb_id"):
                info.append(f"PDB: {metadata['pdb_id']}")
            if metadata.get("uniprot_id"):
                info.append(f"UniProt: {metadata['uniprot_id']}")
            if metadata.get("file_name"):
                info.append(f"File: {metadata['file_name']}")
            
            info_str = f" ({', '.join(info)})" if info else ""
            print(f"  • [{node_type}] {node_label}{info_str}")
    
    if edges:
        print("\n🔗 Edges:")
        for edge in edges:
            from_id = edge.get("from_id", "?")
            to_id = edge.get("to_id", "?")
            edge_type = edge.get("type", "unknown")
            score = edge.get("score", 0)
            evidence = edge.get("evidence", [])
            
            evidence_str = f" | {evidence[0][:50]}..." if evidence else ""
            print(f"  • {from_id} --[{edge_type}, score={score:.3f}]--> {to_id}{evidence_str}")
    
    print("\n" + "=" * 80)


def test_pdf_from_pdf():
    """Test 1: Build PDF graph from text/PDF content."""
    print("\n\n🧪 TEST 1: PDF Graph from PDF/Text")
    print("Finding similar PDFs to a sample research text...")
    
    sample_text = """
    This paper investigates protein folding mechanisms and molecular dynamics simulations 
    of biomolecular systems. We focus on computational methods for predicting protein 
    structure and stability. Machine learning approaches are used to analyze large-scale 
    structural databases and identify folding patterns.
    """
    
    result = build_pdf_graph_from_pdf(sample_text, pdf_name="sample_research.pdf")
    print_graph_summary(result, "TEST 1: Similar PDFs")
    
    return result


def test_pdf_from_protein():
    """Test 2: Build PDF graph from protein."""
    print("\n\n🧪 TEST 2: PDF Graph from Protein")
    print("Finding PDFs related to hemoglobin (4HHB)...")
    
    # Test with PDB ID
    result1 = build_pdf_graph_from_protein("4HHB", input_type="id")
    print_graph_summary(result1, "TEST 2a: PDFs about Hemoglobin (PDB ID)")
    
    # Test with protein name
    print("\n\nTrying with protein name 'insulin'...")
    result2 = build_pdf_graph_from_protein("insulin", input_type="name")
    print_graph_summary(result2, "TEST 2b: PDFs about Insulin (Name)")
    
    return result1


def test_protein_from_pdf():
    """Test 3: Extract proteins from PDF."""
    print("\n\n🧪 TEST 3: Protein Graph from PDF")
    print("Extracting proteins mentioned in a sample paper...")
    
    sample_pdf = """
    Abstract: This study examines the molecular mechanisms of hemoglobin (PDB: 4HHB) 
    in oxygen transport and compares its structure with myoglobin (PDB: 1MBO). 
    We used X-ray crystallography to determine the structure at 2.1 Å resolution.
    
    The research also investigates insulin (UniProt: P01308) signaling pathways 
    and their role in glucose metabolism. Structural comparisons reveal conserved 
    regions across heme-binding proteins. 
    
    Our findings show that lysozyme demonstrates similar catalytic mechanisms.
    The protein kinase A regulatory subunit (PKA-R) was also analyzed for 
    conformational changes upon cAMP binding.
    """
    
    result = build_protein_graph_from_pdf(sample_pdf, pdf_name="structural_biology_paper.pdf")
    print_graph_summary(result, "TEST 3: Proteins in PDF")
    
    return result


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("Testing PDF-Related High-Level Tools")
    print("🚀" * 40)
    
    print("\nThis script tests three new graph-building tools:")
    print("1️⃣  pdf_graph_from_pdf: Find PDFs similar to input text/PDF")
    print("2️⃣  pdf_graph_from_protein: Find PDFs related to a protein")
    print("3️⃣  protein_graph_from_pdf: Extract proteins mentioned in PDF")
    
    try:
        # Run tests
        result1 = test_pdf_from_pdf()
        result2 = test_pdf_from_protein()
        result3 = test_protein_from_pdf()
        
        print("\n\n✅ All tests completed successfully!")
        print("\nℹ️  Note: Results depend on data available in Qdrant collections:")
        print("   - 'pdfs' collection: PDF documents")
        print("   - 'qdesign_text' collection: Text chunks from research papers")
        print("   - 'structures' collection: PDB structures")
        print("   - 'uniprot_sequences' collection: UniProt protein sequences")
        
        # Save results to file
        output = {
            "test1_pdf_from_pdf": result1,
            "test2_pdf_from_protein": result2,
            "test3_protein_from_pdf": result3
        }
        
        with open("test_pdf_tools_output.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to: test_pdf_tools_output.json")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
