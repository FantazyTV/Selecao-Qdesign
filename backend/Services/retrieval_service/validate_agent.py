"""
Quick validation script to test the updated agent without running the full server.
Tests individual components and ensures backward compatibility.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.agent import MultiModalRetrievalAgent
from utils.models import ProcessingRequest, DataPoolItem
from datetime import datetime


def test_backward_compatibility():
    """Test that existing CIF and sequence processing still works."""
    print("="*60)
    print("Testing Backward Compatibility")
    print("="*60)
    
    agent = MultiModalRetrievalAgent()
    
    # Test 1: CIF/PDB short query
    print("\n1. Testing short PDB query...")
    request = ProcessingRequest(
        name="Test PDB Query",
        mainObjective="Test protein query",
        dataPool=[
            DataPoolItem(
                _id="test1",
                type="pdb",
                name="hemoglobin",
                content="4HHB",
                addedBy="test",
                addedAt=datetime.now()
            )
        ]
    )
    
    try:
        result = agent.process_data_pool_request(request)
        graph = result.graph
        print(f"   ✓ Result: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Test 2: Sequence processing
    print("\n2. Testing sequence processing...")
    request = ProcessingRequest(
        name="Test Sequence",
        mainObjective="Test sequence processing",
        dataPool=[
            DataPoolItem(
                _id="test2",
                type="sequence",
                name="test_seq",
                content="MKLFFKRMVIAAALLASSATAQADYYDYADSALDKAADKAAAARKAVASNAKDDAAKAA",
                addedBy="test",
                addedAt=datetime.now()
            )
        ]
    )
    
    try:
        result = agent.process_data_pool_request(request)
        graph = result.graph
        print(f"   ✓ Result: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    return True


def test_new_pdf_functionality():
    """Test the new PDF processing functionality."""
    print("\n" + "="*60)
    print("Testing New PDF Functionality")
    print("="*60)
    
    agent = MultiModalRetrievalAgent()
    
    # Create a simple PDF test (text content, base64 encoded)
    import base64
    pdf_text = """
    Hemoglobin (PDB: 4HHB) is a crucial oxygen transport protein.
    This study compares it with myoglobin (PDB: 1MBO).
    """
    pdf_content = base64.b64encode(pdf_text.encode()).decode()
    
    print("\n1. Testing PDF processing...")
    request = ProcessingRequest(
        name="Test PDF",
        mainObjective="Test PDF depth-2 processing",
        dataPool=[
            DataPoolItem(
                _id="test_pdf",
                type="pdf",
                name="test_paper.pdf",
                content=pdf_content,
                addedBy="test",
                addedAt=datetime.now()
            )
        ]
    )
    
    try:
        result = agent.process_data_pool_request(request)
        graph = result.graph
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        print(f"   ✓ Result: {len(nodes)} nodes, {len(edges)} edges")
        
        # Check for PDF node
        pdf_nodes = [n for n in nodes if n.get('type') == 'pdf']
        print(f"   ✓ PDF nodes: {len(pdf_nodes)}")
        
        # Check for protein nodes (from PDF extraction)
        protein_nodes = [n for n in nodes if n.get('type') in ['pdb', 'sequence']]
        print(f"   ✓ Protein nodes (extracted): {len(protein_nodes)}")
        
        # Check for mentions edges
        mention_edges = [e for e in edges if e.get('type') == 'mentions']
        print(f"   ✓ Mention edges: {len(mention_edges)}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_inputs():
    """Test processing multiple input types together."""
    print("\n" + "="*60)
    print("Testing Mixed Input Types")
    print("="*60)
    
    agent = MultiModalRetrievalAgent()
    
    import base64
    pdf_text = "Study of insulin (UniProt: P01308) structure."
    pdf_content = base64.b64encode(pdf_text.encode()).decode()
    
    request = ProcessingRequest(
        name="Test Mixed",
        mainObjective="Test multiple input types",
        dataPool=[
            DataPoolItem(
                _id="test1",
                type="text",
                name="query",
                content="insulin",
                addedBy="test",
                addedAt=datetime.now()
            ),
            DataPoolItem(
                _id="test2",
                type="pdf",
                name="paper.pdf",
                content=pdf_content,
                addedBy="test",
                addedAt=datetime.now()
            ),
            DataPoolItem(
                _id="test3",
                type="sequence",
                name="seq",
                content="MKLFFKRMVIAAALLASSATAQADYYDYADSALDKAADKAAAARKAVASNAKDDAAKAA",
                addedBy="test",
                addedAt=datetime.now()
            )
        ]
    )
    
    try:
        result = agent.process_data_pool_request(request)
        graph = result.graph
        stats = result.processing_stats
        
        print(f"   ✓ Total nodes: {len(graph.get('nodes', []))}")
        print(f"   ✓ Total edges: {len(graph.get('edges', []))}")
        print(f"   ✓ Processed: {stats.get('processed_items')}/{stats.get('total_items')}")
        print(f"   ✓ Breakdown: {stats.get('item_breakdown')}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("Agent Validation Suite")
    print("="*60)
    
    results = []
    
    # Test backward compatibility
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Test new PDF functionality
    results.append(("PDF Processing", test_new_pdf_functionality()))
    
    # Test mixed inputs
    results.append(("Mixed Inputs", test_mixed_inputs()))
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
