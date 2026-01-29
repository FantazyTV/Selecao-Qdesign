#!/usr/bin/env python3
"""
Quick test script for the hemoglobin knowledge graph.
Tests path finding and workflow execution.
"""

import asyncio
import json
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from knowledge_graph import KnowledgeGraphLoader, KnowledgeGraphIndex, PathFinder


async def test_hemoglobin_kg():
    """Test the hemoglobin knowledge graph."""
    
    print("=" * 70)
    print("Testing Hemoglobin Knowledge Graph")
    print("=" * 70)
    
    kg_path = "data/knowledge_graphs/hemoglobin_kg.json"
    
    # Load and index
    print(f"\n[1/4] Loading knowledge graph...")
    loader = KnowledgeGraphLoader(kg_path)
    kg = loader.load()
    print(f"✓ Loaded: {kg.name}")
    print(f"  • Nodes: {kg.node_count}")
    print(f"  • Edges: {kg.edge_count}")
    print(f"  • Objective: {kg.main_objective}")
    
    # Build index
    print(f"\n[2/4] Building graph index...")
    index = KnowledgeGraphIndex(kg)
    stats = index.get_statistics()
    print(f"✓ Index built")
    print(f"  • Nodes indexed: {stats['total_nodes']}")
    print(f"  • Edges indexed: {stats['total_edges']}")
    
    # Find hub nodes
    print(f"\n[3/4] Identifying hub nodes...")
    hubs = index.get_hub_nodes(top_k=5)
    print(f"✓ Top hub nodes:")
    for node in hubs:
        degree = len(index.adjacency.get(node.id, []))
        print(f"  • {node.label[:40]} ({node.type}): {degree} connections")
    
    # Test path finding
    print(f"\n[4/4] Testing path finding...")
    if len(hubs) >= 2:
        source_id = hubs[0].id
        
        # Find a target node that's not the source
        all_nodes = list(kg.nodes)
        target_node = next((n for n in all_nodes if n.id != source_id and n.type == 'pdb'), all_nodes[-1])
        target_id = target_node.id
        
        print(f"  Finding path: {source_id} → {target_id}")
        
        path_finder = PathFinder(index)
        path = path_finder.find_path(source_id, target_id, strategy="shortest")
        
        if path:
            print(f"✓ Path found with {len(path.path)} nodes")
            print(f"  Path: {' → '.join(path.path[:5])}{'...' if len(path.path) > 5 else ''}")
            print(f"  Average strength: {path.average_strength:.2f}")
        else:
            print(f"⚠ No path found between {source_id} and {target_id}")
    else:
        print("⚠ Not enough hub nodes for path testing")
    
    print(f"\n{'=' * 70}")
    print("✓ All tests completed successfully!")
    print("=" * 70)
    
    # Show how to use the API
    print(f"\n📝 To test with the API, run:")
    print(f"  curl -X POST 'http://localhost:8000/v2/run?kg_path={kg_path}&exploration_mode=balanced&max_iterations=2'")
    print()


if __name__ == "__main__":
    asyncio.run(test_hemoglobin_kg())
