import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional, List, Tuple
from openai import OpenAI
from agent.tools.vector_search import retrieve_similar_cif, retrieve_similar_fasta
from agent.tools import db_query
from agent.tools.file_parser import parse_data_entry
from agent.tools.llm_analysis import sub_llm_tools, analyze_relevance, find_relationships, extract_entities, plan_retrieval
from graph.graph_objects import Graph, Node, Edge
from utils.models import DataPoolRequest, GraphAnalysisResponse, GraphData, GraphNode, GraphEdge, NodeType, EdgeType
from utils.processing import (
    generate_node_id, calculate_text_similarity, GraphAnalyzer, 
    ContentProcessor, create_embedding_placeholder, validate_graph_structure
)

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import json
import openai
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

def llm_tool_real(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal wrapper that sends a short prompt to the LLM.
    """
    client = OpenAI(
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=60.0
    )
    prompt = state.get("prompt", "Decide the next tool or stop. Return a JSON object.")
    try:
        print("LLM Prompt:", prompt)
        completion = client.chat.completions.create(
            extra_body={},
            model=os.getenv("OPENAI_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        text = completion.choices[0].message.content
    except Exception as e:
        return {"error": f"openai call failed: {e}", "stop": True}

    try:
        decision = json.loads(text)
        if isinstance(decision, dict):
            return decision
    except Exception:
        return {"raw_response": text, "stop": True}
    


def tool_retrieve_similar_cif(state: Dict[str, Any]) -> Dict[str, Any]:
    seed_vector = state.get("seed_vector")
    n = state.get("n", 50)
    feature_mask = state.get("feature_mask")
    results = retrieve_similar_cif(seed_vector, n=n, feature_mask=feature_mask)
    return {"cif_results": results}


def tool_retrieve_similar_fasta(state: Dict[str, Any]) -> Dict[str, Any]:
    seed_vector = state.get("seed_vector")
    n = state.get("n", 50)
    feature_mask = state.get("feature_mask")
    results = retrieve_similar_fasta(seed_vector, n=n, feature_mask=feature_mask)
    return {"fasta_results": results}


agent_instance = None


def tool_insert_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Insert or update a node into the shared agent graph without creating duplicates.

    Expects state to contain a `node` dict with keys: id, type, label, embedding (optional), metadata (optional).
    """
    global agent_instance
    if agent_instance is None:
        agent_instance = RetrievalAgent()
    node_data = state.get("node") or {}
    node_id = node_data.get("id")
    if not node_id:
        return {"error": "missing node id"}
    # If exists, merge metadata and update label/embedding if provided
    existing = agent_instance.graph.nodes.get(node_id)
    if existing:
        # merge metadata
        meta = existing.metadata.copy()
        meta.update(node_data.get("metadata", {}))
        existing.metadata = meta
        if node_data.get("label"):
            existing.label = node_data.get("label")
        if node_data.get("embedding") is not None:
            existing.embedding = node_data.get("embedding")
        agent_instance.graph.add_node(existing)
        return {"inserted": False, "id": node_id}
    # create new node
    new_node = Node(
        id=node_id,
        type=node_data.get("type", "unknown"),
        label=node_data.get("label", ""),
        embedding=node_data.get("embedding"),
        metadata=node_data.get("metadata", {}),
    )
    agent_instance.graph.add_node(new_node)
    return {"inserted": True, "id": node_id}


def tool_resolve_protein_name(state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a protein name to canonical ID via `db_query.resolve_protein_name`.

    Expects `name` in state.
    """
    name = state.get("name")
    if not name:
        return {"error": "missing name"}
    resolved = None
    if hasattr(db_query, "resolve_protein_name"):
        resolved = db_query.resolve_protein_name(name)
    return {"name": name, "resolved": resolved}


def tool_return_graph(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return the current graph built by the agent as JSON-serializable dict."""
    global agent_instance
    if agent_instance is None:
        return {"error": "no agent graph available"}
    return {"graph": agent_instance.graph.as_json()}


class MultiModalRetrievalAgent:
    """Enhanced agent for multi-modal data processing and graph generation.
    
    This agent can process various data types (PDF, CIF, PDB, text, images) and
    generate knowledge graphs with relationship detection and iterative retrieval.
    """
    
    def __init__(self, llm_brain=None):
        self.graph = Graph()
        self.llm_brain = llm_brain
        self.state: Dict[str, Any] = {}
        self.processed_entries = set()
        self.objectives = {}
        self.content_cache = {}
        self.processing_stats = defaultdict(int)
        
    def process_data_pool_request(self, request: DataPoolRequest) -> GraphAnalysisResponse:
        """Main entry point for processing data pool requests."""
        logger.info(f"Processing data pool with {len(request.dataPool)} entries")
        
        # Store objectives
        self.objectives = {
            "mainObjective": request.mainObjective,
            "secondaryObjectives": request.secondaryObjectives,
            "Notes": request.Notes,
            "Constraints": request.Constraints
        }
        
        try:
            # Phase 1: Parse and create initial nodes
            self._create_initial_nodes(request.dataPool)
            
            # Phase 2: Analyze content and extract relationships
            self._analyze_relationships()
            
            # Phase 3: Iterative retrieval based on objectives
            self._iterative_retrieval()
            
            # Phase 4: Generate final insights
            insights = self._synthesize_insights()
            
            # Create response
            graph_data = self._convert_to_api_format()
            
            return GraphAnalysisResponse(
                graphs=[graph_data],
                summary=insights.get("executive_summary", ""),
                processing_stats=dict(self.processing_stats),
                recommendations=insights.get("recommendations", [])
            )
            
        except Exception as e:
            logger.error(f"Error processing data pool: {str(e)}")
            raise
    
    def _create_initial_nodes(self, data_pool: List[Any]):
        """Create initial graph nodes from data pool entries."""
        logger.info("Creating initial nodes from data pool")
        
        for entry_data in data_pool:
            try:
                # Convert to dict if it's a Pydantic model
                if hasattr(entry_data, 'dict'):
                    entry_dict = entry_data.dict()
                else:
                    entry_dict = entry_data
                
                entry_id = entry_dict.get("_id", "")
                if entry_id in self.processed_entries:
                    continue
                
                # Parse content based on type
                parsed_content = parse_data_entry(entry_dict)
                self.content_cache[entry_id] = parsed_content
                
                # Analyze relevance to objectives
                text_content = self._extract_text_content(parsed_content)
                if text_content:
                    relevance_analysis = analyze_relevance(text_content, self.objectives)
                else:
                    relevance_analysis = {"relevance_score": 0.5}
                
                # Create node
                node_id = generate_node_id(
                    entry_dict.get("type", "unknown"),
                    text_content[:100],
                    entry_dict.get("name", "")
                )
                
                node_type = self._map_entry_type_to_node_type(entry_dict.get("type", "unknown"))
                
                node = Node(
                    id=node_id,
                    type=node_type,
                    label=entry_dict.get("name", f"Entry_{entry_id[:8]}"),
                    embedding=create_embedding_placeholder(text_content) if text_content else None,
                    metadata={
                        "original_id": entry_id,
                        "original_type": entry_dict.get("type"),
                        "description": entry_dict.get("description", ""),
                        "added_by": entry_dict.get("addedBy"),
                        "added_at": entry_dict.get("addedAt"),
                        "relevance_score": relevance_analysis.get("relevance_score", 0),
                        "key_insights": relevance_analysis.get("key_insights", []),
                        "parsed_data": parsed_content,
                        "content_summary": parsed_content.get("summary", ""),
                        "entities": parsed_content.get("entities", {})
                    }
                )
                
                self.graph.add_node(node)
                self.processed_entries.add(entry_id)
                self.processing_stats["nodes_created"] += 1
                
            except Exception as e:
                logger.error(f"Error processing entry {entry_data}: {str(e)}")
                self.processing_stats["processing_errors"] += 1
    
    def _analyze_relationships(self):
        """Analyze relationships between nodes and create edges."""
        logger.info("Analyzing relationships between nodes")
        
        nodes = list(self.graph.nodes.values())
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                try:
                    # Extract text content for comparison
                    text1 = self._extract_text_content(node1.metadata.get("parsed_data", {}))
                    text2 = self._extract_text_content(node2.metadata.get("parsed_data", {}))
                    
                    if not text1 or not text2:
                        continue
                    
                    # Calculate similarity
                    similarity = calculate_text_similarity(text1, text2)
                    
                    # Use LLM for deeper relationship analysis if similarity is above threshold
                    if similarity > 0.1:  # Basic threshold
                        relationship_analysis = find_relationships(
                            text1[:2000], text2[:2000], 
                            context=self.objectives.get("mainObjective", "")
                        )
                        
                        if relationship_analysis.get("relationship_exists", False):
                            edge_type = relationship_analysis.get("recommended_edge_type", "relates_to")
                            relationship_strength = relationship_analysis.get("relationship_strength", similarity)
                            
                            edge = Edge(
                                from_id=node1.id,
                                to_id=node2.id,
                                type=edge_type,
                                score=relationship_strength,
                                evidence=relationship_analysis.get("evidence", ""),
                                provenance={
                                    "method": "llm_analysis",
                                    "similarity_score": similarity,
                                    "analysis_timestamp": datetime.now().isoformat()
                                }
                            )
                            
                            self.graph.add_edge(edge)
                            self.processing_stats["edges_created"] += 1
                            
                except Exception as e:
                    logger.error(f"Error analyzing relationship between {node1.id} and {node2.id}: {str(e)}")
    
    def _iterative_retrieval(self, max_iterations: int = 3):
        """Perform iterative retrieval to expand the graph."""
        logger.info("Starting iterative retrieval")
        
        for iteration in range(max_iterations):
            current_nodes = [{
                "id": node.id,
                "type": node.type,
                "label": node.label,
                "relevance_score": node.metadata.get("relevance_score", 0)
            } for node in self.graph.nodes.values()]
            
            # Get retrieval strategy from LLM
            strategy = plan_retrieval(current_nodes, self.objectives)
            
            if strategy.get("stop_criteria_met", False) or not strategy.get("continue_retrieval", True):
                logger.info(f"Stopping retrieval at iteration {iteration + 1}")
                break
            
            # Perform retrievals based on strategy
            self._execute_retrieval_strategy(strategy)
            
            self.processing_stats["retrieval_iterations"] = iteration + 1
    
    def _execute_retrieval_strategy(self, strategy: Dict[str, Any]):
        """Execute the retrieval strategy."""
        suggested_queries = strategy.get("suggested_queries", [])
        
        for query in suggested_queries[:3]:  # Limit to 3 queries per iteration
            try:
                # Create seed vector from query (placeholder implementation)
                seed_vector = create_embedding_placeholder(query)
                
                # Try CIF retrieval
                try:
                    cif_results = retrieve_similar_cif(seed_vector, n=5)
                    self._process_retrieval_results(cif_results, "cif", query)
                except Exception as e:
                    logger.warning(f"CIF retrieval failed: {str(e)}")
                
                # Try FASTA retrieval
                try:
                    fasta_results = retrieve_similar_fasta(seed_vector, n=5)
                    self._process_retrieval_results(fasta_results, "fasta", query)
                except Exception as e:
                    logger.warning(f"FASTA retrieval failed: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Error executing retrieval for query '{query}': {str(e)}")
    
    def _process_retrieval_results(self, results: List[Dict[str, Any]], 
                                 result_type: str, query: str):
        """Process retrieval results and add to graph."""
        for result in results:
            try:
                node_id = result.get("node_id", f"retrieved_{len(self.graph.nodes)}")
                
                # Skip if already exists
                if node_id in self.graph.nodes:
                    continue
                
                node_type = "protein" if result_type == "cif" else "sequence"
                
                node = Node(
                    id=node_id,
                    type=node_type,
                    label=node_id,
                    embedding=None,
                    metadata={
                        "source": "retrieval",
                        "retrieval_type": result_type,
                        "query": query,
                        "score": result.get("score", 0),
                        "biological_features": result.get("biological_features", {}),
                        "score_explanation": result.get("score_explanation", ""),
                        "retrieved_at": datetime.now().isoformat()
                    }
                )
                
                self.graph.add_node(node)
                self.processing_stats["retrieved_nodes"] += 1
                
                # Create edges to relevant existing nodes
                self._create_retrieval_edges(node, query)
                
            except Exception as e:
                logger.error(f"Error processing retrieval result: {str(e)}")
    
    def _create_retrieval_edges(self, new_node: Node, query: str):
        """Create edges between retrieved nodes and existing relevant nodes."""
        for existing_node in self.graph.nodes.values():
            if existing_node.id == new_node.id:
                continue
                
            # Simple relevance check based on query similarity
            existing_content = self._extract_text_content(
                existing_node.metadata.get("parsed_data", {})
            )
            
            if existing_content and query.lower() in existing_content.lower():
                edge = Edge(
                    from_id=existing_node.id,
                    to_id=new_node.id,
                    type="relates_to",
                    score=0.6,  # Default retrieval relevance
                    evidence=f"Retrieved based on query: {query}",
                    provenance={"method": "retrieval_connection"}
                )
                
                self.graph.add_edge(edge)
    
    def _synthesize_insights(self) -> Dict[str, Any]:
        """Generate final insights from the complete graph."""
        logger.info("Synthesizing insights from graph")
        
        try:
            graph_data = self.graph.as_json()
            insights = sub_llm_tools.synthesize_graph_insights(graph_data, self.objectives)
            return insights
        except Exception as e:
            logger.error(f"Error synthesizing insights: {str(e)}")
            return {
                "executive_summary": "Analysis completed with errors",
                "key_insights": [],
                "recommendations": []
            }
    
    def _convert_to_api_format(self) -> GraphData:
        """Convert internal graph to API response format."""
        api_nodes = []
        for node in self.graph.nodes.values():
            api_node = GraphNode(
                id=node.id,
                type=NodeType(node.type) if node.type in [nt.value for nt in NodeType] else NodeType.CONCEPT,
                label=node.label,
                embedding=node.embedding,
                metadata=node.metadata,
                content_summary=node.metadata.get("content_summary", ""),
                relevance_score=node.metadata.get("relevance_score", 0)
            )
            api_nodes.append(api_node)
        
        api_edges = []
        for edge in self.graph.edges:
            api_edge = GraphEdge(
                from_id=edge.from_id,
                to_id=edge.to_id,
                type=EdgeType(edge.type) if edge.type in [et.value for et in EdgeType] else EdgeType.RELATES_TO,
                score=edge.score,
                evidence=edge.evidence,
                provenance=edge.provenance
            )
            api_edges.append(api_edge)
        
        return GraphData(
            nodes=api_nodes,
            edges=api_edges,
            metadata={
                "created_at": datetime.now().isoformat(),
                "objectives": self.objectives,
                "processing_stats": dict(self.processing_stats)
            }
        )
    
    def _extract_text_content(self, parsed_data: Dict[str, Any]) -> str:
        """Extract text content from parsed data."""
        if not parsed_data:
            return ""
        
        content_fields = ["text_content", "content", "summary"]
        for field in content_fields:
            if field in parsed_data and parsed_data[field]:
                return str(parsed_data[field])
        
        return ""
    
    def _map_entry_type_to_node_type(self, entry_type: str) -> str:
        """Map data entry types to graph node types."""
        mapping = {
            "pdf": "document",
            "text": "document",
            "cif": "structure",
            "pdb": "structure", 
            "image": "image",
            "fasta": "sequence"
        }
        return mapping.get(entry_type.lower(), "concept")

    def resolve_protein_name(self, name: str) -> Optional[str]:
        if hasattr(db_query, "resolve_protein_name"):
            return db_query.resolve_protein_name(name)
        return None

    def retrieve_and_update(self, retrieval_type: str, seed_vector: List[float], n: int = 10, feature_mask: Optional[List[float]] = None):
        """Legacy method for backward compatibility."""
        if retrieval_type == "cif":
            results = retrieve_similar_cif(seed_vector, n=n, feature_mask=feature_mask)
            node_type = "protein"
        elif retrieval_type == "fasta":
            results = retrieve_similar_fasta(seed_vector, n=n, feature_mask=feature_mask)
            node_type = "protein_sequence"
        else:
            raise ValueError(f"Unknown retrieval_type: {retrieval_type}")
        for r in results:
            node_id = r["node_id"]
            node = Node(
                id=node_id,
                type=node_type,
                label=node_id,
                embedding=None,
                metadata={"score": r.get("score"), "biological_features": r.get("biological_features"), "score_explanation": r.get("score_explanation")}
            )
            self.graph.add_node(node)
            if "query_node_id" in self.state:
                edge = Edge(from_id=self.state["query_node_id"], to_id=node_id, type="similarity", score=r.get("score"))
                self.graph.add_edge(edge)
        return results

# Legacy alias for backward compatibility
RetrievalAgent = MultiModalRetrievalAgent

def build_agent(llm_tool_fn):
    """Builds the StateGraph. Pass use_real_llm=True to call real OpenRouter LLM (requires openai and keys).
       Alternatively pass a custom llm_tool_fn (callable state->dict). Default for tests is llm_tool_dummy.
    """
    if StateGraph is None:
        raise RuntimeError("langgraph is not available in this environment")
    g = StateGraph()

    # tool nodes
    g.add_node("retrieve_cif", ToolNode(tool_retrieve_similar_cif))
    g.add_node("retrieve_fasta", ToolNode(tool_retrieve_similar_fasta))
    g.add_node("insert_node", ToolNode(tool_insert_node))
    g.add_node("resolve_name", ToolNode(tool_resolve_protein_name))
    g.add_node("return_graph", ToolNode(tool_return_graph))

    g.add_node("llm", ToolNode(llm_tool_fn))

    # edges: LLM → tools depending on next_tool in state
    g.add_edge("llm", "retrieve_cif", condition=lambda s: s.get("next_tool") == "retrieve_cif")
    g.add_edge("llm", "retrieve_fasta", condition=lambda s: s.get("next_tool") == "retrieve_fasta")
    g.add_edge("llm", "llm", condition=lambda s: s.get("next_tool") == "llm")  # optional loop
    g.add_edge("llm", "insert_node", condition=lambda s: s.get("next_tool") == "insert_node")
    g.add_edge("llm", "resolve_name", condition=lambda s: s.get("next_tool") == "resolve_name")
    g.add_edge("llm", "return_graph", condition=lambda s: bool(s.get("stop")))

    # return control back to LLM after each tool (so LLM decides next)
    g.add_edge("retrieve_cif", "llm")
    g.add_edge("retrieve_fasta", "llm")
    g.add_edge("insert_node", "llm")
    g.add_edge("resolve_name", "llm")

    g.add_edge("return_graph", END)
    g.set_entry_point("llm")
    return g


if __name__ == "__main__":
    import numpy as np
    from pprint import pprint

    agent = RetrievalAgent()
    
    protein_name = "hemoglobin"
    resolved = agent.resolve_protein_name(protein_name)
    print(f"Resolved '{protein_name}':\n{resolved}\n")

    seed_vector = np.random.randn(1280).tolist() 
    agent.state["query_node_id"] = "seed_node_1"

    agent.graph.add_node(Node(
        id="seed_node_1",
        type="protein",
        label=protein_name,
        embedding=seed_vector,
        metadata={"source": "test_input"}
    ))

    # --- Retrieve similar CIFs and FASTAs ---
    print("Retrieving similar CIFs...")
    cif_results = agent.retrieve_and_update("cif", seed_vector, n=3)
    pprint(cif_results)

    print("\nRetrieving similar FASTAs...")
    fasta_results = agent.retrieve_and_update("fasta", seed_vector, n=3)
    pprint(fasta_results)

    # --- Return final graph ---
    final_graph = agent.graph.as_json()
    print("\nFinal graph nodes and edges:")
    pprint(final_graph)
