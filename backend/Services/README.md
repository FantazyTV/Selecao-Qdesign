# QDesign Services: Collaborative AI-Driven Protein Engineering Platform

## Project Vision

QDesign aims to solve a critical bottleneck in protein engineering: **fragmented knowledge and lack of explainable design reasoning**. Our platform enables researchers to:

1. **Find relevant knowledge** across diverse sources (proteins, papers, structures, experiments)
2. **Understand why** specific designs are suggested (explainability through knowledge graphs)
3. **Design proteins collaboratively** with AI that learns from feedback
4. **Close the loop** between design, synthesis, and experimental validation

---

## Current Implementation Status

### Phase 1: Data Foundation (✅ Complete)

We have built a **5-stage data processing pipeline** that transforms raw biological data into searchable, semantically meaningful representations:

```
Stage 1: Collection → Stage 2: Enrichment → Stage 3: Embedding → Stage 4: Storage → Stage 5: Retrieval
```

#### **Stage 1: Data Collectors**
- **AlphaFold Collector** (`alphafold_collector.py`): Fetches protein structure predictions and metadata from EBI's AlphaFold API (3 endpoints)
- **ArXiv Collector** (`arxiv_collector.py`): Gathers relevant papers on protein design, materials science, and biological engineering
- **BioRxiv Collector** (`biorxiv_collector.py`): Collects preprints from biological research domains
- **Extensible framework**: Base collector abstraction allows adding PDB, UniProt, GitHub, imaging data sources

**Output**: Raw metadata records with complete provenance (source, timestamp, URL, quality metrics)

#### **Stage 2: Metadata Enrichment**
- **AlphaFold Enricher** (`alphafold_enricher.py`): 
  - Analyzes confidence metrics (pLDDT, pAE scores)
  - Classifies structure quality (very_high, high, medium, low)
  - Generates use-case recommendations
  - Extracts design principles (hierarchical organization, multifunctionality)
  
- **Text Enricher**: Extracts concepts, relationships, methodologies from papers
- **Image Enricher**: Analyzes microscopy, diagrams for structural insights
- **Protein Enricher**: Adds functional annotations, domain information

**Output**: Semantically enriched metadata with quality classifications and contextual information

#### **Stage 3: Vector Embedding**
- **FastEmbedder** (`fastembed_embedder.py`): Generates 384-dimensional vectors using sentence-transformers
  - Embeds protein descriptions, paper abstracts, experimental protocols
  - Uses COSINE distance for semantic similarity
  - Normalizes vectors for consistent comparisons
  
- **ESM Embedder** (`esm_embedder.py`): Specialized protein sequence embeddings (for future use)

**Output**: Dense vector representations enabling semantic search and clustering

#### **Stage 4: Vector Storage**
- **Qdrant Backend** (`storage/qdrant_client.py`):
  - Persists vectors in Qdrant vector database (384-dimensional, COSINE metric)
  - Stores structured metadata payloads alongside vectors
  - Collection: `qdesign_structures` (proteins + related knowledge)
  
- **Metadata Storage**: Full enriched JSON payloads preserved with search results

**Output**: Queryable vector space with rich contextual information

#### **Stage 5: Semantic Retrieval**
- **Search API** (`search_api.py`): Query vectors against stored embeddings
- **Similarity Scoring**: Returns ranked results with relevance scores (0-1)
- **Filtering**: Support for metadata-based filtering (pLDDT scores, quality levels, data types)

**Output**: Ranked results with explanatory metadata ("why this result is relevant")

---

## Validated Use Case: AlphaFold Integration

We have **fully tested the entire pipeline** with AlphaFold protein predictions:

```
Input:  3 UniProt IDs (P69905 hemoglobin-α, P68871 hemoglobin-β, Q99895 proteasome)
         ↓
Collected:  3 structures, 3 model predictions, 9 total data points
            Quality scores: 92.5, 91.2, 87.8 (pLDDT)
         ↓
Enriched:  Quality classifications, design recommendations, use-case analysis
         ↓
Embedded:  3 vectors (384-dim, normalized)
         ↓
Stored:    Qdrant with metadata payloads (9 points total with duplicates from enrichment)
         ↓
Retrieved: Semantic search found 9 related structures, similarity scores 0.99-1.0
```

