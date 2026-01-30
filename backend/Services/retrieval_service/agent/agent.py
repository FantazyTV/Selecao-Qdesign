"""
Simplified MultiModal Retrieval Agent that uses high-level tools to build graphs
and LLM only for processing stats, summary, and notes.
"""

import os
import logging
from utils.tool_logger import tool_logger
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from utils.models import ProcessingRequest, GraphAnalysisResponse, GraphData, GraphNode, GraphEdge
from agent.high_level_tools.protein_graph_from_query import build_protein_graph_from_query
from agent.high_level_tools.protein_graph_from_sequence import build_protein_graph_from_sequence
from agent.high_level_tools.protein_graph_from_cif import build_protein_graph_from_cif
from graph.graph_merge_utils import merge_graphs


load_dotenv()
logger = logging.getLogger(__name__)
# Dedicated debug logger for tool/LLM IO
agent_debug_logger = logging.getLogger("agent_debug")
if not agent_debug_logger.handlers:
    handler = logging.FileHandler("agent_debug.log")
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    agent_debug_logger.addHandler(handler)
    agent_debug_logger.setLevel(logging.INFO)

class MultiModalRetrievalAgent:
    """Simplified agent that processes data pools using high-level tools."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=60.0
        )
    
    def process_data_pool_request(self, request: ProcessingRequest) -> GraphAnalysisResponse:
        """Process the data pool request and return graph analysis."""
        logger.info(f"Processing request: {request.name}")
        print(f"[DEBUG] Starting process_data_pool_request for: {request.name}")
        print(f"[DEBUG] Data pool has {len(request.dataPool)} items")
        
        # Collect all graphs from different tools
        graphs = []
        processing_stats = {
            "total_items": len(request.dataPool),
            "processed_items": 0,
            "processing_started": datetime.now().isoformat(),
            "item_breakdown": {}
        }
        
        for item in request.dataPool:
            try:
                print(f"[DEBUG] Processing item: {item.name} (type: {item.type})")
                graph = self._process_single_item(item)
                print(f"[DEBUG] Got graph result: {type(graph)} - {graph is not None}")
                if graph:
                    print(f"[DEBUG] Graph has {len(graph.get('nodes', []))} nodes and {len(graph.get('edges', []))} edges")
                if graph and (graph.get("nodes") or graph.get("edges")):
                    graphs.append(graph)
                    processing_stats["processed_items"] += 1
                    print(f"[DEBUG] Added graph to collection. Total graphs: {len(graphs)}")
                else:
                    print(f"[DEBUG] Skipping empty/invalid graph for {item.name}")
                    
                # Track by type
                item_type = item.type
                if item_type not in processing_stats["item_breakdown"]:
                    processing_stats["item_breakdown"][item_type] = 0
                processing_stats["item_breakdown"][item_type] += 1
                
            except Exception as e:
                print(f"[ERROR] Exception processing item {item.name}: {str(e)}")
                logger.error(f"Error processing item {item.name}: {str(e)}")
                continue
        
        # Merge all graphs
        print(f"[DEBUG] About to merge {len(graphs)} graphs")
        if graphs:
            print(f"[DEBUG] Calling merge_graphs with {len(graphs)} graphs")
            merged_graph = merge_graphs(graphs)
            print(f"[DEBUG] merge_graphs returned: {type(merged_graph)} - {merged_graph is not None}")
            if merged_graph:
                print(f"[DEBUG] Merged graph has {len(merged_graph.get('nodes', []))} nodes and {len(merged_graph.get('edges', []))} edges")
        else:
            print(f"[DEBUG] No graphs to merge, using empty graph")
            merged_graph = {"nodes": [], "edges": []}

        # Log merged graph before converting
        tool_logger.log_tool_call("merge_graphs", {"graphs_count": len(graphs)}, merged_graph)

        # Convert to API format
        print(f"[DEBUG] About to convert to API format")
        # graph_data = self._convert_to_api_format(merged_graph)
        # print(f"[DEBUG] API conversion completed. GraphData has {len(graph_data['nodes'])} nodes")
        
        # Generate summary and notes using LLM
        print(f"[DEBUG] About to generate summary and notes")

        try:
            summary, notes = self._generate_summary_and_notes(request, processing_stats, merged_graph)
        except:
            summary, notes = "Summary generation is currently disabled.", []
        print(f"[DEBUG] Generated summary: {summary[:100] if summary else 'None'}...")
        print(f"[DEBUG] Generated {len(notes)} notes")
        
        processing_stats["processing_completed"] = datetime.now().isoformat()
        print(f"[DEBUG] Processing completed successfully")
        
        return GraphAnalysisResponse(
            graph=merged_graph,
            summary=summary,
            processing_stats=processing_stats,
            notes=notes
        )
    
    def _process_single_item(self, item) -> Dict[str, Any]:
        """Process a single data pool item using appropriate high-level tool, with debug logging and persistent log file."""
        logger.info(f"Processing item: {item.name} (type: {item.type})")
        tool_input = {"type": item.type, "name": item.name, "content": item.content}
        tool_output = None
        try:
            if item.type.lower() in ['pdb', 'structure']:
                if item.content and len(item.content.strip()) <= 10:
                    tool_output = build_protein_graph_from_query(item.content.strip())
                    if tool_output is None:
                        print(f"[WARNING] build_protein_graph_from_query returned None for {item.name}")
                        tool_output = {"nodes": [], "edges": []}
                    tool_logger.log_tool_call("build_protein_graph_from_query", tool_input, tool_output)
                    return tool_output
                elif item.content:
                    tool_output = build_protein_graph_from_cif(item.content)
                    if tool_output is None:
                        print(f"[WARNING] build_protein_graph_from_cif returned None for {item.name}")
                        tool_output = {"nodes": [], "edges": []}
                    tool_logger.log_tool_call("build_protein_graph_from_cif", tool_input, tool_output)
                    return tool_output
            elif item.type.lower() in ['sequence', 'fasta']:
                if item.content:
                    tool_output = build_protein_graph_from_sequence(item.content)
                    if tool_output is None:
                        print(f"[WARNING] build_protein_graph_from_sequence returned None for {item.name}")
                        tool_output = {"nodes": [], "edges": []}
                    tool_logger.log_tool_call("build_protein_graph_from_sequence", tool_input, tool_output)
                    return tool_output
            elif item.type.lower() == 'text':
                if item.content:
                    content = item.content.strip()
                    if len(content) <= 10 and content.isalnum():
                        tool_output = build_protein_graph_from_query(content)
                        if tool_output is None:
                            print(f"[WARNING] build_protein_graph_from_query returned None for {item.name}")
                            tool_output = {"nodes": [], "edges": []}
                        tool_logger.log_tool_call("build_protein_graph_from_query", tool_input, tool_output)
                        return tool_output
                    elif self._looks_like_sequence(content):
                        tool_output = build_protein_graph_from_sequence(content)
                        if tool_output is None:
                            print(f"[WARNING] build_protein_graph_from_sequence returned None for {item.name}")
                            tool_output = {"nodes": [], "edges": []}
                        tool_logger.log_tool_call("build_protein_graph_from_sequence", tool_input, tool_output)
                        return tool_output
            if item.content and len(item.content.strip()) <= 10:
                tool_output = build_protein_graph_from_query(item.content.strip())
                if tool_output is None:
                    print(f"[WARNING] build_protein_graph_from_query returned None for {item.name}")
                    tool_output = {"nodes": [], "edges": []}
                tool_logger.log_tool_call("build_protein_graph_from_query", tool_input, tool_output)
                return tool_output
            logger.warning(f"Could not process item {item.name} of type {item.type}")
            tool_logger.log_tool_call("unknown type", tool_input, {"nodes": [], "edges": []})
            return {"nodes": [], "edges": []}
        except Exception as e:
            tool_logger.log_tool_call("tool_error", tool_input, f"Exception: {str(e)}")
            raise
    
    def _looks_like_sequence(self, content: str) -> bool:
        """Check if content looks like a protein sequence."""
        if not content or len(content) < 10:
            return False
        
        # Common amino acid letters
        amino_acids = set('ACDEFGHIKLMNPQRSTVWY')
        content_upper = content.upper().replace('\n', '').replace(' ', '')
        
        if len(content_upper) < 10:
            return False
        
        # Check if most characters are amino acids
        amino_acid_count = sum(1 for c in content_upper if c in amino_acids)
        return amino_acid_count / len(content_upper) > 0.8
    
    def _convert_to_api_format(self, graph: Dict[str, Any]) -> GraphData:
        """Convert merged graph to API format."""
        print(f"[DEBUG] _convert_to_api_format called with graph type: {type(graph)}")
        if graph is None:
            print(f"[ERROR] Graph is None in _convert_to_api_format!")
            return GraphData(nodes=[], edges=[], metadata={})
        
        nodes = []
        edges = []
        
        print(f"[DEBUG] Graph keys: {list(graph.keys()) if graph else 'None'}")
        raw_nodes = graph.get("nodes", [])
        print(f"[DEBUG] Found {len(raw_nodes)} raw nodes")
        
        # Convert nodes
        for i, node in enumerate(raw_nodes):
            print(f"[DEBUG] Processing node {i}: {node}")
            if node is None:
                print(f"[ERROR] Node {i} is None!")
                continue
                
            node_type = node.get("type", "concept")
            if node_type == "annotation":
                print(f"[DEBUG] Converting annotation type to concept for node {node.get('id')}")
                node_type = "concept"
            
            try:
                api_node = GraphNode(
                    id=str(node.get("id", "")),
                    type=node_type,
                    label=node.get("label", node.get("name", "Unknown")),
                    metadata=node.get("metadata", {}),
                    content_summary=node.get("metadata", {}).get("sequence", "")[:100] if node.get("metadata") else None,
                    relevance_score=node.get("score", 1.0)
                )
                nodes.append(api_node)
                print(f"[DEBUG] Successfully converted node {i}")
            except Exception as e:
                print(f"[ERROR] Failed to convert node {i}: {str(e)}")
                print(f"[ERROR] Node data: {node}")
                continue
        
        # Convert edges
        raw_edges = graph.get("edges", [])
        print(f"[DEBUG] Found {len(raw_edges)} raw edges")
        
        for i, edge in enumerate(raw_edges):
            print(f"[DEBUG] Processing edge {i}: {edge}")
            if edge is None:
                print(f"[ERROR] Edge {i} is None!")
                continue
                
            try:
                api_edge = GraphEdge(
                    from_id=str(edge.get("from_id", edge.get("source", ""))),
                    to_id=str(edge.get("to_id", edge.get("target", ""))),
                    type=edge.get("type", edge.get("label", "relates_to")),
                    score=edge.get("score", edge.get("strength", 1.0)),
                    evidence=edge.get("evidence", ""),
                    provenance=edge.get("provenance", {})
                )
                edges.append(api_edge)
                print(f"[DEBUG] Successfully converted edge {i}")
            except Exception as e:
                print(f"[ERROR] Failed to convert edge {i}: {str(e)}")
                print(f"[ERROR] Edge data: {edge}")
                continue
        
        print(f"[DEBUG] Returning GraphData with {len(nodes)} nodes and {len(edges)} edges")
        return GraphData(
            nodes=nodes,
            edges=edges,
            metadata=graph.get("metadata", {})
        )
    
    def _generate_summary_and_notes(self, request: ProcessingRequest, stats: Dict[str, Any], graph_data: GraphData) -> tuple:
        """Generate summary and notes using LLM."""
        try:
            # Prepare context for LLM
            context = {
                "objective": request.mainObjective,
                "secondary_objectives": request.secondaryObjectives,
                "constraints": request.constraints,
                "user_notes": request.notes,
                "processing_stats": stats,
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", [])),
                "node_types": list(set(node.type for node in graph_data.get("nodes", []))),
                "edge_types": list(set(edge.type for edge in graph_data.get("edges", [])))
            }
            
            prompt = f"""
