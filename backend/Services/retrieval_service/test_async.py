"""
Updated test script for the asynchronous retrieval service.
"""

import httpx
import json
import time
from datetime import datetime

def test_async_endpoint():
    """Test the new async /process endpoint with polling."""
    
    # Prepare test data
    payload = {
        "name": "Protein Analysis Test",
        "mainObjective": "Analyze protein structures and sequences for research insights",
        "secondaryObjectives": [
            "Compare protein similarities",
            "Identify structural patterns"
        ],
        "constraints": [
            "Focus on high-confidence results",
            "Limit to biomedical domain"
        ],
        "notes": [
            "This is a test run",
            "Looking for comprehensive analysis"
        ],
        "description": "Test of the async retrieval service",
        "dataPool": [
            {
                "_id": "test_pdb_1",
                "type": "pdb",
                "name": "Test PDB Query",
                "description": "Testing PDB ID lookup",
                "content": "1EZA",  # PDB ID
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            },
            {
                "_id": "test_seq_1", 
                "type": "sequence",
                "name": "Test Sequence",
                "description": "Testing sequence analysis",
                "content": "MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPDWQNYTPGPGIRYPLKF",
                "addedBy": "test_user",
                "addedAt": datetime.now().isoformat(),
                "comments": []
            }
        ]
    }
    
    base_url = "http://localhost:8000/api/v1/retrieval"
    headers = {"Content-Type": "application/json"}
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=None)
    
    try:
        print("Testing async retrieval endpoint...")
        
        # Step 1: Submit job
        with httpx.Client(timeout=timeout) as client:
            print("Submitting job...")
            response = client.post(f"{base_url}/process", json=payload, headers=headers)
            
        print(f"Submit response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error submitting job: {response.text}")
            return
            
        job_data = response.json()
        job_id = job_data.get("jobId")
        if not job_id:
            print("No jobId received!")
            return
            
        print(f"Job submitted: {job_id}")
        
        # Step 2: Poll for completion
        max_polls = 24  # 2 minutes at 5s intervals
        poll_count = 0
        
        with httpx.Client(timeout=timeout) as client:
            while poll_count < max_polls:
                poll_count += 1
                print(f"Polling attempt {poll_count}/{max_polls}...")
                
                try:
                    status_response = client.get(f"{base_url}/status/{job_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Status: {status_data.get('status')}")
                        
                        if status_data.get("status") == "completed":
                            # Get the result
                            result_response = client.get(f"{base_url}/result/{job_id}")
                            if result_response.status_code == 200:
                                result = result_response.json()
                                print("\n--- Results ---")
                                print(f"Summary: {result.get('summary', 'N/A')}")
                                print(f"Graph nodes: {len(result.get('graph', {}).get('nodes', []))}")
                                print(f"Graph edges: {len(result.get('graph', {}).get('edges', []))}")
                                print(f"Notes: {result.get('notes', [])}")
                                
                                # Save result
                                with open("async_test_result.json", "w") as f:
                                    json.dump(result, f, indent=2)
                                print("Result saved to async_test_result.json")
                                return
                            else:
                                print(f"Error getting result: {result_response.text}")
                                return
                                
                        elif status_data.get("status") == "failed":
                            print(f"Job failed: {status_data.get('error')}")
                            return
                            
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"Polling error: {str(e)}")
                
                time.sleep(5)  # Wait 5 seconds before next poll
                
        print("Timed out waiting for job completion")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        url = "http://localhost:8000/api/v1/retrieval/health"
        with httpx.Client() as client:
            response = client.get(url)
        
        print(f"\n--- Health Check ---")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Health check failed: {str(e)}")

if __name__ == "__main__":
    print("Testing Asynchronous Retrieval Service")
    print("=" * 50)
    
    # Test health first
    test_health_endpoint()
    
    # Test async processing
    test_async_endpoint()