**Key Achievement**: Demonstrated that metadata is **persisted in Qdrant** as structured payloads, enabling:
- Semantic search without database hits
- Rich context preservation
- Fast retrieval with filtering capabilities

---

## SciAgents Paper Integration: Knowledge Graph Reasoning

The recent paper **"SciAgents: Automating Scientific Discovery Through Bioinspired Multi-Agent Intelligent Graph Reasoning"** provides the architectural blueprint for QDesign's **next evolutionary step**.

### Why SciAgents Fits Our Use Case

| Aspect | SciAgents Framework | QDesign Adaptation |
|--------|-------------------|-------------------|
| **Problem** | Materials scientists overwhelmed by fragmented knowledge | Protein engineers need design guidance from scattered sources |
| **Solution** | Ontological knowledge graph + multi-agent reasoning | Graph connecting proteins → properties → design principles |
| **Path Discovery** | Random/heuristic paths surface non-obvious relationships | "High-pLDDT proteins" → "hierarchical-structure" → "self-assembly" |
| **Agent Roles** | Ontologist, Scientist 1, Scientist 2, Critic | Domain experts analyzing design hypotheses |
| **Output** | Research hypotheses with 7 structured aspects | Design proposals with simulation priorities |
| **Novelty Check** | Semantic Scholar API against literature | Check against existing protein designs |

### Three Layers of Intelligence

#### **Layer 1: Data Foundation (Already Built ✅)**
```
Collectors → Enrichers → Embedders → Qdrant
```
This is the **raw material** for graph construction.

#### **Layer 2: Knowledge Graph (To Build)**
```
Nodes: Proteins, properties, design principles, experimental methods
Edges: "is_family_of", "has_property", "enables", "improves", "self_assembles_into"
Embeddings: Use existing 384-dim vectors for semantic similarity in pathfinding
```

**Key Difference from Naive Search**:
- Current search: Find proteins similar to query vector
- Graph-based search: Find **unexpected connection paths** between concepts
  - Example: "Hemoglobin" → "cooperative-binding" → "hierarchical-assembly" → "peptide-nanofibers"
  - Insight: "Could we design peptide nanofibers inspired by hemoglobin's cooperativity?"

#### **Layer 3: Multi-Agent Reasoning (To Build)**
```
User Query
  ↓
Graph Reasoning Service [Path Sampling]
  ↓
LLM Agents Chain:
  - Ontologist: Define concepts along path
  - Scientist 1: Generate initial design hypothesis
  - Scientist 2: Expand with quantitative details, simulation plans
  - Critic: Evaluate feasibility, identify experiments needed
  ↓
Structured Hypothesis (JSON)
  ↓
Project Storage + Explainability Trace
```

---

## Proposed Architecture: Graph Reasoning Service

```
                    ┌─────────────────────────────────┐
                    │     User / Project Service       │
                    │   (What properties to engineer?) │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │  Graph Reasoning Service (NEW)  │
                    │  ────────────────────────────   │
                    │ 1. Sample paths in KG            │
                    │ 2. Query Qdrant for context      │
                    │ 3. Call LLM agent chain          │
                    │ 4. Generate hypotheses           │
                    │ 5. Score novelty & feasibility   │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │  Design Hypothesis Storage       │
                    │  ────────────────────────────   │
                    │ - Structured JSON output         │
                    │ - Knowledge path explanation     │
                    │ - Simulation recommendations     │
                    │ - Experimental priorities        │
                    └─────────────────────────────────┘
```

---

## What the Research Paper Enables

### **Current Capability (Stage 5)**
```
Input:  "Find proteins similar to hemoglobin"
Output: 5 proteins with high sequence/structure similarity (obvious results)
```

