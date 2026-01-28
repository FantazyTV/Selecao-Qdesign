import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional, List, Tuple
from openai import OpenAI
from agent.tools.vector_search import retrieve_similar_cif, retrieve_similar_fasta
from agent.tools import web_search
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
    if hasattr(web_search, "resolve_protein_name"):
        resolved = web_search.resolve_protein_name(name)
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
        """Main entry point for processing data pool requests using the new deterministic pipeline."""
        logger.info(f"Processing data pool with {len(request.dataPool)} entries")
        
        # Convert DataPoolRequest to run_single_job format
        project_payload = {
            "files": [
                {
                    "type": entry.type.value,
                    "content": entry.content,
                    "name": entry.name,
                    "description": entry.description
                }
                for entry in request.dataPool
            ],
            "objectives": {
                "mainObjective": request.mainObjective,
                "secondaryObjectives": request.secondaryObjectives,
                "Notes": request.Notes,
                "Constraints": request.Constraints
            }
        }
        
        try:
            # Use the new deterministic pipeline
            result = self.run_single_job(project_payload)
            
            # Convert result to GraphAnalysisResponse format
            graph_data = GraphData(
                nodes=[
                    GraphNode(
                        id=str(node["id"]),
                        type=node["type"],
                        label=str(node["label"]),
                        metadata=node.get("metadata", {})
                    )
                    for node in result["nodes"]
                ],
                edges=[
                    GraphEdge(
                        from_id=str(edge["from_id"]),
                        to_id=str(edge["to_id"]),
                        type=edge["type"],
                        score=edge.get("score"),
                        evidence=edge.get("evidence"),
                        provenance=edge.get("provenance", {})
                    )
                    for edge in result["edges"]
                ]
            )
            
            return GraphAnalysisResponse(
                graphs=[graph_data],
                summary=f"Processed {len(result['nodes'])} nodes and {len(result['edges'])} edges",
                processing_stats=result["metadata"]["processing_stats"],
                recommendations=[]
            )
            
        except Exception as e:
            logger.error(f"Error processing data pool: {str(e)}")
            raise
    
    def run_single_job(self, project_payload: Dict[str, Any]) -> Dict[str, Any]:
        """New simplified pipeline for processing project files with deterministic logic."""
        print("=== STARTING AGENT PIPELINE: run_single_job ===")
        from agent.tools.parser.cif_parser import parse_cif_file
        from agent.tools.embedder import embed_if_missing, dummy_embedder
        from utils.processing import generate_node_id
        
        logger.info("Starting new deterministic pipeline")
        
        # Reset graph and stats
        self.graph = Graph()
        self.processing_stats = defaultdict(int)
        
        # Parse objectives
        objectives = project_payload.get("objectives", {})
        logger.info(f"Objectives: {objectives}")
        
        # Phase 1: Process uploaded files and create initial nodes
        files = project_payload.get("files", [])
        print(f"Processing {len(files)} uploaded files")
        for file_data in files:
            try:
                file_type = file_data.get("type", "").lower()
                content = file_data.get("content", "")
                
                if file_type == "cif":
                    # Parse CIF
                    print(f"TOOL CALL: parse_cif_file(content_length={len(content)})")
                    parsed = parse_cif_file(content)
                    print(f"TOOL RESULT: parse_cif_file returned keys={list(parsed.keys())}")
                    
                    print(f"TOOL CALL: summarize_parsed(parsed_keys={list(parsed.keys())})")
                    summary = summarize_parsed(parsed)
                    print(f"TOOL RESULT: summarize_parsed returned '{summary[:50]}...'")
                    
                    # Create node
                    node_id = generate_node_id("cif", summary, parsed.get("entry_id", "unknown"))
                    node = Node(
                        id=node_id,
                        type="structure",
                        label=str(parsed.get("entry_id", "Unknown")),
                        metadata={
                            "parsed": parsed,
                            "content_summary": summary,
                            "source": "uploaded_file",
                            "file_type": file_type
                        }
                    )
                    
                    self.graph.add_node(node)
                    self.processing_stats["nodes_created"] += 1
                    
                    logger.info(f"Created node {node.id}: {summary}")
                    
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                self.processing_stats["processing_errors"] += 1
        
        # Phase 2: Embed all nodes
        print("=== PHASE 2: EMBEDDING ALL NODES ===")
        for node in list(self.graph.nodes.values()):
            try:
                print(f"TOOL CALL: embed_if_missing(node_id={node.id}, has_embedding={node.embedding is not None})")
                embedding = embed_if_missing(node, dummy_embedder)
                print(f"TOOL RESULT: embed_if_missing returned embedding_length={len(embedding) if embedding else 0}")
                if embedding:
                    node.embedding = embedding
            except Exception as e:
                logger.error(f"Error embedding node {node.id}: {str(e)}")
        
        # Phase 3: Deterministic expansion phase (NO LLM)
        print("=== PHASE 3: DETERMINISTIC EXPANSION ===")
        self.expand_unexpanded_nodes()
        
        # Phase 4: LLM reasoning phase (analyze expanded graph)
        print("=== PHASE 4: LLM REASONING PHASE ===")
        for node in self.graph.nodes.values():
            try:
                # Validate against objectives (for analysis, not for expansion decisions)
                print(f"TOOL CALL: validate_against_objectives(node_id={node.id}, objectives_keys={list(objectives.keys())})")
                validation = validate_against_objectives(node, objectives)
                print(f"TOOL RESULT: validate_against_objectives returned score={validation.get('relevance_score')}, reasons_count={len(validation.get('reasons', []))}")
                node.metadata["relevance"] = validation
                
                logger.info(f"Node {node.id}: relevance={validation.get('relevance_score', 0):.2f}")
                
            except Exception as e:
                logger.error(f"Error validating node {node.id}: {str(e)}")
        
        # Compute final metrics
        total_nodes = len(self.graph.nodes)
        total_edges = len(self.graph.edges)
        expanded_nodes = sum(
            1 for n in self.graph.nodes.values() 
            if n.metadata.get("expanded", {}).get("cif", False) or n.metadata.get("expanded", {}).get("fasta", False)
        )
        
        coverage = {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "expanded_nodes": expanded_nodes,
            "retrieval_iterations": 1,
            "stop_criteria_met": True
        }
        
        # Update processing stats
        self.processing_stats.update(coverage)
        
        # Return graph with metadata
        graph_json = self.graph.as_json()
        graph_json["metadata"] = {
            "processing_stats": dict(self.processing_stats),
            "objectives": objectives,
            "pipeline_version": "deterministic_v2"
        }
        
        logger.info(f"Pipeline complete: {coverage}")
        print(f"=== AGENT PIPELINE COMPLETE: Returning graph with {len(graph_json['nodes'])} nodes and {len(graph_json['edges'])} edges ===")
        return graph_json
    
    def expand_unexpanded_nodes(self):
        """Deterministically expand all nodes that have embeddings and haven't been expanded yet."""
        print("=== STARTING DETERMINISTIC EXPANSION: expand_unexpanded_nodes ===")
        from agent.tools.retriever import retrieve_candidates
        from agent.tools.feature_mapper import map_score_explanation_to_features
        from agent.tools.edge_creator import create_edge_with_evidence
        
        expanded_count = 0
        
        for node in list(self.graph.nodes.values()):
            if not node.embedding:
                continue
                
            expanded = node.metadata.setdefault("expanded", {})
            
            # Expand CIF structures if not already expanded
            if node.type == "structure" and not expanded.get("cif", False):
                print(f"TOOL CALL: retrieve_candidates for CIF (node_id={node.id}, embedding_length={len(node.embedding)})")
                results = retrieve_candidates(
                    node.embedding, 
                    collections=["structures"], 
                    n=50
                )
                print(f"TOOL RESULT: retrieve_candidates returned {len(results)} CIF results")
                
                self._insert_results(node, results, edge_type="structure_similarity")
                expanded["cif"] = True
                expanded_count += 1
            
            # Expand FASTA sequences if not already expanded
            if node.type == "sequence" and not expanded.get("fasta", False):
                print(f"TOOL CALL: retrieve_candidates for FASTA (node_id={node.id}, embedding_length={len(node.embedding)})")
                results = retrieve_candidates(
                    node.embedding, 
                    collections=["uniprot_sequences"], 
                    n=50
                )
                print(f"TOOL RESULT: retrieve_candidates returned {len(results)} FASTA results")
                
                self._insert_results(node, results, edge_type="sequence_similarity")
                expanded["fasta"] = True
                expanded_count += 1
        
        print(f"=== DETERMINISTIC EXPANSION COMPLETE: Expanded {expanded_count} nodes ===")
    
    def _insert_results(self, source_node, results, edge_type):
        """Helper method to insert retrieval results into the graph."""
        from agent.tools.feature_mapper import map_score_explanation_to_features
        from agent.tools.edge_creator import create_edge_with_evidence
        
        for candidate in results:
            try:
                # Map features
                features = map_score_explanation_to_features(candidate)
                
                # Create or update candidate node
                cand_id = str(candidate["node_id"])
                if cand_id not in self.graph.nodes:
                    cand_node = Node(
                        id=cand_id,
                        type="structure" if candidate["collection"] == "structures" else "sequence",
                        label=cand_id,
                        metadata={
                            "source": "retrieval",
                            "collection": candidate["collection"],
                            "score_explanation": candidate.get("score_explanation"),
                            "biological_features": candidate.get("biological_features", {}),
                            "provenance": {
                                "query_vector_hash": candidate["query_vector_hash"],
                                "raw_qdrant_result": candidate
                            }
                        }
                    )
                    self.graph.add_node(cand_node)
                    self.processing_stats["retrieved_nodes"] += 1
                
                # Create edge
                edge = create_edge_with_evidence(
                    from_node_id=source_node.id,
                    to_node_id=cand_id,
                    score=candidate["score"],
                    evidence=features,
                    provenance={
                        "collection": candidate["collection"],
                        "id": cand_id,
                        "query_vector_hash": candidate["query_vector_hash"]
                    }
                )
                
                self.graph.add_edge(edge)
                self.processing_stats["edges_created"] += 1
                
            except Exception as e:
                logger.error(f"Error processing candidate {candidate.get('node_id')}: {str(e)}")
    
    def expand_node_direction(self, node_id: str, direction: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Expand a specific node in a given direction."""
        print(f"=== STARTING NODE EXPANSION: expand_node_direction(node_id={node_id}, direction={direction}) ===")
        from agent.tools.retriever import retrieve_candidates
        from agent.tools.feature_mapper import map_score_explanation_to_features
        from agent.tools.edge_creator import create_edge_with_evidence
        
        if params is None:
            params = {}
            
        node = self.graph.nodes.get(node_id)
        if not node:
            return {"error": f"Node {node_id} not found"}
        
        results = []
        
        if direction == "similar_proteins":
            # Get embedding
            embedding = node.embedding
            if not embedding:
                return {"error": f"Node {node_id} has no embedding"}
            
            # Get feature mask from node's top dimensions if available
            feature_mask = params.get("feature_mask")
            if not feature_mask and node.metadata.get("score_explanation"):
                # Build mask from top dimensions
                top_dims = node.metadata["score_explanation"].get("top_dimensions", [])
                if top_dims:
                    # Simple mask: boost top dimensions
                    feature_mask = [0.1] * 1280  # Default low weight
                    for dim_info in top_dims[:5]:  # Top 5 dimensions
                        dim = dim_info.get("dimension", 0)
                        if 0 <= dim < 1280:
                            feature_mask[dim] = 1.0
            
            # Retrieve
            print(f"TOOL CALL: retrieve_candidates(embedding_length={len(embedding)}, collections={params.get('collections', ['structures', 'uniprot_sequences'])}, n={params.get('n', 20)}, has_feature_mask={feature_mask is not None})")
            candidates = retrieve_candidates(
                embedding,
                collections=params.get("collections", ["structures", "uniprot_sequences"]),
                n=params.get("n", 20),
                feature_mask=feature_mask
            )
            print(f"TOOL RESULT: retrieve_candidates returned {len(candidates)} candidates")
            
            # Process results
            for candidate in candidates:
                print(f"TOOL CALL: map_score_explanation_to_features(candidate_id={candidate.get('node_id')})")
                features = map_score_explanation_to_features(candidate)
                print(f"TOOL RESULT: map_score_explanation_to_features returned {len(features)} features")
                
                # Create node if doesn't exist
                cand_id = candidate["node_id"]
                if cand_id not in self.graph.nodes:
                    cand_node = Node(
                        id=cand_id,
                        type="structure" if candidate["collection"] == "structures" else "sequence",
                        label=cand_id,
                        metadata={
                            "source": "expansion",
                            "collection": candidate["collection"],
                            "score_explanation": candidate.get("score_explanation"),
                            "biological_features": candidate.get("biological_features", {})
                        }
                    )
                    self.graph.add_node(cand_node)
                
                # Create edge
                print(f"TOOL CALL: create_edge_with_evidence(from_id={node_id}, to_id={cand_id}, score={candidate['score']}, features_count={len(features)})")
                edge = create_edge_with_evidence(
                    from_node_id=node_id,
                    to_node_id=cand_id,
                    score=candidate["score"],
                    evidence=features,
                    provenance={
                        "collection": candidate["collection"],
                        "id": cand_id,
                        "query_vector_hash": candidate["query_vector_hash"],
                        "expansion_direction": direction
                    }
                )
                print(f"TOOL RESULT: create_edge_with_evidence created edge with type={edge.type}")
                
                self.graph.add_edge(edge)
                results.append({
                    "candidate_id": cand_id,
                    "score": candidate["score"],
                    "features": features
                })
                
        elif direction == "papers":
            # Stub for paper retrieval
            results = [{"stub": "paper_retrieval_not_implemented"}]
        else:
            return {"error": f"Unknown direction: {direction}"}
        
        print(f"=== NODE EXPANSION COMPLETE: Created {len(results)} edges for {direction} ===")
        return {
            "expanded_node": node_id,
            "direction": direction,
            "results": results,
            "edges_created": len(results)
        }
    
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
            logger.info(f"Iteration {iteration + 1} - Retrieval Strategy: continue={strategy.get('continue_retrieval', True)}, queries={strategy.get('suggested_queries', [])}")
            
            if strategy.get("stop_criteria_met", False) or not strategy.get("continue_retrieval", True):
                logger.info(f"Stopping retrieval at iteration {iteration + 1}")
                break
            
            # Perform retrievals based on strategy
            self._execute_retrieval_strategy(strategy)
            
            self.processing_stats["retrieval_iterations"] = iteration + 1
    
    def _execute_retrieval_strategy(self, strategy: Dict[str, Any]):
        """Execute the retrieval strategy."""
        suggested_queries = strategy.get("suggested_queries", [])
        logger.info(f"Executing retrieval for queries: {suggested_queries[:3]}")
        
        for query in suggested_queries[:3]:  # Limit to 3 queries per iteration
            try:
                logger.info(f"Processing query: {query}")
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
                embedding=None,
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
        if hasattr(web_search, "resolve_protein_name"):
            return web_search.resolve_protein_name(name)
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
