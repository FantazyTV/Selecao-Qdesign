#!/usr/bin/env python3
"""
Co-Scientist Service Test Script

Tests the API endpoints with the example knowledge graph.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx


BASE_URL = "http://localhost:8000"
KG_PATH = str(Path(__file__).parent / "data" / "knowledge_graphs" / "example_bio_kg.json")


class Colors:
    """Terminal colors for pretty output."""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")


def log_test(msg: str):
    print(f"{Colors.CYAN}[TEST]{Colors.NC} {msg}")


async def test_health_check():
    """Test the health check endpoint."""
    log_test("Testing health check endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                log_success(f"Health check passed: {response.json()}")
                return True
            else:
                log_error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            log_error(f"Health check error: {e}")
            return False


async def test_v2_run():
    """Test the /v2/run endpoint with the example knowledge graph."""
    log_test("Testing /v2/run endpoint...")
    
    if not Path(KG_PATH).exists():
        log_error(f"Knowledge graph not found: {KG_PATH}")
        return False
    
    log_info(f"Using knowledge graph: {KG_PATH}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            params = {
                "kg_path": KG_PATH,
                "query": "Find therapeutic strategies targeting apoptosis pathways in cancer",
                "concept_a": "p53",
                "concept_b": "cancer_therapy",
                "exploration_mode": "balanced",
                "max_iterations": 2
            }
            
            log_info(f"Request parameters: {json.dumps(params, indent=2)}")
            
            response = await client.post(
                f"{BASE_URL}/v2/run",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                log_success(f"Workflow completed successfully!")
                log_info(f"Run ID: {result.get('run_id')}")
                log_info(f"Status: {result.get('status')}")
                
                final_output = result.get('final_output', {})
                if final_output:
                    log_info("Final output preview:")
                    print(json.dumps(final_output, indent=2)[:500] + "...")
                
                return True
            else:
                log_error(f"Request failed: {response.status_code}")
                log_error(f"Response: {response.text}")
                return False
                
        except httpx.TimeoutException:
            log_error("Request timed out (this is expected if OPENROUTER_API_KEY is not set)")
            log_info("Set OPENROUTER_API_KEY in .env to test full workflow")
            return False
        except Exception as e:
            log_error(f"Request error: {e}")
            return False


async def test_knowledge_graph_loading():
    """Test knowledge graph loading directly."""
    log_test("Testing knowledge graph loading...")
    
    try:
        from src.knowledge_graph import KnowledgeGraphLoader
        
        loader = KnowledgeGraphLoader(KG_PATH)
        kg = loader.load()
        
        log_success(f"Knowledge graph loaded successfully")
        log_info(f"Nodes: {len(kg.nodes)}")
        log_info(f"Edges: {len(kg.edges)}")
        log_info(f"Main objective: {kg.main_objective}")
        
        # Display some nodes
        log_info("Sample nodes:")
        for node in list(kg.nodes.values())[:3]:
            print(f"  - {node.id} ({node.type}): {node.label}")
        
        return True
        
    except Exception as e:
        log_error(f"Knowledge graph loading error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_path_finding():
    """Test path finding in the knowledge graph."""
    log_test("Testing path finding...")
    
    try:
        from src.knowledge_graph import (
            KnowledgeGraphLoader,
            KnowledgeGraphIndex,
            PathFinder
        )
        
        loader = KnowledgeGraphLoader(KG_PATH)
        kg = loader.load()
        index = KnowledgeGraphIndex(kg)
        path_finder = PathFinder(index)
        
        log_info("Finding path: p53 -> cancer_therapy")
        paths = path_finder.find_paths("p53", "cancer_therapy", strategy="shortest", max_paths=3)
        
        if paths:
            log_success(f"Found {len(paths)} path(s)")
            for i, path in enumerate(paths, 1):
                path_str = " -> ".join(path.node_ids)
                log_info(f"Path {i}: {path_str}")
                log_info(f"  Confidence: {path.avg_confidence:.2f}")
            return True
        else:
            log_error("No paths found")
            return False
            
    except Exception as e:
        log_error(f"Path finding error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test functions."""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.NC}")
    print(f"{Colors.YELLOW}Co-Scientist Service Test Suite{Colors.NC}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.NC}\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", await test_health_check()))
    print()
    
    # Test 2: Knowledge graph loading
    results.append(("KG Loading", await test_knowledge_graph_loading()))
    print()
    
    # Test 3: Path finding
    results.append(("Path Finding", await test_path_finding()))
    print()
    
    # Test 4: API endpoint (may fail without API key)
    results.append(("API Endpoint", await test_v2_run()))
    print()
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.NC}")
    print(f"{Colors.YELLOW}Test Summary{Colors.NC}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.NC}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.NC}" if result else f"{Colors.RED}FAILED{Colors.NC}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests passed{Colors.NC}\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
