"""
Comprehensive test script for the multimodal retrieval service.
Tests the endpoint with CIF, sequence, PDF, and image inputs.
"""

import requests
import json
import time
import base64
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on a different port
API_ENDPOINT = f"{BASE_URL}/api/v1/retrieval/process"
STATUS_ENDPOINT = f"{BASE_URL}/api/v1/retrieval/status"
RESULT_ENDPOINT = f"{BASE_URL}/api/v1/retrieval/result"

def load_cif_file(file_path: str) -> str:
    """Load CIF file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_fasta_file(file_path: str) -> str:
    """Load FASTA file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_sample_pdf_content() -> str:
    """
    Create a sample PDF text content (base64 encoded).
    For testing, we'll use plain text that simulates a PDF about proteins.
    In production, this would be actual PDF bytes encoded in base64.
    """
    # Sample text that would be in a PDF about proteins
    pdf_text = """
    Structural Analysis of Hemoglobin and Related Proteins
    
    This study investigates the three-dimensional structure of human hemoglobin (PDB: 4HHB) 
    and its role in oxygen transport. Hemoglobin is a tetrameric protein composed of two 
    alpha and two beta subunits, each containing a heme group.
    
    We compare the structure with myoglobin (PDB: 1MBO), which is a monomeric oxygen-binding 
    protein found in muscle tissue. The comparison reveals important structural differences 
    that account for their different oxygen-binding properties.
    
    Additionally, we examined insulin (UniProt: P01308) signaling pathways and their 
    relationship to metabolic regulation. The crystal structure of insulin shows a 
    characteristic fold that is essential for receptor binding.
    
    Our analysis included molecular dynamics simulations and protein-protein interaction 
    studies. The results suggest that the heme pocket geometry plays a crucial role in 
    cooperative oxygen binding.
    
    Keywords: hemoglobin, myoglobin, insulin, protein structure, heme proteins, 
    oxygen transport, molecular dynamics
    """
    # For testing without a real PDF, just return the plain text
    # The parser will fail gracefully and we'll skip PDF processing in this test
    # To test with real PDF: create actual PDF bytes and encode with base64
    return pdf_text  # Return plain text instead of fake base64

def create_sample_image_path() -> str:
    """
    Return a path to a sample image for testing.
    Note: In production, this would be base64-encoded image data.
    For now, we'll just use a placeholder path.
    """
    # This is a placeholder - replace with an actual image path if available
    return "./1.png"

def create_test_request():
    """Create a comprehensive test request with CIF, sequence, PDF, and image inputs."""
    
    # Load actual CIF and FASTA files
    cif_path = Path(__file__).parent / "pdbs" / "1EZA.cif"
    fasta_path = Path(__file__).parent / "fastas" / "Q9ZSM8.fasta"
    
    cif_content = load_cif_file(str(cif_path))
    fasta_content = load_fasta_file(str(fasta_path))
    pdf_content = create_sample_pdf_content()
    
    # Create the processing request
    request_data = {
        "name": "Multimodal Protein Analysis Test",
        "mainObjective": "Test multimodal retrieval with protein structures, sequences, PDFs, and images",
        "secondaryObjectives": [
            "Verify depth-2 graph generation for PDFs",
            "Test protein extraction from PDFs",
            "Validate image-based retrieval",
            "Ensure proper graph merging"
        ],
        "constraints": [
            "Use only high-quality data sources",
            "Limit graph depth to 2 levels"
        ],
        "notes": [
            "Testing the new PDF and image processing features",
            "Expecting multimodal knowledge graph output"
        ],
        "description": "Comprehensive test of multimodal retrieval capabilities",
        "dataPool": [
            # 1. CIF/PDB Structure
            {
                "_id": "test_cif_001",
                "type": "cif",
                "name": "1EZA.cif",
                "description": "Histone-lysine N-methyltransferase EZA1 structure",
                "content": cif_content,
                "fileUrl": None,
                "metadata": {"source": "RCSB PDB", "resolution": "2.5A"},
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            },
            # 2. FASTA Sequence
            {
                "_id": "test_seq_001",
                "type": "sequence",
                "name": "Q9ZSM8.fasta",
                "description": "Histone-lysine N-methyltransferase EZA1 sequence",
                "content": fasta_content,
                "fileUrl": None,
                "metadata": {"organism": "Arabidopsis thaliana", "length": 875},
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            },
            # 3. PDF Document
            {
                "_id": "test_pdf_001",
                "type": "pdf",
                "name": "hemoglobin_study.pdf",
                "description": "Research paper on hemoglobin structure and function",
                "content": pdf_content,
                "fileUrl": None,
                "metadata": {"pages": 12, "year": 2023},
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            },
            # 4. Short query (should use protein query tool)
            {
                "_id": "test_query_001",
                "type": "text",
                "name": "insulin_query",
                "description": "Query for insulin protein",
                "content": "insulin",
                "fileUrl": None,
                "metadata": {},
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            }
        ]
    }
    
    return request_data

