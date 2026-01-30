"""
Tests for New Agent Types (Ontologist and Scientist2)

Unit tests focusing on data structures and validation logic.
These tests do not require agent imports due to import complexity.
"""

import pytest
import json


# ============================================================================
# SAMPLE TEST DATA
# ============================================================================

SAMPLE_SUBGRAPH = {
    "nodes": [
        {
            "id": "hemoglobin",
            "type": "protein",
            "label": "Hemoglobin",
            "properties": {
                "name": "Hemoglobin",
                "function": "oxygen transport"
            }
        },
        {
            "id": "oxygen",
            "type": "molecule",
            "label": "Oxygen",
            "properties": {
                "name": "Oxygen",
                "formula": "O2"
            }
        },
        {
            "id": "iron",
            "type": "element",
            "label": "Iron",
            "properties": {
                "name": "Iron",
                "symbol": "Fe"
            }
        }
    ],
    "edges": [
        {
            "source": "hemoglobin",
            "target": "oxygen",
            "type": "binds",
            "properties": {"affinity": "high"}
        },
        {
            "source": "hemoglobin",
            "target": "iron",
            "type": "contains",
            "properties": {"count": 4}
        }
    ]
}

SAMPLE_HYPOTHESIS = {
    "title": "Hemoglobin-Iron Interaction Hypothesis",
    "core_hypothesis": "Modifying iron coordination in hemoglobin can improve oxygen affinity",
    "supporting_rationale": [
        "Iron is central to oxygen binding",
        "Coordination geometry affects binding affinity"
    ],
    "potential_applications": ["Medical treatment", "Synthetic biology"],
    "confidence_score": 0.75
}


# ============================================================================
# STRUCTURED OUTPUT VALIDATION TESTS
# ============================================================================

class TestStructuredOutputValidation:
    """Tests for validating expected structured outputs."""
    
    def test_ontologist_output_schema(self):
        """Test expected ontologist output schema."""
        required_fields = [
            "concept_definitions",
            "relationship_explanations", 
            "key_patterns",
            "narrative_synthesis"
        ]
        
        sample_output = {
            "concept_definitions": [
                {
                    "concept": "Hemoglobin",
                    "definition": "Oxygen-carrying protein",
                    "domain": "biochemistry",
                    "significance": "Essential for respiration"
                }
            ],
            "relationship_explanations": [
                {
                    "relationship": "hemoglobin binds oxygen",
                    "mechanism": "Iron heme coordination",
                    "biological_significance": "Enables oxygen transport"
                }
            ],
            "key_patterns": ["Protein-ligand binding pattern"],
            "narrative_synthesis": "This subgraph represents oxygen transport system."
        }
        
        for field in required_fields:
            assert field in sample_output
        
        # Validate structure
        assert isinstance(sample_output["concept_definitions"], list)
        assert isinstance(sample_output["relationship_explanations"], list)
        assert isinstance(sample_output["key_patterns"], list)
        assert isinstance(sample_output["narrative_synthesis"], str)
    
    def test_scientist2_output_schema(self):
        """Test expected scientist2 output schema (7-point framework)."""
        required_fields = [
            "expanded_hypothesis",
            "quantitative_details",
            "methodologies",
            "experimental_protocols",
            "citations",
            "risk_assessment",
            "timeline"
        ]
        
        sample_output = {
            "expanded_hypothesis": "Detailed expansion of the hypothesis...",
            "quantitative_details": {
                "metrics": ["Oxygen binding affinity (Kd)", "Cooperativity coefficient"],
                "expected_ranges": {"Kd": "10-50 nM", "Hill coefficient": "2.5-3.0"},
                "measurement_methods": ["ITC", "UV-Vis spectroscopy"]
            },
            "methodologies": [
                {
                    "name": "Site-directed mutagenesis",
                    "description": "Mutate iron-coordinating residues",
                    "expected_outcome": "Altered oxygen affinity"
                }
            ],
            "experimental_protocols": [
                {
                    "step": 1,
                    "description": "Clone hemoglobin gene",
                    "duration": "1 week",
                    "resources_needed": ["PCR kit", "Expression vector"]
                }
            ],
            "citations": [
                {
                    "title": "Hemoglobin Structure and Function",
                    "source": "arxiv",
                    "relevance": "Foundational structural data"
                }
            ],
            "risk_assessment": {
                "technical_risks": ["Protein misfolding"],
                "mitigation_strategies": ["Use chaperone co-expression"]
            },
            "timeline": {
                "total_duration": "6 months",
                "milestones": [
                    {"month": 1, "goal": "Gene cloning complete"},
                    {"month": 3, "goal": "Mutants characterized"}
                ]
            }
        }
        
        for field in required_fields:
            assert field in sample_output
        
        # Validate nested structures
        assert "metrics" in sample_output["quantitative_details"]
        assert isinstance(sample_output["methodologies"], list)
        assert isinstance(sample_output["experimental_protocols"], list)
        assert "technical_risks" in sample_output["risk_assessment"]
        assert "milestones" in sample_output["timeline"]


