# Co-Scientist Service

A **SciAgents-inspired multi-agent scientific discovery system** for generating novel biological research hypotheses from knowledge graphs.

## Overview

The Co-Scientist Service implements an automated scientific reasoning pipeline that:

1. **Ingests** a pre-built biological knowledge graph (JSON format)
2. **Extracts** meaningful paths connecting biological concepts
3. **Generates** novel, testable scientific hypotheses using LLM agents
4. **Critiques** and iteratively refines hypotheses through multi-agent collaboration

This system is inspired by the **SciAgents methodology** (Ghafarollahi & Buehler, 2024) which pioneered using knowledge graphs combined with large language models for automated scientific hypothesis generation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Co-Scientist Service                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   JSON KG    │───▶│    Loader    │───▶│    Index     │              │
│  │   (Input)    │    │              │    │   Builder    │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                 │                        │
│                                                 ▼                        │
│                                    ┌──────────────────────┐             │
│                                    │   PathFinder         │             │
│                                    │   (Multiple          │             │
│                                    │    Strategies)       │             │
│                                    └──────────────────────┘             │
│                                                 │                        │
│                                                 ▼                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Orchestration                            │  │
│  │                                                                   │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │  │
│  │   │   Planner   │───▶│  Scientist  │◀──▶│   Critic    │         │  │
│  │   │   Agent     │    │   Agent     │    │   Agent     │         │  │
│  │   └─────────────┘    └─────────────┘    └─────────────┘         │  │
│  │         │                   │                  │                  │  │
│  │         ▼                   ▼                  ▼                  │  │
│  │   ┌─────────────────────────────────────────────────────────┐   │  │
│  │   │              OpenRouter LLM Provider                     │   │  │
│  │   │              (Claude, GPT-4, etc.)                       │   │  │
│  │   └─────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       FastAPI REST API                            │  │
│  │   /v2/run  │  /v2/run/stream  │  /v2/knowledge-graph/*           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
co_scientist_service/
├── src/
│   ├── agents/                 # Multi-agent system
│   │   ├── base_agent.py       # Base class with LLM integration
│   │   ├── planner_agent.py    # Subgraph extraction & path planning
│   │   ├── scientist_agent.py  # Hypothesis generation (7-point framework)
│   │   ├── critic_agent.py     # Scientific quality control
│   │   ├── confidence.py       # Confidence score calculators
│   │   ├── models.py           # Agent data models
│   │   ├── scientist_input.py  # Scientist input preparation
│   │   └── critic_input.py     # Critic input preparation
│   │
│   ├── knowledge_graph/        # Knowledge graph processing
│   │   ├── models.py           # KGNode, KGEdge, KnowledgeGraph
│   │   ├── loader.py           # JSON KG loading & validation
│   │   ├── index_builder.py    # Graph indexing (adjacency, hubs)
│   │   ├── index.py            # Query interface for indexed graph
│   │   ├── pathfinding.py      # Path finding orchestrator
│   │   ├── path_strategies.py  # Shortest, random waypoint, diverse
│   │   ├── path_result.py      # Path result data class
│   │   ├── subgraph.py         # Subgraph extraction
│   │   └── reasoning_subgraph.py # Subgraph with natural language
│   │
│   ├── orchestration/          # Workflow management
│   │   ├── config.py           # WorkflowConfig, state builders
│   │   ├── runner.py           # Non-streaming workflow execution
│   │   ├── streaming.py        # Real-time SSE streaming workflow
│   │   ├── state_manager.py    # In-memory run state tracking
│   │   └── workflow.py         # Re-exports
│   │
│   ├── api/                    # FastAPI endpoints
│   │   ├── routes.py           # Router aggregator
│   │   ├── workflow_routes.py  # /run, /v2/run endpoints
│   │   ├── kg_routes.py        # Knowledge graph exploration
│   │   ├── util_routes.py      # Health, metrics, status
│   │   └── models.py           # Pydantic request/response models
│   │
│   ├── prompts/                # LLM system prompts
│   │   ├── planner.txt         # Planner agent instructions
│   │   ├── scientist.txt       # Scientist agent (7-point framework)
│   │   ├── critic.txt          # Critic agent evaluation criteria
│   │   └── loader.py           # Prompt file loader
│   │
│   ├── providers/              # LLM provider integrations
│   │   ├── base_provider.py    # Abstract LLM provider
│   │   ├── openrouter_provider.py # OpenRouter API client
│   │   └── factory.py          # Provider factory
│   │
│   ├── config/                 # Configuration
│   │   └── settings.py         # Environment-based settings
│   │
│   ├── monitoring/             # Observability
│   │   ├── metrics.py          # Prometheus metrics
│   │   ├── audit_log.py        # Audit logging
│   │   └── traces.py           # Tracing (placeholder)
│   │
│   └── main.py                 # FastAPI application entry
│
├── tests/                      # Test suite
├── data/                       # Data directory (pdb, pdf, text)
├── scripts/                    # Utility scripts
├── .env                        # Environment variables
└── requirements.txt            # Python dependencies
```

---

## Components

### 1. Knowledge Graph Module (`src/knowledge_graph/`)

Handles loading, indexing, and querying the biological knowledge graph.

#### Data Model

```python
@dataclass
class KGNode:
    id: str                    # Unique identifier
    label: str                 # Human-readable name
    type: str                  # "pdb", "sequence", "annotation"
    trust_level: float         # 0.0 - 1.0
    biological_features: list  # Domain-specific features
    metadata: dict             # Additional properties

@dataclass
class KGEdge:
    id: str
    source: str                # Source node ID
    target: str                # Target node ID
    label: str                 # Relationship description
    strength: float            # Confidence score 0.0 - 1.0
    correlation_type: str      # "similarity", "derived", etc.
    explanation: str           # Why this relationship exists
```

#### Path Finding Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `shortest` | BFS shortest path | Direct connections |
| `high_confidence` | Dijkstra with confidence weighting | Conservative analysis |
| `random` | Random walk with waypoints (SciAgents) | Discovery mode |
| `diverse` | Multiple diverse paths | Comprehensive exploration |

---

### 2. Agents Module (`src/agents/`)

Three specialized LLM agents working together:

#### Planner Agent
- **Role**: Extract relevant subgraph from knowledge graph
- **Input**: Knowledge graph + two concepts to connect
- **Output**: Selected path, subgraph, rationale
- **Key Logic**: Evaluates paths based on confidence, length, node diversity

#### Scientist Agent
- **Role**: Generate novel scientific hypotheses
- **Framework**: SciAgents 7-Point Hypothesis Structure
  1. **Hypothesis** - Specific, testable statement
  2. **Expected Outcomes** - Quantifiable predictions
  3. **Mechanisms** - Step-by-step mechanistic explanation
  4. **Design Principles** - Structural/functional principles
  5. **Unexpected Properties** - Emergent behaviors
  6. **Comparison** - Difference from existing knowledge
  7. **Novelty** - What is genuinely new

#### Critic Agent
- **Role**: Scientific quality control
- **Evaluation Criteria**:
  - Logical consistency
  - Evidence grounding
  - Mechanistic plausibility
  - Novelty assessment
  - Feasibility check
- **Decisions**: APPROVE / REVISE / REJECT

---

### 3. Orchestration (`src/orchestration/`)

Manages the multi-agent workflow with iterative refinement.

```python
@dataclass
class WorkflowConfig:
    max_iterations: int = 3           # Max critique-revise cycles
    exploration_mode: str = "balanced" # Path finding strategy
    streaming_enabled: bool = True     # Real-time output
    min_approval_score: float = 7.0    # Approval threshold
```

#### Workflow Phases

```
Phase 1: Planning
    └── Load KG → Index → Find paths → Extract subgraph

Phase 2: Hypothesis Generation
    └── Scientist Agent generates 7-point hypothesis

Phase 3: Critique & Iteration (up to max_iterations)
    ├── Critic evaluates hypothesis
    ├── If APPROVE → Phase 4
    ├── If REVISE → Scientist revises with feedback
    └── If REJECT → Phase 4 (with rejection)

Phase 4: Final Assembly
    └── Package hypothesis + evaluation + subgraph
```

---

### 4. API Endpoints (`src/api/`)

#### Workflow Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/run` | POST | Run workflow (blocking) |
| `/v2/run/stream` | POST | Run workflow with SSE streaming |
| `/run` | POST | Legacy workflow endpoint |

#### Knowledge Graph Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/knowledge-graph/load` | GET | Load and analyze KG |
| `/v2/knowledge-graph/nodes` | GET | Get nodes (optionally filtered) |
| `/v2/knowledge-graph/neighbors/{node_id}` | GET | Get node neighbors |

#### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/status/{run_id}` | GET | Get run status |
| `/hypothesis/{run_id}` | GET | Get hypothesis result |

---

## Configuration

### Environment Variables (`.env`)

```bash
# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=120

# Optional
OPENROUTER_HTTP_REFERER=https://your-app.com
OPENROUTER_APP_TITLE=Co-Scientist
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### 1. Create Virtual Environment

```bash
cd co_scientist_service
uv venv co_scientist_venv
```

### 2. Activate Virtual Environment

```bash
source co_scientist_venv/bin/activate
```

### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### 5. Run the Service

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

## Usage

### Example API Calls

#### Run Workflow (Non-Streaming)

```bash
curl -X POST "http://localhost:8000/v2/run" \
  -H "Content-Type: application/json" \
  -d '{
    "kg_path": "ai_analysis_697390190ad61483087611b8_1769708091179.json",
    "query": "How can we improve hemoglobin efficiency in cold environments?",
    "exploration_mode": "diverse",
    "max_iterations": 3
  }'
```

#### Run Workflow (Streaming)

```bash
curl -X POST "http://localhost:8000/v2/run/stream?kg_path=ai_analysis_*.json&exploration_mode=diverse"
```

#### Explore Knowledge Graph

```bash
# Load and analyze
curl "http://localhost:8000/v2/knowledge-graph/load?kg_path=ai_analysis_*.json"

# Get nodes
curl "http://localhost:8000/v2/knowledge-graph/nodes?kg_path=ai_analysis_*.json&limit=10"

# Get neighbors
curl "http://localhost:8000/v2/knowledge-graph/neighbors/node_123?kg_path=ai_analysis_*.json"
```

---

## Knowledge Graph Input Format

The service expects a JSON knowledge graph with this structure:

```json
{
  "name": "HEMOGLOBIN",
  "mainObjective": "Increase hemoglobin efficiency under low-temperature environments",
  "secondaryObjectives": ["Compare structures across species"],
  "nodes": [
    {
      "id": "unique_node_id",
      "label": "Human-readable name",
      "type": "pdb|sequence|annotation",
      "trustLevel": 0.95,
      "biologicalFeatures": ["feature1", "feature2"],
      "metadata": {
        "pdb_id": "1EZA",
        "organism": "Homo sapiens"
      }
    }
  ],
  "edges": [
    {
      "id": "unique_edge_id",
      "source": "node_id_1",
      "target": "node_id_2",
      "label": "structurally similar",
      "strength": 0.92,
      "correlationType": "similarity",
      "explanation": "RMSD < 2Å across aligned residues"
    }
  ]
}
```

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Knowledge Graph Loading | ✅ Complete | JSON parsing, validation |
| Graph Indexing | ✅ Complete | Adjacency, reverse adjacency, hub detection |
| Path Finding | ✅ Complete | 4 strategies implemented |
| Subgraph Extraction | ✅ Complete | Context expansion, hub inclusion |
| Agent Prompts | ✅ Complete | Well-designed 7-point framework |
| Agent Classes | ✅ Complete | Planner, Scientist, Critic |
| Workflow Orchestration | ✅ Complete | Iterative critique loop |
| Streaming Support | ✅ Complete | SSE event streaming |
| LLM Integration | ⚠️ Needs Testing | OpenRouter provider ready |
| Response Validation | ⚠️ Needs Work | JSON parsing, schema validation |
| End-to-End Tests | ❌ Missing | Need integration tests |

---

## Next Steps

### High Priority

1. **End-to-End Testing**
   - Test full workflow with real KG + LLM
   - Validate JSON response parsing
   - Handle malformed LLM responses

2. **Response Validation**
   - Add JSON schema validation for LLM outputs
   - Implement retry logic for parsing failures
   - Add fallback responses

3. **Fix `_ask()` Return Type**
   - Currently returns full API response
   - Should extract content and parse JSON

### Medium Priority

4. **Multiple Path Exploration**
   - Current implementation finds one path
   - Implement multi-path subgraph for richer hypotheses

5. **Revision Loop Enhancement**
   - Pass detailed critic feedback to scientist
   - Track revision history

6. **Caching**
   - Cache KG loading/indexing
   - Cache LLM responses for identical inputs

### Low Priority

7. **UI Integration**
   - WebSocket support for bidirectional communication
   - Progress indicators for long workflows

8. **Persistent Storage**
   - Save run results to database
   - Enable result retrieval after restart

---

## References

- **SciAgents Paper**: Ghafarollahi, A., & Buehler, M. J. (2024). "SciAgents: Automating scientific discovery through multi-agent intelligent graph reasoning"
- **OpenRouter API**: https://openrouter.ai/docs

---

## License

Internal use only - Selecao-QDesign project.
