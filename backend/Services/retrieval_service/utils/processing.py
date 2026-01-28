"""
Utility functions for content processing, embedding generation, and graph operations.
"""

import hashlib
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import logging
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)

def generate_content_hash(content: str) -> str:
    """Generate a consistent hash for content to detect duplicates."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def generate_node_id(content_type: str, content: str, name: str = "") -> str:
    """Generate a unique node ID based on content."""
    identifier = f"{content_type}_{name}_{generate_content_hash(content)}"
    return identifier.lower().replace(' ', '_').replace('-', '_')

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity based on word overlap."""
    if not text1 or not text2:
        return 0.0
    
    # Simple word-based similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def extract_key_terms(text: str, max_terms: int = 20) -> List[str]:
    """Extract key terms from text using simple frequency analysis."""
    if not text:
        return []
    
    # Clean and tokenize
    text = text.lower()
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    
    # Filter out common words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these', 
        'those', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 
        'could', 'should', 'may', 'might', 'can', 'are', 'is', 'am', 'be'
    }
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Count frequency and return top terms
    word_counts = Counter(filtered_words)
    return [word for word, _ in word_counts.most_common(max_terms)]

def merge_metadata(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two metadata dictionaries intelligently."""
    result = existing.copy()
    
    for key, value in new.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], list) and isinstance(value, list):
            # Merge lists and remove duplicates
            combined = result[key] + value
            result[key] = list(dict.fromkeys(combined))  # Preserve order
        elif isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            result[key] = merge_metadata(result[key], value)
        elif result[key] != value:
            # Handle conflicts by keeping both values
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            if value not in result[key]:
                result[key].append(value)
    
    return result

class GraphAnalyzer:
    """Utility class for analyzing graph structure and properties."""
    
    @staticmethod
    def calculate_node_centrality(graph_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate degree centrality for nodes."""
        nodes = {node["id"]: node for node in graph_data.get("nodes", [])}
        edges = graph_data.get("edges", [])
        
        # Count connections for each node
        degree_count = defaultdict(int)
        for edge in edges:
            degree_count[edge["from_id"]] += 1
            degree_count[edge["to_id"]] += 1
        
        # Normalize by maximum possible connections
        max_degree = max(degree_count.values()) if degree_count else 1
        centrality = {node_id: count / max_degree for node_id, count in degree_count.items()}
        
        # Include isolated nodes
        for node_id in nodes.keys():
            if node_id not in centrality:
                centrality[node_id] = 0.0
        
        return centrality
    
    @staticmethod
    def find_node_clusters(graph_data: Dict[str, Any], 
                          similarity_threshold: float = 0.7) -> List[List[str]]:
        """Find clusters of similar nodes."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # Build adjacency list for similarity edges
        similarity_graph = defaultdict(set)
        for edge in edges:
            if (edge.get("type") == "similarity" and 
                edge.get("score", 0) >= similarity_threshold):
                similarity_graph[edge["from_id"]].add(edge["to_id"])
                similarity_graph[edge["to_id"]].add(edge["from_id"])
        
        # Find connected components (simple clustering)
        visited = set()
        clusters = []
        
        def dfs(node_id: str, cluster: List[str]):
            if node_id in visited:
                return
            visited.add(node_id)
            cluster.append(node_id)
            
            for neighbor in similarity_graph[node_id]:
                dfs(neighbor, cluster)
        
        for node in nodes:
            node_id = node["id"]
            if node_id not in visited:
                cluster = []
                dfs(node_id, cluster)
                if len(cluster) > 1:  # Only include multi-node clusters
                    clusters.append(cluster)
        
        return clusters
    
    @staticmethod
    def identify_key_nodes(graph_data: Dict[str, Any], 
                         top_k: int = 10) -> List[Dict[str, Any]]:
        """Identify the most important nodes based on multiple criteria."""
        nodes = graph_data.get("nodes", [])
        centrality = GraphAnalyzer.calculate_node_centrality(graph_data)
        
        # Score nodes based on multiple factors
        scored_nodes = []
        for node in nodes:
            node_id = node["id"]
            score = (
                centrality.get(node_id, 0) * 0.4 +  # Network centrality
                node.get("relevance_score", 0) * 0.6  # Content relevance
            )
            
            scored_nodes.append({
                **node,
                "importance_score": score,
                "centrality": centrality.get(node_id, 0)
            })
        
        # Sort by importance and return top k
        scored_nodes.sort(key=lambda x: x["importance_score"], reverse=True)
        return scored_nodes[:top_k]
    
    @staticmethod
    def analyze_graph_coverage(graph_data: Dict[str, Any], 
                             objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well the graph covers the research objectives."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # Analyze node types coverage
        node_types = Counter(node.get("type", "unknown") for node in nodes)
        
        # Analyze relevance distribution
        relevance_scores = [node.get("relevance_score", 0) for node in nodes]
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0
        
        # Analyze connectivity
        total_possible_edges = len(nodes) * (len(nodes) - 1) / 2
        edge_density = len(edges) / total_possible_edges if total_possible_edges > 0 else 0
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_type_distribution": dict(node_types),
            "average_relevance": avg_relevance,
            "high_relevance_nodes": len([s for s in relevance_scores if s > 0.7]),
            "edge_density": edge_density,
            "connectivity_assessment": "well-connected" if edge_density > 0.1 else "sparse",
            "coverage_completeness": min(1.0, len(nodes) / 20)  # Assume 20 nodes is "complete"
        }

class ContentProcessor:
    """Utility class for processing and analyzing content."""
    
    @staticmethod
    def detect_content_language(text: str) -> str:
        """Detect the primary language of text content."""
        # Simple heuristic based on common words
        english_indicators = ['the', 'and', 'of', 'to', 'a', 'in', 'is', 'it', 'you', 'that']
        german_indicators = ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich']
        french_indicators = ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir']
        
        words = text.lower().split()[:100]  # Check first 100 words
        
        english_score = sum(1 for word in words if word in english_indicators)
        german_score = sum(1 for word in words if word in german_indicators)
        french_score = sum(1 for word in words if word in french_indicators)
        
        if english_score >= german_score and english_score >= french_score:
            return "english"
        elif german_score >= french_score:
            return "german"
        else:
            return "french" if french_score > 0 else "unknown"
    
    @staticmethod
    def extract_numerical_data(text: str) -> List[Dict[str, Any]]:
        """Extract numerical measurements and data from text."""
        patterns = [
            (r'(\d+\.?\d*)\s*([μmMnNkK]?[gGlLmM])\b', 'measurement'),
            (r'(\d+\.?\d*)\s*°C\b', 'temperature'),
            (r'(\d+\.?\d*)\s*[pP][hH]\b', 'pH'),
            (r'(\d+\.?\d*)\s*[mM][Mm]\b', 'molarity'),
            (r'(\d+\.?\d*)\s*%', 'percentage'),
            (r'(\d+\.?\d*)x\b', 'magnification'),
        ]
        
        numerical_data = []
        for pattern, data_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                numerical_data.append({
                    "value": float(match.group(1)),
                    "unit": match.group(2) if len(match.groups()) > 1 else "",
                    "type": data_type,
                    "context": text[max(0, match.start()-50):match.end()+50]
                })
        
        return numerical_data
    
    @staticmethod
    def categorize_content_by_domain(content: str) -> Dict[str, float]:
        """Categorize content by scientific domain based on keyword analysis."""
        domains = {
            "biochemistry": ["protein", "enzyme", "amino", "peptide", "biochemical", "metabolic"],
            "molecular_biology": ["dna", "rna", "gene", "genome", "molecular", "sequence"],
            "structural_biology": ["crystal", "structure", "fold", "domain", "conformation"],
            "pharmacology": ["drug", "compound", "inhibitor", "binding", "therapeutic"],
            "biophysics": ["energy", "thermodynamic", "kinetic", "binding", "interaction"],
            "cell_biology": ["cell", "cellular", "membrane", "organelle", "cytoplasm"],
            "computational": ["algorithm", "model", "simulation", "computational", "analysis"]
        }
        
        content_lower = content.lower()
        domain_scores = {}
        
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            domain_scores[domain] = score / len(keywords)  # Normalize
        
        return domain_scores

def create_embedding_placeholder(content: str, dimension: int = 1280) -> List[float]:
    """Create a placeholder embedding based on content hash (for testing)."""
    # In production, replace with actual embedding generation
    content_hash = hashlib.sha256(content.encode('utf-8')).digest()
    
    # Create deterministic "embedding" from hash
    np.random.seed(int.from_bytes(content_hash[:4], byteorder='big'))
    embedding = np.random.randn(dimension).tolist()
    
    return embedding

def validate_graph_structure(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate graph structure and identify potential issues."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    issues = []
    warnings = []
    
    # Check for duplicate node IDs
    node_ids = [node.get("id") for node in nodes]
    duplicate_ids = [id for id, count in Counter(node_ids).items() if count > 1]
    if duplicate_ids:
        issues.append(f"Duplicate node IDs found: {duplicate_ids}")
    
    # Check for orphaned edges
    valid_node_ids = set(node_ids)
    orphaned_edges = []
    for edge in edges:
        if edge.get("from_id") not in valid_node_ids or edge.get("to_id") not in valid_node_ids:
            orphaned_edges.append(edge)
    
    if orphaned_edges:
        issues.append(f"Found {len(orphaned_edges)} edges referencing non-existent nodes")
    
    # Check for isolated nodes
    connected_nodes = set()
    for edge in edges:
        connected_nodes.add(edge.get("from_id"))
        connected_nodes.add(edge.get("to_id"))
    
    isolated_nodes = valid_node_ids - connected_nodes
    if len(isolated_nodes) > len(nodes) * 0.3:  # More than 30% isolated
        warnings.append(f"High number of isolated nodes: {len(isolated_nodes)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "isolated_nodes": len(isolated_nodes),
        "connectivity_ratio": len(connected_nodes) / len(nodes) if nodes else 0
    }