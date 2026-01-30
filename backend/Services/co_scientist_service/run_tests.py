#!/usr/bin/env python3
"""
Test Runner - Comprehensive test suite for Co-Scientist Service improvements.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --quick      # Run quick tests only
    python run_tests.py --verbose    # Verbose output
"""

import sys
import os
import json
import time
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(name: str, passed: bool, duration: float = 0.0, error: str = None):
    """Print a test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    time_str = f"({duration:.3f}s)" if duration > 0 else ""
    print(f"  {status} {name} {time_str}")
    if error:
        print(f"       └─ {error[:80]}")


def run_test(name: str, test_func):
    """Run a single test and return result."""
    start = time.time()
    try:
        result = test_func()
        duration = time.time() - start
        passed = result is True or result is None
        print_result(name, passed, duration)
        return passed
    except Exception as e:
        duration = time.time() - start
        print_result(name, False, duration, str(e))
        return False


# ============================================================================
# METRICS TESTS
# ============================================================================

def test_metrics_import():
    """Test that enhanced metrics module imports correctly."""
    from src.monitoring.metrics import (
        REQUESTS, LATENCY, ACTIVE_REQUESTS,
        WORKFLOW_RUNS, AGENT_CALLS, LLM_CALLS,
        track_request, track_workflow, track_agent,
        track_llm_call, initialize_metrics
    )
    assert REQUESTS is not None
    assert track_request is not None
    return True


def test_metrics_tracking():
    """Test metrics tracking functions."""
    from src.monitoring.metrics import (
        track_request, track_agent, track_llm_call
    )
    
    # Test request tracking context manager
    with track_request("/test"):
        time.sleep(0.01)
    
    # Test agent tracking
    with track_agent("test_agent"):
        time.sleep(0.01)
    
    # Test LLM call tracking
    track_llm_call("openrouter", "test-model", 0.5, tokens_in=100, tokens_out=50)
    
    return True


# ============================================================================
# API MODELS TESTS
# ============================================================================

def test_api_models_import():
    """Test that enhanced API models import correctly."""
    from src.api.models import (
        RunRequest, V2RunRequest, FeedbackRequest,
        RunResponse, StatusResponse, HypothesisResponse,
        HealthResponse, MetricsResponse, ErrorResponse,
        ExplorationMode, RunStatus, CriticDecision,
        KGNodeResponse, KGEdgeResponse, SubgraphResponse,
    )
    assert ExplorationMode.BALANCED.value == "balanced"
    assert RunStatus.COMPLETED.value == "COMPLETED"
    return True


def test_api_models_validation():
    """Test API model validation."""
    from src.api.models import V2RunRequest, ExplorationMode
    from pydantic import ValidationError
    
    # Valid request
    req = V2RunRequest(
        kg_path="test.json",
        query="Test query",
        max_iterations=3
    )
    assert req.kg_path == "test.json"
    assert req.exploration_mode == ExplorationMode.BALANCED
    
    # Invalid max_iterations
    try:
        V2RunRequest(kg_path="test.json", max_iterations=15)
        return False  # Should have raised
    except ValidationError:
        pass  # Expected
    
    # Empty kg_path
    try:
        V2RunRequest(kg_path="   ")
        return False
    except ValidationError:
        pass
    
    return True


# ============================================================================
# STATE MANAGER TESTS
# ============================================================================

def test_state_manager_import():
    """Test that enhanced state manager imports correctly."""
    from src.orchestration.state_manager import (
        InMemoryStateManager, RunState, RunStatus,
        get_state_manager, AuditEntry
    )
    assert RunStatus.COMPLETED.value == "COMPLETED"
    return True


def test_state_manager_operations():
    """Test state manager CRUD operations."""
    from src.orchestration.state_manager import InMemoryStateManager
    
    manager = InMemoryStateManager()
    
    # Create run
    run = manager.create_run("test_run_1", config={"max_iterations": 3})
    assert run.run_id == "test_run_1"
    assert run.status == "CREATED"
    assert len(run.audit) == 1  # creation audit entry
    
    # Update run
    manager.update_run("test_run_1", status="RUNNING", phase="planning")
    run = manager.get_run("test_run_1")
    assert run.status == "RUNNING"
    assert run.current_phase == "planning"
    
    # Add audit
    manager.add_audit("test_run_1", "test_action", agent="planner", details={"key": "value"})
    run = manager.get_run("test_run_1")
    assert len(run.audit) >= 2  # creation + update + test_action
    
    # List runs
    manager.create_run("test_run_2")
    runs = manager.list_runs()
    assert len(runs) == 2
    
    # Get statistics
    stats = manager.get_statistics()
    assert stats["total_runs"] == 2
    
    # Delete run
    assert manager.delete_run("test_run_1")
    assert manager.get_run("test_run_1") is None
    
    return True


def test_state_manager_persistence():
    """Test state manager persistence."""
    from src.orchestration.state_manager import InMemoryStateManager
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        persist_path = Path(tmpdir) / "state.json"
        
        # Create and persist
        manager1 = InMemoryStateManager(persist_path=persist_path, auto_persist=True)
        manager1.create_run("persist_test", config={"test": True})
        manager1.update_run("persist_test", status="COMPLETED")
        
        # Load from disk
        manager2 = InMemoryStateManager(persist_path=persist_path)
        run = manager2.get_run("persist_test")
        assert run is not None
        assert run.status == "COMPLETED"
    
    return True


# ============================================================================
# MULTI-PATH TESTS
# ============================================================================

def test_multi_path_import():
    """Test multi-path extractor imports."""
    from src.knowledge_graph import MultiPathSubgraph, MultiPathExtractor
    assert MultiPathSubgraph is not None
    assert MultiPathExtractor is not None
    return True


def test_multi_path_subgraph_structure():
    """Test MultiPathSubgraph data structure."""
    from src.knowledge_graph.multi_path import MultiPathSubgraph
    from src.knowledge_graph.path_result import PathResult
    
    # Create a mock path result
    primary_path = PathResult(
        source="node_a",
        target="node_b",
        path=["node_a", "node_mid", "node_b"],
        edges=[],
        nodes=[],
        total_strength=0.8,
        path_length=3,
        path_string="A -> mid -> B",
        rationale=["Test rationale"]
    )
    
    subgraph = MultiPathSubgraph(
        primary_path=primary_path,
        alternative_paths=[],
        total_paths=1,
        total_nodes=3,
        total_edges=2,
    )
    
    # Test to_dict
    data = subgraph.to_dict()
    assert data["primary_path"]["source"] == "node_a"
    assert data["metadata"]["total_paths"] == 1
    
    # Test to_natural_language
    nl = subgraph.to_natural_language()
    assert "Multi-Path" in nl
    assert "node_a" in nl
    
    return True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_knowledge_graph_loading():
    """Test knowledge graph loading with multi-path support."""
    from src.knowledge_graph import KnowledgeGraphLoader, KnowledgeGraphIndex
    
    # Try loading the hemoglobin KG if available
    kg_path = Path("data/knowledge_graphs/hemoglobin_kg.json")
    if not kg_path.exists():
        print("       (skipped - no KG file)")
        return True
    
    loader = KnowledgeGraphLoader(str(kg_path))
    kg = loader.load()
    
    assert kg is not None
    assert len(kg.nodes) > 0
    
    # Test indexing
    index = KnowledgeGraphIndex(kg)
    stats = index.get_statistics()
    assert stats["total_nodes"] > 0
    
    return True


def test_multi_path_extraction():
    """Test multi-path extraction on real KG."""
    from src.knowledge_graph import (
        KnowledgeGraphLoader, KnowledgeGraphIndex, MultiPathExtractor
    )
    
    kg_path = Path("data/knowledge_graphs/hemoglobin_kg.json")
    if not kg_path.exists():
        print("       (skipped - no KG file)")
        return True
    
    loader = KnowledgeGraphLoader(str(kg_path))
    kg = loader.load()
    index = KnowledgeGraphIndex(kg)
    
    extractor = MultiPathExtractor(index)
    
    # Get hub nodes for testing
    hub_nodes = index.get_hub_nodes(top_k=2)
    if len(hub_nodes) < 2:
        print("       (skipped - not enough nodes)")
        return True
    
    # Extract multi-path subgraph
    result = extractor.extract_multi_path(
        hub_nodes[0].id,
        hub_nodes[1].id,
        max_paths=2,
        context_hops=1
    )
    
    if result:
        assert result.total_nodes > 0
        assert result.primary_path is not None
    
    return True


# ============================================================================
# ASYNC TESTS
# ============================================================================

async def async_test_workflow_config():
    """Test workflow configuration."""
    from src.orchestration.config import WorkflowConfig
    
    config = WorkflowConfig(
        max_iterations=5,
        exploration_mode="diverse",
        min_approval_score=8.0
    )
    
    assert config.max_iterations == 5
    assert config.exploration_mode == "diverse"
    return True


def test_workflow_config():
    """Wrapper for async test."""
    return asyncio.run(async_test_workflow_config())


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run Co-Scientist tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print_header("Co-Scientist Service - Test Suite v2.0")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Mode: {'Quick' if args.quick else 'Full'}")
    
    all_tests = []
    
    # Metrics tests
    print_header("Metrics Tests")
    all_tests.append(("metrics_import", run_test("Metrics Import", test_metrics_import)))
    all_tests.append(("metrics_tracking", run_test("Metrics Tracking", test_metrics_tracking)))
    
    # API Models tests
    print_header("API Models Tests")
    all_tests.append(("api_models_import", run_test("API Models Import", test_api_models_import)))
    all_tests.append(("api_models_validation", run_test("API Models Validation", test_api_models_validation)))
    
    # State Manager tests
    print_header("State Manager Tests")
    all_tests.append(("state_manager_import", run_test("State Manager Import", test_state_manager_import)))
    all_tests.append(("state_manager_ops", run_test("State Manager Operations", test_state_manager_operations)))
    all_tests.append(("state_manager_persist", run_test("State Manager Persistence", test_state_manager_persistence)))
    
    # Multi-Path tests
    print_header("Multi-Path Tests")
    all_tests.append(("multi_path_import", run_test("Multi-Path Import", test_multi_path_import)))
    all_tests.append(("multi_path_structure", run_test("Multi-Path Structure", test_multi_path_subgraph_structure)))
    
    if not args.quick:
        # Integration tests
        print_header("Integration Tests")
        all_tests.append(("kg_loading", run_test("Knowledge Graph Loading", test_knowledge_graph_loading)))
        all_tests.append(("multi_path_extraction", run_test("Multi-Path Extraction", test_multi_path_extraction)))
        
        # Workflow tests
        print_header("Workflow Tests")
        all_tests.append(("workflow_config", run_test("Workflow Config", test_workflow_config)))
    
    # Summary
    print_header("Summary")
    passed = sum(1 for _, p in all_tests if p)
    failed = sum(1 for _, p in all_tests if not p)
    total = len(all_tests)
    
    print(f"\n  Total:  {total}")
    print(f"  Passed: {passed} ✅")
    print(f"  Failed: {failed} {'❌' if failed else ''}")
    print(f"\n  Pass Rate: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
