"""
Ontologist Agent

Provides deep semantic interpretation of knowledge graph relationships.
Inspired by the SciAgents Ontologist role which defines and explains
concepts and their relationships within the knowledge graph.
"""

import json
import logging
from typing import AsyncIterator, Optional

from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class OntologistAgent(BaseAgent):
    """Ontologist Agent - Deep Knowledge Graph Interpretation.
    
    Analyzes the knowledge graph subgraph and provides:
    1. Clear definitions for each node/concept
    2. Detailed explanations of relationships between concepts
    3. Identification of key patterns and connections
    4. Synthesis of the subgraph into a coherent narrative
    """
    
    name = "ontologist"
    
    async def interpret(
        self, 
        subgraph: dict, 
        context: Optional[str] = None
    ) -> AgentResult:
        """High-level interface for subgraph interpretation.
        
        Args:
            subgraph: Knowledge graph subgraph with nodes and edges
            context: Optional context string
            
        Returns:
            AgentResult with interpretation
        """
        state = {
            "planner_output": {
                "subgraph": subgraph,
                "kg_metadata": {},
                "natural_language_context": context or ""
            },
            "user_query": context or ""
        }
        return await self.run(state)
    
    async def run(self, state: dict) -> AgentResult:
        """Analyze and interpret the knowledge graph subgraph.
        
        Args:
            state: Contains planner_output with subgraph and KG metadata
            
        Returns:
            AgentResult with detailed ontological interpretation
        """
        planner_output = state.get("planner_output", {})
        if not planner_output:
            return self._result({"error": "No planner output provided"}, confidence=0.0)
        
        subgraph = planner_output.get("subgraph", {})
        if not subgraph.get("nodes"):
            return self._result({"error": "No subgraph nodes to analyze"}, confidence=0.0)
        
        # Prepare input for LLM
        ontologist_input = self._prepare_input(
            subgraph=subgraph,
            kg_metadata=planner_output.get("kg_metadata", {}),
            natural_language=planner_output.get("natural_language_context", ""),
            user_query=state.get("user_query", "")
        )
        
        try:
            response = await self._ask("ontologist", ontologist_input)
            interpretation = self._validate_and_enhance(response, subgraph)
        except Exception as e:
            logger.error(f"Ontologist analysis failed: {e}")
            return self._result({"error": f"Ontological analysis failed: {e}"}, confidence=0.0)
        
        confidence = self._calculate_confidence(interpretation, subgraph)
        return self._result(interpretation, confidence=confidence)
    
    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        """Stream ontological interpretation in real-time."""
        planner_output = state.get("planner_output", {})
        if not planner_output:
            yield json.dumps({"error": "No planner output provided"})
            return
        
        subgraph = planner_output.get("subgraph", {})
        ontologist_input = self._prepare_input(
            subgraph=subgraph,
            kg_metadata=planner_output.get("kg_metadata", {}),
            natural_language=planner_output.get("natural_language_context", ""),
            user_query=state.get("user_query", "")
        )
        
        async for chunk in self._ask_stream("ontologist", ontologist_input):
            yield chunk
    
    def _prepare_input(
        self,
        subgraph: dict,
        kg_metadata: dict,
        natural_language: str,
        user_query: str
    ) -> dict:
        """Prepare structured input for the ontologist prompt.
        
        Args:
            subgraph: The extracted subgraph with nodes and edges
            kg_metadata: Metadata about the knowledge graph
            natural_language: Natural language description of the path
            user_query: User's research question
            
        Returns:
            Structured input dictionary for LLM
        """
        # Extract key information from subgraph
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        
        # Build node summaries
        node_summaries = []
        for node in nodes:
            summary = {
                "id": node.get("id"),
                "label": node.get("label"),
                "type": node.get("type"),
                "biological_features": node.get("biological_features", []),
                "trust_level": node.get("trust_level", 0.5)
            }
            node_summaries.append(summary)
        
        # Build edge summaries with relationship details
        edge_summaries = []
        for edge in edges:
            summary = {
                "source": edge.get("source"),
                "target": edge.get("target"),
                "label": edge.get("label"),
                "relationship_type": edge.get("correlation_type", "unknown"),
                "strength": edge.get("strength", 0.5),
                "explanation": edge.get("explanation", "")
            }
            edge_summaries.append(summary)
        
        return {
            "subgraph": {
                "nodes": node_summaries,
                "edges": edge_summaries,
                "node_count": len(nodes),
                "edge_count": len(edges)
            },
            "kg_context": {
                "main_objective": kg_metadata.get("main_objective", ""),
                "secondary_objectives": kg_metadata.get("secondary_objectives", []),
                "hub_nodes": kg_metadata.get("hub_nodes", [])
            },
            "path_description": natural_language,
            "user_query": user_query
        }
    
    def _validate_and_enhance(self, response: dict, subgraph: dict) -> dict:
        """Validate LLM response and enhance with computed metadata.
        
        Args:
            response: Raw response from LLM
            subgraph: Original subgraph for cross-referencing
            
        Returns:
            Enhanced interpretation dictionary
        """
        # Ensure required fields exist
        required_fields = [
            "concept_definitions",
            "relationship_explanations",
            "key_patterns",
            "narrative_synthesis"
        ]
        
        for field in required_fields:
            if field not in response:
                response[field] = self._generate_default(field, subgraph)
        
        # Add metadata
        response["_metadata"] = {
            "agent": "ontologist",
            "nodes_analyzed": len(subgraph.get("nodes", [])),
            "edges_analyzed": len(subgraph.get("edges", [])),
            "concepts_defined": len(response.get("concept_definitions", []))
        }
        
        return response
    
    def _generate_default(self, field: str, subgraph: dict) -> any:
        """Generate default value for missing field.
        
        Args:
            field: Field name
            subgraph: Subgraph for reference
            
        Returns:
            Default value for the field
        """
        defaults = {
            "concept_definitions": [
                {
                    "concept_id": node.get("id"),
                    "concept_label": node.get("label"),
                    "definition": f"Biological concept of type {node.get('type', 'unknown')}",
                    "role_in_subgraph": "participant"
                }
                for node in subgraph.get("nodes", [])
            ],
            "relationship_explanations": [
                {
                    "from_concept": edge.get("source"),
                    "to_concept": edge.get("target"),
                    "relationship": edge.get("label", "related to"),
                    "explanation": edge.get("explanation", "Connection in knowledge graph"),
                    "confidence": edge.get("strength", 0.5)
                }
                for edge in subgraph.get("edges", [])
            ],
            "key_patterns": ["Default pattern: nodes connected through biological relationships"],
            "narrative_synthesis": "Analysis of biological concepts and their relationships."
        }
        return defaults.get(field, None)
    
    def _calculate_confidence(self, interpretation: dict, subgraph: dict) -> float:
        """Calculate confidence score for the interpretation.
        
        Args:
            interpretation: The generated interpretation
            subgraph: Original subgraph
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.5  # Base score
        
        # More concepts defined = higher confidence
        concepts = interpretation.get("concept_definitions", [])
        nodes = subgraph.get("nodes", [])
        if nodes and concepts:
            coverage = len(concepts) / len(nodes)
            score += 0.2 * min(coverage, 1.0)
        
        # More relationship explanations = higher confidence
        relationships = interpretation.get("relationship_explanations", [])
        edges = subgraph.get("edges", [])
        if edges and relationships:
            rel_coverage = len(relationships) / len(edges)
            score += 0.2 * min(rel_coverage, 1.0)
        
        # Narrative quality (simple heuristic based on length)
        narrative = interpretation.get("narrative_synthesis", "")
        if len(narrative) > 200:
            score += 0.1
        
        return min(score, 1.0)
    
    def _format_subgraph(self, subgraph: dict) -> str:
        """Format subgraph into a string representation.
        
        Args:
            subgraph: Dictionary with nodes and edges
            
        Returns:
            Formatted string representation
        """
        lines = ["=== Subgraph Overview ===\n"]
        
        # Format nodes
        lines.append("Nodes:")
        for node in subgraph.get("nodes", []):
            node_id = node.get("id", "unknown")
            node_type = node.get("type", "entity")
            label = node.get("label", node.get("properties", {}).get("name", node_id))
            lines.append(f"  - {label} ({node_type}): {node_id}")
        
        lines.append("\nRelationships:")
        for edge in subgraph.get("edges", []):
            source = edge.get("source", "?")
            target = edge.get("target", "?")
            rel_type = edge.get("type", edge.get("label", "relates_to"))
            lines.append(f"  - {source} --[{rel_type}]--> {target}")
        
        return "\n".join(lines)
    
    def _extract_concepts(self, nodes: list[dict]) -> list[str]:
        """Extract concept names/labels from node list.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            List of concept names
        """
        concepts = []
        for node in nodes:
            # Try different keys for the concept name
            name = (
                node.get("label") or 
                node.get("name") or 
                node.get("properties", {}).get("name") or
                node.get("id", "")
            )
            if name:
                concepts.append(str(name))
        return concepts
