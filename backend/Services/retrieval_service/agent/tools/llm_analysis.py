"""
Specialized LLM tools for content analysis, relationship detection, and objective-based retrieval.
These tools act as sub-agents with focused capabilities for specific tasks.
"""

import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

logger = logging.getLogger(__name__)

class LLMToolError(Exception):
    """Custom exception for LLM tool errors."""
    pass

class SubLLMTools:
    """Collection of specialized LLM tools for different analysis tasks."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE")
        self.model = os.getenv("OPENAI_MODEL")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. LLM tools will be limited.")
    
    def _call_llm(self, prompt: str, model: str = "anthropic/claude-3-haiku", 
                  temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Make a call to the LLM with error handling."""
        if not self.api_key:
            raise LLMToolError("No API key available for LLM calls")
        
        try:
            client = OpenAI(
                base_url=self.api_base,
                api_key=self.api_key,
                timeout=60.0
            )
            completion = client.chat.completions.create(
                extra_body={},
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise LLMToolError(f"LLM call failed: {str(e)}")
    
    def analyze_content_relevance(self, content: str, objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how relevant content is to the given objectives."""
        main_objective = objectives.get("mainObjective", "")
        secondary_objectives = objectives.get("secondaryObjectives", [])
        constraints = objectives.get("Constraints", [])
        
        prompt = f"""
        Analyze the following content for relevance to the research objectives:
        
        MAIN OBJECTIVE: {main_objective}
        SECONDARY OBJECTIVES: {', '.join(secondary_objectives)}
        CONSTRAINTS: {', '.join(constraints)}
        
        CONTENT TO ANALYZE:
        {content[:3000]}  # Limit content length
        
        Please provide a JSON response with:
        {{
            "relevance_score": float (0-1),
            "main_objective_alignment": float (0-1),
            "secondary_alignment": [float for each secondary objective],
            "constraint_violations": [list of potential violations],
            "key_insights": [list of relevant insights from the content],
            "recommended_connections": [list of potential connections to make],
            "content_type_assessment": "description of what type of information this is"
        }}
        
        Be specific and detailed in your analysis.
        """
        
        try:
            response = self._call_llm(prompt, max_tokens=1500)
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "relevance_score": 0.5,
                "main_objective_alignment": 0.5,
                "secondary_alignment": [0.5] * len(secondary_objectives),
                "constraint_violations": [],
                "key_insights": ["Analysis failed - manual review needed"],
                "recommended_connections": [],
                "content_type_assessment": "unknown",
                "error": "Failed to parse LLM response"
            }
    
    def detect_relationships(self, content1: str, content2: str, 
                           context: Optional[str] = None) -> Dict[str, Any]:
        """Detect relationships between two pieces of content."""
        prompt = f"""
        Analyze the relationship between these two pieces of content:
        
        CONTENT 1:
        {content1[:2000]}
        
        CONTENT 2:
        {content2[:2000]}
        
        {"CONTEXT: " + context if context else ""}
        
        Please provide a JSON response with:
        {{
            "relationship_exists": boolean,
            "relationship_type": "one of: similarity, reference, conflict, support, derivation, mention, unknown",
            "relationship_strength": float (0-1),
            "evidence": "specific evidence for the relationship",
            "bidirectional": boolean,
            "semantic_similarity": float (0-1),
            "topical_overlap": [list of overlapping topics/concepts],
            "recommended_edge_type": "graph edge type recommendation"
        }}
        """
        
        try:
            response = self._call_llm(prompt, max_tokens=1000)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "relationship_exists": False,
                "relationship_type": "unknown",
                "relationship_strength": 0.0,
                "evidence": "Analysis failed",
                "bidirectional": False,
                "semantic_similarity": 0.0,
                "topical_overlap": [],
                "recommended_edge_type": "unknown",
                "error": "Failed to parse LLM response"
            }
    
    def extract_entities_and_concepts(self, content: str, 
                                    domain_context: str = "biomedical") -> Dict[str, Any]:
        """Extract entities and concepts from content."""
        prompt = f"""
        Extract entities and concepts from this {domain_context} content:
        
        CONTENT:
        {content[:3000]}
        
        Please provide a JSON response with:
        {{
            "proteins": [list of protein names/identifiers],
            "genes": [list of gene names/identifiers],
            "chemicals": [list of chemical compounds],
            "organisms": [list of organism names],
            "diseases": [list of diseases/conditions],
            "methods": [list of experimental methods/techniques],
            "measurements": [list of quantitative measurements with units],
            "key_concepts": [list of important scientific concepts],
            "relationships": [list of entity-relationship pairs],
            "confidence_scores": {{entity_type: confidence_score}}
        }}
        
        Be precise and focus on scientifically relevant entities.
        """
        
        try:
            response = self._call_llm(prompt, max_tokens=1500)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "proteins": [],
                "genes": [],
                "chemicals": [],
                "organisms": [],
                "diseases": [],
                "methods": [],
                "measurements": [],
                "key_concepts": [],
                "relationships": [],
                "confidence_scores": {},
                "error": "Failed to parse LLM response"
            }
    
    def suggest_retrieval_strategy(self, current_nodes: List[Dict], 
                                 objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest what additional data to retrieve based on current graph state."""
        nodes_summary = "\n".join([
            f"- {node.get('type', 'unknown')}: {node.get('label', 'unlabeled')} (relevance: {node.get('relevance_score', 'unknown')})"
            for node in current_nodes[:20]  # Limit to avoid token overflow
        ])
        
        main_objective = objectives.get("mainObjective", "")
        secondary_objectives = objectives.get("secondaryObjectives", [])
        
        prompt = f"""
        Based on the current graph state and research objectives, suggest what additional data to retrieve:
        
        MAIN OBJECTIVE: {main_objective}
        SECONDARY OBJECTIVES: {', '.join(secondary_objectives)}
        
        CURRENT GRAPH NODES:
        {nodes_summary}
        
        Please provide a JSON response with:
        {{
            "continue_retrieval": boolean,
            "retrieval_priority": "high/medium/low",
            "suggested_queries": [list of specific search queries],
            "missing_data_types": [list of data types we should look for],
            "gap_analysis": "description of what's missing",
            "convergence_assessment": "how close are we to sufficient coverage",
            "next_steps": [list of recommended next steps],
            "stop_criteria_met": boolean
        }}
        """
        
        try:
            response = self._call_llm(prompt, max_tokens=1200)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "continue_retrieval": True,
                "retrieval_priority": "medium",
                "suggested_queries": [],
                "missing_data_types": [],
                "gap_analysis": "Analysis failed",
                "convergence_assessment": "Unknown",
                "next_steps": [],
                "stop_criteria_met": False,
                "error": "Failed to parse LLM response"
            }
    
    def synthesize_graph_insights(self, graph_data: Dict[str, Any], 
                                objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize insights from the complete graph."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        graph_summary = f"""
        GRAPH STATISTICS:
        - Nodes: {len(nodes)}
        - Edges: {len(edges)}
        - Node Types: {list(set(node.get('type', 'unknown') for node in nodes))}
        - Edge Types: {list(set(edge.get('type', 'unknown') for edge in edges))}
        """
        
        key_nodes = [node for node in nodes if node.get('relevance_score', 0) > 0.7][:10]
        
        prompt = f"""
        Synthesize insights from this knowledge graph related to the research objectives:
        
        OBJECTIVES: {objectives.get('mainObjective', '')}
        SECONDARY: {', '.join(objectives.get('secondaryObjectives', []))}
        
        {graph_summary}
        
        KEY HIGH-RELEVANCE NODES:
        {json.dumps(key_nodes, indent=2)[:2000]}
        
        Please provide a JSON response with:
        {{
            "executive_summary": "high-level summary of findings",
            "key_insights": [list of important discoveries],
            "objective_alignment": "how well the graph addresses objectives",
            "knowledge_gaps": [list of identified gaps],
            "recommendations": [list of actionable recommendations],
            "confidence_level": float (0-1),
            "graph_quality_assessment": "assessment of graph completeness and reliability"
        }}
        """
        
        try:
            response = self._call_llm(prompt, model="anthropic/claude-3-sonnet", max_tokens=2000)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "executive_summary": "Analysis failed",
                "key_insights": [],
                "objective_alignment": "Unknown",
                "knowledge_gaps": [],
                "recommendations": [],
                "confidence_level": 0.0,
                "graph_quality_assessment": "Unable to assess",
                "error": "Failed to parse LLM response"
            }
    
    def objective_focused_retrieval(self, objectives: Dict[str, Any], 
                                  data_types: List[str] = None) -> Dict[str, Any]:
        """Generate targeted retrieval queries based on objectives."""
        main_objective = objectives.get("mainObjective", "")
        secondary_objectives = objectives.get("secondaryObjectives", [])
        constraints = objectives.get("Constraints", [])
        notes = objectives.get("Notes", [])
        
        data_types_str = ", ".join(data_types) if data_types else "any relevant data type"
        
        prompt = f"""
        Generate targeted retrieval strategies for these research objectives:
        
        MAIN OBJECTIVE: {main_objective}
        SECONDARY OBJECTIVES: {', '.join(secondary_objectives)}
        CONSTRAINTS: {', '.join(constraints)}
        NOTES: {', '.join(notes)}
        
        AVAILABLE DATA TYPES: {data_types_str}
        
        Please provide a JSON response with:
        {{
            "primary_queries": [list of specific search queries for main objective],
            "secondary_queries": [list of queries for secondary objectives],
            "cross_cutting_queries": [queries that address multiple objectives],
            "data_type_priorities": {{data_type: priority_score}},
            "search_strategies": [list of recommended search approaches],
            "expected_connections": [list of likely connections to find],
            "success_metrics": [list of criteria for successful retrieval]
        }}
        
        Be specific and actionable in your recommendations.
        """
        
        try:
            response = self._call_llm(prompt, max_tokens=1500)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "primary_queries": [],
                "secondary_queries": [],
                "cross_cutting_queries": [],
                "data_type_priorities": {},
                "search_strategies": [],
                "expected_connections": [],
                "success_metrics": [],
                "error": "Failed to parse LLM response"
            }

# Singleton instance for easy access
sub_llm_tools = SubLLMTools()

# Convenience functions for common operations
def analyze_relevance(content: str, objectives: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for content relevance analysis."""
    return sub_llm_tools.analyze_content_relevance(content, objectives)

def find_relationships(content1: str, content2: str, context: str = None) -> Dict[str, Any]:
    """Convenience function for relationship detection."""
    return sub_llm_tools.detect_relationships(content1, content2, context)

def extract_entities(content: str, domain: str = "biomedical") -> Dict[str, Any]:
    """Convenience function for entity extraction."""
    return sub_llm_tools.extract_entities_and_concepts(content, domain)

def plan_retrieval(current_nodes: List[Dict], objectives: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for retrieval planning."""
    return sub_llm_tools.suggest_retrieval_strategy(current_nodes, objectives)

def synthesize_insights(graph_data: Dict[str, Any], objectives: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for graph insights synthesis."""
    return sub_llm_tools.synthesize_graph_insights(graph_data, objectives)