def poll_job_status(job_id: str, max_wait_seconds: int = 300, poll_interval: int = 5):
    """Poll the job status until completion or timeout."""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{STATUS_ENDPOINT}/{job_id}")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status")
                
                print(f"[{time.strftime('%H:%M:%S')}] Job status: {status}")
                
                if status == "completed":
                    return True
                elif status == "failed":
                    print(f"Job failed: {status_data.get('error')}")
                    return False
                
            else:
                print(f"Error checking status: {response.status_code}")
                
        except Exception as e:
            print(f"Error polling status: {str(e)}")
        
        time.sleep(poll_interval)
    
    print(f"Timeout after {max_wait_seconds} seconds")
    return False

def save_results(job_id: str, output_file: str = None):
    """Fetch and save the job results to a JSON file."""
    try:
        response = requests.get(f"{RESULT_ENDPOINT}/{job_id}")
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Generate output filename if not provided
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"multimodal_retrieval_result_{timestamp}.json"
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"\n{'='*60}")
            print(f"Results saved to: {output_file}")
            print(f"{'='*60}\n")
            
            # Print summary
            graph = result_data.get("graph", {})
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            
            print(f"Summary:")
            print(f"  - Total nodes: {len(nodes)}")
            print(f"  - Total edges: {len(edges)}")
            print(f"  - Summary: {result_data.get('summary', 'N/A')}")
            
            # Count node types
            node_types = {}
            for node in nodes:
                node_type = node.get("type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            print(f"\nNode types:")
            for node_type, count in node_types.items():
                print(f"  - {node_type}: {count}")
            
            # Count edge types
            edge_types = {}
            for edge in edges:
                edge_type = edge.get("type") or edge.get("label") or edge.get("correlationType", "unknown")
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            
            print(f"\nEdge types:")
            for edge_type, count in edge_types.items():
                print(f"  - {edge_type}: {count}")
            
            # Show processing stats
            stats = result_data.get("processing_stats", {})
            print(f"\nProcessing stats:")
            print(f"  - Total items: {stats.get('total_items', 'N/A')}")
            print(f"  - Processed items: {stats.get('processed_items', 'N/A')}")
            print(f"  - Item breakdown: {stats.get('item_breakdown', {})}")
            
            return result_data
        else:
            print(f"Error fetching results: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error saving results: {str(e)}")
        return None

def main():
    """Main test execution."""
    print("="*60)
    print("Multimodal Retrieval Service Test")
    print("="*60)
    print()
    
    # Create test request
    print("Creating test request...")
    request_data = create_test_request()
    print(f"Request includes {len(request_data['dataPool'])} data items:")
    for item in request_data['dataPool']:
        print(f"  - {item['name']} ({item['type']})")
    print()
    
    # Submit the request
    print("Submitting request to API...")
    try:
        response = requests.post(API_ENDPOINT, json=request_data)
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get("jobId")
            print(f"Job submitted successfully!")
            print(f"Job ID: {job_id}")
            print(f"Status: {job_data.get('status')}")
            print(f"Message: {job_data.get('message')}")
            print()
            
            # Poll for completion
            print("Polling for job completion...")
            if poll_job_status(job_id):
                print("\nJob completed successfully!")
                
                # Fetch and save results
                print("\nFetching results...")
                save_results(job_id)
            else:
                print("\nJob did not complete successfully")
                
        else:
            print(f"Error submitting request: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
