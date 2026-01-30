"""
SciAgents-inspired Planner Agent

Loads KG, extracts subgraphs via random pathfinding with waypoints.
"""
from typing import Optional

from .base_agent import BaseAgent, AgentResult
from .models import PlannerContext
from .confidence import calculate_planner_confidence
from ..knowledge_graph import (
    KnowledgeGraphLoader,
    KnowledgeGraphIndex,
    PathFinder,
    SubgraphExtractor,
)


class PlannerAgent(BaseAgent):
    """Planner Agent - Knowledge Graph Path Finding."""
    name = "planner"

    def __init__(self):
        self._kg_loader: Optional[KnowledgeGraphLoader] = None
        self._kg_index: Optional[KnowledgeGraphIndex] = None
        self._path_finder: Optional[PathFinder] = None
        self._subgraph_extractor: Optional[SubgraphExtractor] = None

    def load_knowledge_graph(self, kg_path: str) -> dict:
        """Load and index the knowledge graph from JSON file."""
        self._kg_loader = KnowledgeGraphLoader(kg_path)
        kg = self._kg_loader.load()
        self._kg_index = KnowledgeGraphIndex(kg)
        self._path_finder = PathFinder(self._kg_index)
        self._subgraph_extractor = SubgraphExtractor(self._kg_index)
        stats = self._kg_index.get_statistics()
        hub_nodes = self._kg_index.get_hub_nodes(top_k=5)
        return {
            "loaded": True, "statistics": stats,
            "hub_nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in hub_nodes],
            "main_objective": kg.main_objective,
            "secondary_objectives": kg.secondary_objectives
        }

    def _select_concept_pair(self, state: dict) -> tuple[str, str]:
        """Select two concepts to connect."""
        if not self._kg_index:
            raise RuntimeError("Knowledge graph not loaded")
        if "concept_a" in state and "concept_b" in state:
            return (state["concept_a"], state["concept_b"])
        hub_nodes = self._kg_index.get_hub_nodes(top_k=10)
        if len(hub_nodes) >= 2:
            return (hub_nodes[0].id, hub_nodes[1].id)
        nodes = list(self._kg_index.get_all_nodes())
        if len(nodes) >= 2:
            return (nodes[0].id, nodes[-1].id)
        raise ValueError("Not enough nodes in knowledge graph")

    def _determine_path_strategy(self, state: dict) -> str:
        """Determine path finding strategy."""
        mode = state.get("exploration_mode", "balanced")
        return {"diverse": "random", "conservative": "high_confidence",
                "balanced": "diverse", "direct": "shortest"}.get(mode, "diverse")

    async def run(self, state: dict) -> AgentResult:
        """Main planner execution."""
        kg_path = state.get("kg_path")
        if not kg_path:
            return self._result({"error": "No knowledge graph path provided"}, confidence=0.0)
        try:
            kg_metadata = self.load_knowledge_graph(kg_path)
        except Exception as e:
            return self._result({"error": f"Failed to load KG: {e}"}, confidence=0.0)
        try:
            concept_a, concept_b = self._select_concept_pair(state)
        except Exception as e:
            return self._result({"error": f"Failed to select concepts: {e}"}, confidence=0.0)
        strategy = self._determine_path_strategy(state)
        max_paths = state.get("max_paths", 3)
        try:
            subgraph = self._subgraph_extractor.extract_for_concepts(
                concept_a, concept_b, strategy=strategy)
        except Exception as e:
            return self._result({"error": f"Failed to extract subgraph: {e}"}, confidence=0.0)
        if not subgraph:
            return self._result({"error": "No path found between concepts"}, confidence=0.0)
        subgraph_dict = subgraph.to_dict()
        natural_language = subgraph.to_natural_language()
        enriched = await self._enrich_with_llm(subgraph_dict, natural_language,
                                                kg_metadata.get("main_objective", ""), state)
        output = {
            "subgraph": subgraph_dict, "natural_language_context": natural_language,
            "enriched_analysis": enriched, "path_strategy": strategy,
            "concepts_connected": {"source": concept_a, "target": concept_b},
            "kg_metadata": kg_metadata, "statistics": {
                "nodes_in_subgraph": len(subgraph_dict.get("nodes", [])),
                "edges_in_subgraph": len(subgraph_dict.get("edges", [])),
            }
        }
        return self._result(output, confidence=calculate_planner_confidence(subgraph_dict))

    async def _enrich_with_llm(self, subgraph_dict: dict, natural_language: str,
                               main_objective: str, state: dict) -> dict:
        """Use LLM to provide additional analysis."""
        llm_input = {"subgraph": subgraph_dict, "context": natural_language,
                     "main_objective": main_objective, "user_query": state.get("query", "")}
        try:
            return await self._ask("planner", llm_input)
        except Exception as e:
            return {"error": str(e), "raw_context_available": True}

