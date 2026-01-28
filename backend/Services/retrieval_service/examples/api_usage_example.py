"""
Example usage of the Multi-Modal Retrieval Service API.
This demonstrates how to submit a data pool for analysis and receive graph results.
"""

import json
import requests
from datetime import datetime
import time

# Example data pool request structure
example_request = {
    "dataPool": [
        {
            "_id": "1c3b5915-69fa-4c07-9732-6ca458f1b746",
            "type": "pdf", 
            "name": "Moetez Fradi AI.pdf",
            "description": "",
            "content": "JVBERi0xLjQKJfbk/N8KMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovVmVyc2lvbiAvMS...",  # Base64 encoded PDF
            "addedBy": "69738fb00ad61483087611b1",
            "addedAt": "2026-01-26T15:58:44.470+00:00",
            "comments": []
        },
        {
            "_id": "2f3ca543-6df4-4999-bb6a-35d6c37ed1e1",
            "type": "text",
            "name": "cheat.txt", 
            "description": "",
            "content": "GIT_AUTHOR_DATE=\"2026-01-18T12:00:00\" \nGIT_COMMITTER_DATE=\"2026-01-18T12:00:00\"",
            "addedBy": "697390b90ad61483087611c3",
            "addedAt": "2026-01-26T15:58:50.056+00:00",
            "comments": []
        },
        {
            "_id": "7e9b3123-4a56-477e-b087-ef23e5fb342d",
            "type": "pdb",
            "name": "4hhb.cif",
            "description": "",
            "content": "data_4HHB\n# \n_entry.id   4HHB \n# \n_audit_conform.dict_name       mmcif...",
            "addedBy": "69738fb00ad61483087611b1",
            "addedAt": "2026-01-26T15:59:45.365+00:00",
            "comments": []
        },
        {
            "_id": "6e86001c-2787-43f9-94ef-ca81d2ac4215",
            "type": "text",
            "name": "Objective",
            "description": "we need to make hemoglobin more fast",
            "content": "",
            "addedBy": "69738fb00ad61483087611b1", 
            "addedAt": "2026-01-26T16:34:11.627+00:00",
            "comments": []
        },
        {
            "_id": "60caf432-54f6-4bd5-bfe2-018585f6fc47",
            "type": "text",
            "name": "report.txt",
            "description": "",
            "content": "def _export_yolo_ultralytics_segmentation(dst_file, temp_dir, instance...",
            "addedBy": "697390b90ad61483087611c3",
            "addedAt": "2026-01-26T17:17:40.491+00:00",
            "comments": []
        }
    ],
    "mainObjective": "Increasing binding affinity of hemoglobin",
    "secondaryObjectives": [
        "Improving thermal or chemical stability",
        "Reducing aggregation or toxicity"
    ],
    "Notes": [],
    "Constraints": []
}

class RetrievalServiceClient:
    """Client for interacting with the Multi-Modal Retrieval Service."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def health_check(self):
        """Check if the service is healthy."""
        response = requests.get(f"{self.base_url}/api/v1/retrieval/health")
        return response.json()
    
    def analyze_sync(self, data_pool_request: dict):
        """Submit a synchronous analysis request."""
        response = requests.post(
            f"{self.base_url}/api/v1/retrieval/analyze",
            json=data_pool_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def analyze_async(self, data_pool_request: dict):
        """Submit an asynchronous analysis request."""
        response = requests.post(
            f"{self.base_url}/api/v1/retrieval/analyze-async",
            json=data_pool_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_job_status(self, job_id: str):
        """Get the status of an async job."""
        response = requests.get(f"{self.base_url}/api/v1/retrieval/status/{job_id}")
        return response.json()
    
    def get_job_result(self, job_id: str):
        """Get the result of a completed async job."""
        response = requests.get(f"{self.base_url}/api/v1/retrieval/result/{job_id}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 202:
            return {"status": "still_processing"}
        else:
            raise Exception(f"Failed to get result: {response.status_code} - {response.text}")
    
    def parse_file(self, content: str, file_type: str, file_name: str = ""):
        """Parse a single file."""
        response = requests.post(
            f"{self.base_url}/api/v1/retrieval/parse-file",
            params={
                "content": content,
                "file_type": file_type,
                "file_name": file_name
            }
        )
        return response.json()
    
    def extract_entities(self, content: str, domain: str = "biomedical"):
        """Extract entities from text content."""
        response = requests.post(
            f"{self.base_url}/api/v1/retrieval/extract-entities",
            params={
                "content": content,
                "domain": domain
            }
        )
        return response.json()

def example_sync_usage():
    """Example of synchronous API usage."""
    print("=== Synchronous Analysis Example ===")
    
    client = RetrievalServiceClient()
    
    # Health check
    try:
        health = client.health_check()
        print(f"Service health: {health}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Submit analysis request
    try:
        print("Submitting analysis request...")
        result = client.analyze_sync(example_request)
        
        print(f"Analysis completed!")
        print(f"Summary: {result.get('summary', 'No summary available')}")
        print(f"Number of graphs: {len(result.get('graphs', []))}")
        
        if result.get('graphs'):
            graph = result['graphs'][0]
            print(f"Graph has {len(graph.get('nodes', []))} nodes and {len(graph.get('edges', []))} edges")
        
        print(f"Processing stats: {json.dumps(result.get('processing_stats', {}), indent=2)}")
        print(f"Recommendations: {result.get('recommendations', [])}")
        
    except Exception as e:
        print(f"Sync analysis failed: {e}")

def example_async_usage():
    """Example of asynchronous API usage."""
    print("\\n=== Asynchronous Analysis Example ===")
    
    client = RetrievalServiceClient()
    
    try:
        # Submit async request
        print("Submitting async analysis request...")
        job_info = client.analyze_async(example_request)
        job_id = job_info["job_id"]
        print(f"Job started: {job_id}")
        
        # Poll for completion
        while True:
            status = client.get_job_status(job_id)
            print(f"Job status: {status.get('status')}")
            
            if status.get("status") == "completed":
                # Get results
                result = client.get_job_result(job_id)
                print("Analysis completed!")
                print(f"Summary: {result.get('summary', 'No summary available')}")
                break
            elif status.get("status") == "failed":
                print(f"Job failed: {status.get('error')}")
                break
            else:
                time.sleep(5)  # Wait 5 seconds before checking again
                
    except Exception as e:
        print(f"Async analysis failed: {e}")

def example_utility_usage():
    """Example of utility endpoint usage."""
    print("\\n=== Utility Endpoints Example ===")
    
    client = RetrievalServiceClient()
    
    # Parse a sample text file
    try:
        sample_text = "Hemoglobin is a protein that carries oxygen in red blood cells."
        parsed = client.parse_file(sample_text, "text", "sample.txt")
        print(f"Parsed text file: {json.dumps(parsed, indent=2)}")
    except Exception as e:
        print(f"File parsing failed: {e}")
    
    # Extract entities
    try:
        entities = client.extract_entities(sample_text)
        print(f"Extracted entities: {json.dumps(entities, indent=2)}")
    except Exception as e:
        print(f"Entity extraction failed: {e}")

if __name__ == "__main__":
    print("Multi-Modal Retrieval Service API Examples")
    print("==========================================")
    
    # Run examples
    example_sync_usage()
    # example_async_usage()  # Uncomment to test async
    # example_utility_usage()  # Uncomment to test utilities
    
    print("\\nExamples completed!")