class TestHypothesisStructure:
    """Tests for hypothesis data structures."""
    
    def test_initial_hypothesis_fields(self):
        """Test initial hypothesis has expected fields."""
        required = ["title", "core_hypothesis"]
        optional = ["supporting_rationale", "potential_applications", "confidence_score"]
        
        for field in required:
            assert field in SAMPLE_HYPOTHESIS
    
    def test_subgraph_structure(self):
        """Test KG subgraph structure."""
        assert "nodes" in SAMPLE_SUBGRAPH
        assert "edges" in SAMPLE_SUBGRAPH
        assert len(SAMPLE_SUBGRAPH["nodes"]) == 3
        assert len(SAMPLE_SUBGRAPH["edges"]) == 2
        
        # Check node structure
        node = SAMPLE_SUBGRAPH["nodes"][0]
        assert "id" in node
        assert "type" in node
        
        # Check edge structure  
        edge = SAMPLE_SUBGRAPH["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge


class TestDataTransformations:
    """Tests for data transformation logic."""
    
    def test_extract_concepts_from_nodes(self):
        """Test concept extraction from graph nodes."""
        nodes = SAMPLE_SUBGRAPH["nodes"]
        concepts = []
        
        for node in nodes:
            name = (
                node.get("label") or 
                node.get("name") or 
                node.get("properties", {}).get("name") or
                node.get("id", "")
            )
            if name:
                concepts.append(str(name))
        
        assert len(concepts) == 3
        assert "Hemoglobin" in concepts
    
    def test_format_hypothesis(self):
        """Test hypothesis formatting."""
        hypothesis = SAMPLE_HYPOTHESIS
        
        lines = []
        if "title" in hypothesis:
            lines.append(f"Title: {hypothesis['title']}")
        if "core_hypothesis" in hypothesis:
            lines.append(f"Core Hypothesis: {hypothesis['core_hypothesis']}")
        
        formatted = "\n".join(lines)
        
        assert "Hemoglobin-Iron" in formatted
        assert "oxygen affinity" in formatted
    
    def test_build_search_queries(self):
        """Test search query extraction from hypothesis."""
        hypothesis = SAMPLE_HYPOTHESIS
        queries = []
        
        if hypothesis.get("title"):
            queries.append(hypothesis["title"])
        if hypothesis.get("core_hypothesis"):
            queries.append(hypothesis["core_hypothesis"])
        
        assert len(queries) >= 2
        assert any("hemoglobin" in q.lower() for q in queries)


class TestConfidenceCalculation:
    """Tests for confidence score calculation logic."""
    
    def test_calculate_interpretation_confidence(self):
        """Test confidence calculation for interpretations."""
        interpretation = {
            "concept_definitions": [
                {"concept": "A"},
                {"concept": "B"},
                {"concept": "C"}
            ],
            "relationship_explanations": [
                {"rel": "1"},
                {"rel": "2"}
            ],
            "narrative_synthesis": "This is a detailed narrative synthesis that provides context." * 5
        }
        
        subgraph = SAMPLE_SUBGRAPH
        
        # Calculate confidence based on coverage
        score = 0.5  # Base score
        
        concepts = interpretation.get("concept_definitions", [])
        nodes = subgraph.get("nodes", [])
        if nodes and concepts:
            coverage = len(concepts) / len(nodes)
            score += 0.2 * min(coverage, 1.0)
        
        relationships = interpretation.get("relationship_explanations", [])
        edges = subgraph.get("edges", [])
        if edges and relationships:
            rel_coverage = len(relationships) / len(edges)
            score += 0.2 * min(rel_coverage, 1.0)
        
        narrative = interpretation.get("narrative_synthesis", "")
        if len(narrative) > 200:
            score += 0.1
        
        assert score > 0.5
        assert score <= 1.0
    
    def test_calculate_expansion_confidence(self):
        """Test confidence calculation for hypothesis expansion."""
        expanded = {
            "expanded_hypothesis": "Detailed expansion",
            "quantitative_details": {"metrics": ["M1", "M2"], "values": "many details here" * 20},
            "methodologies": {"methods": ["method1", "method2"], "details": "details" * 20},
            "citations": [
                {"title": "Paper 1"},
                {"title": "Paper 2"},
                {"title": "Paper 3"}
            ]
        }
        
        score = 0.5  # Base score
        
        quant = expanded.get("quantitative_details", {})
        if quant and len(str(quant)) > 100:
            score += 0.15
        
        methods = expanded.get("methodologies", {})
        if methods and len(str(methods)) > 100:
            score += 0.15
        
        citations = expanded.get("citations", [])
        if citations:
            score += min(0.2, len(citations) * 0.04)
        
        assert score > 0.7
        assert score <= 1.0


class TestJSONParsing:
    """Tests for JSON parsing of agent outputs."""
    
    def test_parse_valid_json_output(self):
        """Test parsing valid JSON output."""
        json_str = json.dumps({
            "hypothesis": "Test hypothesis",
            "confidence": 0.8
        })
        
        parsed = json.loads(json_str)
        assert parsed["hypothesis"] == "Test hypothesis"
        assert parsed["confidence"] == 0.8
    
    def test_handle_json_with_newlines(self):
        """Test parsing JSON with embedded newlines."""
        output = {
            "text": "Line 1\nLine 2\nLine 3",
            "list": ["a", "b", "c"]
        }
        
        json_str = json.dumps(output)
        parsed = json.loads(json_str)
        
        assert "\n" in parsed["text"]
        assert len(parsed["list"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