### **New Capability (Graph Reasoning)**
```
Input:  "Design a biodegradable, high-strength biomaterial protein"
        Constraints: pLDDT > 90, target strength > 1.0 GPa, degradation 7-30 days
        
Output: Design Hypothesis
  {
    "hypothesis": "Engineer AlphaFold protein with hierarchical motifs inspired by collagen to achieve both high mechanical strength and biological degradation.",
    
    "source_path": "high-confidence-protein → collagen → enzymatic-degradation → biodegradable",
    
    "outcome": "Protein composite with 1.5 GPa strength + 90% degradation in 30 days",
    
    "design_principles": [
      "Multi-scale organization: nano → micro → macro",
      "MMP cleavage sites for enzymatic degradation",
      "β-sheet stacking for hierarchical strength"
    ],
    
    "simulation_priorities": [
      "MD: Collagen-inspired β-sheet packing",
      "FEA: Fiber reinforcement mechanics",
      "DE: Protease accessibility"
    ],
    
    "novelty_score": 7.5/10,
    "feasibility_score": 7.0/10
  }

Explanation: "This design emerges from connecting your high-pLDDT proteins with collagen's natural degradation pathways. Here's the knowledge path that led to this: [visual graph]"
```

---

## Project Roadmap

### **Phase 1: Foundation (Current - Week 1-2)**
- ✅ AlphaFold data collection & pipeline validation
- ✅ Enrichment with quality metrics and design principles
- ✅ Embedding generation and semantic search
- 🔄 Documentation and architecture alignment (THIS README)

### **Phase 2: Knowledge Graph Construction (Week 3-4)**
**Deliverables:**
- Build knowledge graph from:
  - Protein domain annotations (UniProt families)
  - Structural properties (pLDDT confidence, hierarchical organization)
  - Design principles (from literature, enricher outputs)
  - Experimental data (from your lab)
  - Mechanisms (binding, catalysis, degradation)
  
- Create edges:
  - "protein_A is_family_of protein_B"
  - "protein_X has_property mechanical_strength"
  - "property_Y enables design_principle_Z"
  - "design_principle enables target_outcome"

**Key Component**: Graph Reasoning Service
- Path sampling algorithm (heuristic + random with embeddings)
- Subgraph extraction
- Graph query interface

### **Phase 3: Multi-Agent Hypothesis Generation (Week 4-5)**
**Deliverables:**
- LLM agent orchestration (Ontologist → Scientist1 → Scientist2 → Critic)
- Structured hypothesis generation (7-aspect JSON output)
- Novelty & feasibility scoring
- Simulation priority identification

**Integration Point**: Chain LLM calls with in-context learning from knowledge graph paths

### **Phase 4: Closed-Loop System (Week 5-6)**
**Deliverables:**
- Project-based hypothesis tracking
- Experimental feedback loop
- Graph update with real results
- Collaborative refinement interface

**What this adds**: "We designed hypothesis X, synthesized it, got results Y. Let's update the knowledge graph with this new data."

---

## What the Project Needs

### **Immediate (Phase 2)**

1. **Knowledge Graph Schema**
   - Define all node types (proteins, properties, principles, methods, organisms)
   - Define all edge relationships (15-20 core types)
   - Decide storage: PostgreSQL? Neo4j? In-memory with Qdrant?

2. **Graph Construction Pipeline**
   - Mining protein domains from UniProt API
   - Extracting design principles from enricher outputs
   - Parsing experimental metadata from projects
   - Building adjacency lists + embeddings

3. **Path-Finding Algorithm**
   - Implement heuristic Dijkstra with randomness factor (from SciAgents paper)
   - Use existing 384-dim embeddings for distance estimation
   - Return subgraph context (path + second-hop neighbors)

### **Phase 2-3 Integration**

4. **LLM Agent Prompts**
   - Domain-specific prompt templates for protein engineering
   - Ontologist: "Define what [protein_domain] means in context of [property]"
   - Scientist1: "Generate design hypothesis connecting [path_nodes]"
   - Scientist2: "Expand with quantitative details: sequences, metrics, simulations"
   - Critic: "Identify weaknesses and most impactful experiments"

