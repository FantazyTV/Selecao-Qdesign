#!/usr/bin/env python3
"""
Test script for QDesign Knowledge Service API endpoints
Tests all discovery, retrieval, curation, and finalization endpoints
"""

import requests
import json
import sys
import time
from pathlib import Path

# Add services to path
services_dir = Path(__file__).parent.parent
sys.path.insert(0, str(services_dir))

# Configuration
API_ROOT_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{API_ROOT_URL}/api/v1/knowledge"
TIMEOUT = 30

class Colors:
    """ANSI color codes for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Print an error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    """Print an info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")

def print_json(data, indent=2):
    """Print JSON data nicely"""
    print(json.dumps(data, indent=indent))

def test_health_check():
    """Test the health check endpoint"""
    print_header("Health Check")
    try:
        response = requests.get(f"{API_ROOT_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("API is healthy")
            print_json(response.json())
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to connect to API: {e}")
        return False

def test_discovery_endpoints():
    """Test discovery endpoints"""
    print_header("Discovery Service Endpoints")
    
    # Test data
    project_description = """
    Protein engineering for antibody optimization with improved binding affinity 
    to SARS-CoV-2 spike protein and better thermal stability for storage.
    """
    
    endpoints = [
        {
            "method": "POST",
            "path": "/discover",
            "name": "Discover Resources",
            "data": {
                "project_id": "test-project-001",
                "project_description": project_description,
                "top_k": 10,
                "min_relevance": 0.3
            }
        }
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            print(f"\n{Colors.BOLD}Testing: {endpoint['name']}{Colors.RESET}")
            print(f"Endpoint: {endpoint['method']} {endpoint['path']}")
            
            url = f"{API_BASE_URL}{endpoint['path']}"
            
            if endpoint['method'] == "POST":
                response = requests.post(url, json=endpoint['data'], timeout=TIMEOUT)
            else:
                response = requests.get(url, params=endpoint['data'], timeout=TIMEOUT)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print_success(f"{endpoint['name']} successful")
                data = response.json()
                
                # Show summary based on response type
                if isinstance(data, dict):
                    if "total_resources" in data:
                        print_info(f"Found {data.get('total_resources', 0)} resources")
                    elif "knowledge_base_id" in data:
                        print_info(f"Knowledge base: {data.get('knowledge_base_id')}")
                    elif "error" in data:
                        print_error(f"API Error: {data['error']}")
                    else:
                        print(f"Response: {list(data.keys())[:5]}")
                
            else:
                print_error(f"Failed with status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                all_ok = False
        except Exception as e:
            print_error(f"Exception: {e}")
            all_ok = False

    return all_ok

def test_curation_endpoints(kb_id: str) -> bool:
    """Test curation endpoints"""
    print_header("Curation Service Endpoints")
    if not kb_id:
        print_info("Skipping curation tests: no knowledge base id")
        return False

    try:
        print(f"{Colors.BOLD}Testing: Add Custom Resource{Colors.RESET}")

        resource_data = {
            "knowledge_base_id": kb_id,
            "resource_type": "paper",
            "title": "Antibody Engineering for COVID-19",
            "url": "https://arxiv.org/abs/2212.12345",
            "metadata": {"source": "arxiv"},
            "comment": "Seed paper for testing"
        }

        response = requests.post(
            f"{API_BASE_URL}/resources/custom",
            json=resource_data,
            timeout=TIMEOUT
        )

        print(f"Status Code: {response.status_code}")

        resource_id = None
        if response.status_code in [200, 201]:
            print_success("Custom resource added")
            data = response.json()
            resource_id = data.get("id")
        else:
            print_error(f"Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

        if resource_id:
            print(f"\n{Colors.BOLD}Testing: Annotate Resource{Colors.RESET}")
            annotate_data = {
                "comment": "Looks relevant for stability optimization",
                "tags": ["stability", "antibody"],
                "confidence_score": 0.8
            }
            response = requests.post(
                f"{API_BASE_URL}/resources/{resource_id}/annotate",
                json=annotate_data,
                timeout=TIMEOUT
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code in [200, 201]:
                print_success("Annotation added")
            else:
                print_error(f"Failed with status {response.status_code}")
                print(f"Response: {response.text[:200]}")

        print(f"\n{Colors.BOLD}Testing: Reorder Resources{Colors.RESET}")
        reorder_data = {
            "resource_ids": [resource_id] if resource_id else []
        }
        response = requests.post(
            f"{API_BASE_URL}/{kb_id}/reorder",
            json=reorder_data,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            print_success("Reordered resources")
        else:
            print_error(f"Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

        return True

    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_retrieval_endpoints(kb_id: str) -> bool:
    """Test retrieval endpoints"""
    print_header("Retrieval Service Endpoints")
    if not kb_id:
        print_info("Skipping retrieval tests: no knowledge base id")
        return False

    try:
        print(f"{Colors.BOLD}Testing: Get Knowledge Base{Colors.RESET}")

        response = requests.get(
            f"{API_BASE_URL}/{kb_id}",
            timeout=TIMEOUT
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print_success("Knowledge base retrieved")
            kb = response.json()
            if isinstance(kb, dict):
                resources = kb.get("resources", []) if isinstance(kb.get("resources"), list) else []
                print_info(f"Resources: {len(resources)}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_finalization_endpoints(kb_id: str) -> bool:
    """Test finalization endpoints"""
    print_header("Finalization Service Endpoints")
    if not kb_id:
        print_info("Skipping finalization tests: no knowledge base id")
        return False

    try:
        print(f"{Colors.BOLD}Testing: Finalize Knowledge Base{Colors.RESET}")

        response = requests.post(
            f"{API_BASE_URL}/{kb_id}/finalize",
            timeout=TIMEOUT
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code in [200, 201]:
            print_success("Knowledge base finalized")
        else:
            print_error(f"Failed with status {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:200]}")
            return False

        print(f"\n{Colors.BOLD}Testing: Export Knowledge Base{Colors.RESET}")
        response = requests.get(
            f"{API_BASE_URL}/{kb_id}/export",
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print_success("Knowledge base exported")
        else:
            print_error(f"Failed with status {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:200]}")
            return False

        return True

    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_embedder_availability():
    """Test that embedders are properly initialized"""
    print_header("Embedder Availability Check")
    
    try:
        # Try to import embedders
        from pipeline.embedding import (
            SentenceTransformerTextEmbedder,
            CLIPImageEmbedder,
            ESMSequenceEmbedder
        )
        
        # Test text embedder
        print(f"\n{Colors.BOLD}Testing: SentenceTransformer Text Embedder{Colors.RESET}")
        try:
            text_embedder = SentenceTransformerTextEmbedder()
            embedding = text_embedder.embed("test protein sequence")
            if embedding is not None and len(embedding) == 384:
                print_success(f"SentenceTransformer embedder working (384-dim)")
            else:
                print_error("SentenceTransformer returned invalid embedding")
        except Exception as e:
            print_error(f"SentenceTransformer failed: {e}")
        
        # Test image embedder
        print(f"\n{Colors.BOLD}Testing: CLIP Image Embedder{Colors.RESET}")
        try:
            image_embedder = CLIPImageEmbedder()
            # Don't test with actual image, just check initialization
            print_success(f"CLIP embedder initialized (512-dim)")
        except Exception as e:
            print_info(f"CLIP may not be installed: {e}")
        
        # Test sequence embedder
        print(f"\n{Colors.BOLD}Testing: ESM Sequence Embedder{Colors.RESET}")
        try:
            seq_embedder = ESMSequenceEmbedder()
            # Don't test with actual sequence, just check initialization
            print_success(f"ESM embedder initialized (1280-dim)")
        except Exception as e:
            print_info(f"ESM may not be installed: {e}")
            
    except ImportError as e:
        print_error(f"Failed to import embedders: {e}")

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       QDesign Knowledge Service - API Test Suite          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    print_info(f"Testing API at: {API_BASE_URL}")
    print_info(f"Timeout: {TIMEOUT} seconds\n")
    
    # Wait a moment for API to be ready
    time.sleep(1)
    
    # Run tests
    results = {}
    try:
        results["Health Check"] = test_health_check()
    except Exception as e:
        print_error(f"Test Health Check failed with exception: {e}")
        results["Health Check"] = False

    try:
        results["Embedder Availability"] = test_embedder_availability()
    except Exception as e:
        print_error(f"Test Embedder Availability failed with exception: {e}")
        results["Embedder Availability"] = False

    kb_id = None
    try:
        discovery_ok = test_discovery_endpoints()
        results["Discovery Endpoints"] = discovery_ok
        if discovery_ok:
            # Re-run discovery to capture kb id for downstream tests
            response = requests.post(
                f"{API_BASE_URL}/discover",
                json={
                    "project_id": "test-project-001",
                    "project_description": "Protein engineering for stability and affinity",
                    "top_k": 5,
                    "min_relevance": 0.3
                },
                timeout=TIMEOUT
            )
            if response.status_code in [200, 201]:
                data = response.json()
                kb_id = data.get("knowledge_base_id")
    except Exception as e:
        print_error(f"Test Discovery Endpoints failed with exception: {e}")
        results["Discovery Endpoints"] = False

    try:
        results["Retrieval Endpoints"] = test_retrieval_endpoints(kb_id)
    except Exception as e:
        print_error(f"Test Retrieval Endpoints failed with exception: {e}")
        results["Retrieval Endpoints"] = False

    try:
        results["Curation Endpoints"] = test_curation_endpoints(kb_id)
    except Exception as e:
        print_error(f"Test Curation Endpoints failed with exception: {e}")
        results["Curation Endpoints"] = False

    try:
        results["Finalization Endpoints"] = test_finalization_endpoints(kb_id)
    except Exception as e:
        print_error(f"Test Finalization Endpoints failed with exception: {e}")
        results["Finalization Endpoints"] = False
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