Based on the following analysis context, provide a concise summary and helpful notes:

Main Objective: {request.mainObjective}
Secondary Objectives: {', '.join(request.secondaryObjectives) if request.secondaryObjectives else 'None'}
Constraints: {', '.join(request.constraints) if request.constraints else 'None'}
User Notes: {', '.join(request.notes) if request.notes else 'None'}

Processing Results:
- Total data items: {stats['total_items']}
- Successfully processed: {stats['processed_items']}
- Graph nodes: {len(graph_data.get("nodes", []))}
- Graph edges: {len(graph_data.get("edges", []))}
- Node types: {', '.join(set(node.type for node in graph_data.get("nodes", [])))}
- Item breakdown: {stats['item_breakdown']}

Please provide:
1. A summary (2-3 sentences) of what was analyzed and found
2. A list of 3-5 helpful notes about the analysis

Return as JSON with 'summary' and 'notes' fields.
"""
            
            response = self.client.chat.completions.create(

                extra_body={},
                model="google/gemma-3-27b-it:free",
                messages=[
                    {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": prompt
                        }
                    ]
                    }
                ]
                )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get("summary", "Analysis completed successfully."), result.get("notes", [])
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Processed {stats['processed_items']} out of {stats['total_items']} items successfully.", [
                f"Generated knowledge graph with {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges",
                f"Main objective: {request.mainObjective}",
                "Analysis completed with high-level protein analysis tools"
            ]