5. **Hypothesis Storage Model**
   - SQLAlchemy models for: DesignHypothesis, KnowledgePath, SimulationPriority
   - Link hypotheses to projects for tracking
   - Store LLM model version, temperature, tokens used (for reproducibility)

### **Phase 3 Onwards**

6. **Experimental Feedback Integration**
   - Schema for experimental results
   - Comparison: predicted vs. actual outcomes
   - Graph update logic: "This hypothesis was correct/incorrect → adjust edges"

7. **Multi-User Collaboration**
   - Project ownership and sharing
   - Hypothesis voting/ranking within team
   - Comments and refinement history
   - Version control for designs

8. **Explainability UI**
   - Visualize knowledge paths
   - Interactive hypothesis exploration
   - Simulation results correlation
   - Design rationale documents (markdown export)

---

## Why This Architecture Matters

### **Current State (Search-Based)**
```
Q: "Find proteins like hemoglobin"
A: [5 similar proteins] ← Limited to training data similarity

Problem: Doesn't synthesize new ideas, only retrieves known things
```

### **Target State (Graph-Based Reasoning)**
```
Q: "Design biodegradable, high-strength proteins"
A: [Design hypothesis with:
    - Knowledge path explaining reasoning
    - Design principles from graph
    - Simulation priorities
    - Novelty & feasibility assessment
    - Alternative designs with trade-offs] ← Actively generates new ideas

Benefit: AI becomes a design partner, not just a search engine
```

### **Team Multiplier Effect**
- One researcher → uses graph to find non-obvious inspirations
- Multiple researchers → collaborate on same hypothesis, refine via feedback
- Experimental results → feeds back to graph → improves future predictions
- Knowledge compounds over time

---

## Technical Dependencies

### **Current Stack**
- **Language**: Python 3.10+
- **Vector Database**: Qdrant (http://localhost:6333)
- **Embeddings**: sentence-transformers (384-dim)
- **APIs**: AlphaFold EBI, ArXiv, BioRxiv
- **Backend**: NestJS (TypeScript) for Core API
- **Frontend**: Next.js (React) for UI

### **Phase 2-3 Requirements**
- **Graph Database**: Option 1: PostgreSQL + custom adjacency lists, Option 2: Neo4j
- **LLM Access**: OpenAI GPT-4 or open-source alternatives
- **Agentic Framework**: AutoGen (Python) for multi-agent orchestration
- **NLP**: sentence-transformers for node embeddings

### **Scalability Considerations**
- Qdrant can handle 100K+ vectors efficiently
- Knowledge graph: 10K-50K nodes for initial domain
- Path sampling: O(log n) with good heuristics
- LLM calls: Batch where possible, cache paths

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| **Data Sources** | 4 (AlphaFold, ArXiv, BioRxiv, local) | 8+ (+ UniProt, GitHub, PDB, images, experiments) |
| **Searchable Items** | ~100 | 50K+ |
| **Query Types** | Vector similarity | Vector similarity + graph reasoning |
| **Hypothesis Generation** | None | Automated with explanations |
| **Design Feedback Loop** | Linear (no update) | Closed-loop (results update graph) |
| **User Collaboration** | Individual projects | Team projects with feedback |
| **Explainability** | "Top 5 similar proteins" | "Here's the knowledge path that led to this design" |

---

## Summary

QDesign is transitioning from a **retrieval platform** to a **reasoning platform**:

1. **Now**: "Find relevant proteins and papers"
2. **Next**: "Generate novel protein designs with explainable reasoning"
3. **Future**: "Closed-loop learning from experimental feedback"

The SciAgents paper provides the blueprint for step 2. Our existing data pipeline provides the foundation. The knowledge graph will be the connective tissue that makes AI-driven protein engineering collaborative, explainable, and reproducible.

---

## Contact & Questions

For architecture decisions, integration points, or clarifications on the roadmap:
- Check [existing issues](../../../issues) for discussion threads
- Refer to individual component READMEs (e.g., `pipeline/README.md`)
- Review the SciAgents paper: https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/adma.202413523
