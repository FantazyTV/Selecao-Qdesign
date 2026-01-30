# Co-Scientist Service

A **SciAgents-inspired multi-agent scientific discovery system** for generating novel biological research hypotheses from knowledge graphs.

## 🌟 Features

- **5-Agent Pipeline**: Planner → Ontologist → Scientist → Scientist² → Critic
- **Bio-Lab Themed UI**: Modern glassmorphism Streamlit interface
- **Human-in-the-Loop**: Configurable review checkpoints
- **JSON Export**: Workflow results saved to `data/workflow_outputs/`
- **Robust Error Handling**: Connection retries, type safety, graceful fallbacks

## Overview

The Co-Scientist Service implements an automated scientific reasoning pipeline that:

1. **Ingests** a pre-built biological knowledge graph (JSON format)
2. **Extracts** meaningful paths connecting biological concepts
3. **Interprets** concepts semantically through ontological analysis
4. **Generates** novel, testable scientific hypotheses using LLM agents
5. **Expands** hypotheses with quantitative details and experimental protocols
6. **Critiques** and iteratively refines hypotheses through multi-agent collaboration
7. **Supports Human-in-the-Loop** checkpoints for expert guidance

This system is inspired by the **SciAgents methodology** (Ghafarollahi & Buehler, 2024) which pioneered using knowledge graphs combined with large language models for automated scientific hypothesis generation.

---

## Architecture

```
+-------------------------------------------------------------------------+
|                         Co-Scientist Service                             |
+-------------------------------------------------------------------------+
|                                                                          |
|  +------------+    +------------+    +------------+                      |
|  |  JSON KG   |--->|   Loader   |--->|   Index    |                      |
|  |  (Input)   |    |            |    |   Builder  |                      |
|  +------------+    +------------+    +------------+                      |
|                                            |                             |
|                                            v                             |
|                              +------------------------+                  |
|                              |     PathFinder         |                  |
|                              |     (Multiple          |                  |
|                              |      Strategies)       |                  |
|                              +------------------------+                  |
|                                            |                             |
|                                            v                             |
|  +----------------------------------------------------------------------+|
|  |                    Agent Pipeline (5 Agents)                         ||
|  |                                                                      ||
|  |  +---------+   +-----------+   +-----------+   +-----------+        ||
|  |  | Planner |-->| Ontologist|-->| Scientist |-->| Scientist2|        ||
|  |  |  Agent  |   |   Agent   |   |   Agent   |   |  (Expand) |        ||
|  |  +---------+   +-----------+   +-----------+   +-----------+        ||
|  |       |              |              |               |                ||
|  |       |    [HITL Checkpoint]  [HITL Checkpoint]    |                ||
|  |       |              |              |               |                ||
|  |       v              v              v               v                ||
|  |                  +---------------------------+                       ||
|  |                  |       Critic Agent        |                       ||
|  |                  | (Evaluate & Decision)     |                       ||
|  |                  +---------------------------+                       ||
|  |                              |                                       ||
|  |               [APPROVE / REVISE / REJECT]                           ||
|  |                              |                                       ||
|  |                     [HITL Checkpoint]                               ||
|  +----------------------------------------------------------------------+|
|                                                                          |
|  +----------------------------------------------------------------------+|
|  |                  OpenRouter LLM Provider                             ||
|  |                  (Claude, GPT-4, Gemini, etc.)                       ||
|  +----------------------------------------------------------------------+|
|                                                                          |
|  +----------------------------------------------------------------------+|
|  |                       FastAPI REST API                               ||
|  |  /v2/run | /v2/hitl/run | /v2/knowledge-graph/* | /health | /metrics ||
|  +----------------------------------------------------------------------+|
|                                                                          |
+-------------------------------------------------------------------------+
```

---

## Agent Pipeline

The system uses 5 specialized LLM agents working in sequence:

### 1. Planner Agent
- **Role**: Extract relevant subgraph from knowledge graph
- **Input**: Knowledge graph + two concepts to connect
- **Output**: Selected path, subgraph, rationale
- **Key Logic**: Evaluates paths based on confidence, length, node diversity

### 2. Ontologist Agent
- **Role**: Deep semantic interpretation of KG relationships
- **Input**: Planner output with subgraph
- **Output**: 
  - Clear definitions for each concept
  - Detailed relationship explanations
  - Pattern identification
  - Narrative synthesis

### 3. Scientist Agent
- **Role**: Generate novel scientific hypotheses
- **Framework**: SciAgents 7-Point Hypothesis Structure
  1. **Hypothesis** - Specific, testable statement
  2. **Expected Outcomes** - Quantifiable predictions
  3. **Mechanisms** - Step-by-step mechanistic explanation
  4. **Design Principles** - Structural/functional principles
  5. **Unexpected Properties** - Emergent behaviors
  6. **Comparison** - Difference from existing knowledge
  7. **Novelty** - What is genuinely new

### 4. Scientist2 Agent (Expander)
- **Role**: Expand hypothesis with quantitative details
- **Features**:
  - Literature search integration (ArXiv, PubMed)
  - Quantitative predictions with specific values
  - Detailed experimental protocols
  - Computational methodology specifications
  - Risk assessment and timeline estimation

### 5. Critic Agent
- **Role**: Scientific quality control
- **Evaluation Criteria**:
  - Logical consistency (1-10)
  - Evidence grounding (1-10)
  - Mechanistic plausibility (1-10)
  - Novelty assessment (1-10)
  - Feasibility check (1-10)
- **Decisions**: APPROVE / REVISE / REJECT

---

## Human-in-the-Loop (HITL)

The system supports human expert intervention at configurable checkpoints:

### Checkpoint Stages
- After **Planner**: Review/modify extracted subgraph
- After **Ontologist**: Review/modify concept interpretations
- After **Scientist**: Review/modify initial hypothesis
- After **Scientist2**: Review/modify expanded hypothesis
- After **Critic**: Review/override final decision

### HITL Actions
- **Approve**: Continue to next stage
- **Modify**: Edit the output and continue
- **Reject**: Stop the workflow

### HITL API
```bash
# Start workflow with HITL
POST /v2/hitl/run

# List pending checkpoints
GET /v2/hitl/checkpoints

# Resolve a checkpoint
POST /v2/hitl/checkpoints/{checkpoint_id}/resolve
```

---

## Directory Structure

```
co_scientist_service/
├── src/
│   ├── agents/                 # Multi-agent system
│   │   ├── base_agent.py       # Base class with LLM integration & streaming
│   │   ├── planner_agent.py    # Subgraph extraction & path planning
│   │   ├── ontologist_agent.py # Semantic concept interpretation
│   │   ├── scientist_agent.py  # Hypothesis generation (7-point framework)
│   │   ├── scientist2_agent.py # Hypothesis expansion with quantitative details
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
│   │   ├── multi_path.py       # Multi-path exploration
│   │   ├── subgraph.py         # Subgraph extraction
│   │   └── reasoning_subgraph.py # Subgraph with natural language
│   │
│   ├── orchestration/          # Workflow management
│   │   ├── config.py           # WorkflowConfig, state builders
│   │   ├── runner.py           # Non-streaming workflow execution
│   │   ├── streaming.py        # Real-time SSE streaming workflow
│   │   ├── checkpoints.py      # HITL checkpoint management
│   │   ├── state_manager.py    # In-memory run state tracking
│   │   └── workflow.py         # Re-exports
│   │
│   ├── api/                    # FastAPI endpoints
│   │   ├── routes.py           # Router aggregator
│   │   ├── workflow_routes.py  # /run, /v2/run endpoints
│   │   ├── hitl_routes.py      # HITL workflow endpoints
│   │   ├── kg_routes.py        # Knowledge graph exploration
│   │   ├── util_routes.py      # Health, metrics, status
│   │   └── models.py           # Pydantic request/response models
│   │
│   ├── prompts/                # LLM system prompts
│   │   ├── planner.txt         # Planner agent instructions
│   │   ├── ontologist.txt      # Ontologist agent instructions
│   │   ├── scientist.txt       # Scientist agent (7-point framework)
│   │   ├── scientist2.txt      # Scientist2 expansion instructions
│   │   ├── critic.txt          # Critic agent evaluation criteria
│   │   └── loader.py           # Prompt file loader
│   │
│   ├── tools/                  # Agent tools
│   │   ├── arxiv_search.py     # ArXiv literature search
│   │   ├── pubmed_search.py    # PubMed literature search
│   │   └── base_tool.py        # Base tool class
│   │
│   ├── providers/              # LLM provider integrations
│   │   ├── base_provider.py    # Abstract LLM provider
│   │   ├── openrouter_provider.py # OpenRouter API client (with streaming)
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
│   ├── test_agents_new.py      # Agent unit tests
│   ├── test_hitl.py            # HITL workflow tests
│   ├── test_integration.py     # End-to-end tests
│   └── ...
│
├── data/                       # Data directory
│   ├── knowledge_graphs/       # Sample KG files
│   │   └── test_hemoglobin_kg.json
│   ├── pdb/                    # PDB structure files
│   ├── pdf/                    # PDF documents
│   └── text/                   # Text files
│
├── streamlit_app.py            # Interactive testing UI
├── test_agents_output.py       # Agent output testing script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── start.sh                    # Server startup script
```

---

## API Endpoints

### Workflow Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/run` | POST | Run full workflow (blocking) |
| `/v2/run/stream` | POST | Run workflow with SSE streaming |
| `/v2/hitl/run` | POST | Run workflow with HITL checkpoints |
| `/run` | POST | Legacy workflow endpoint |

### HITL Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/hitl/checkpoints` | GET | List pending checkpoints |
| `/v2/hitl/checkpoints/{id}` | GET | Get checkpoint details |
| `/v2/hitl/checkpoints/{id}/resolve` | POST | Resolve checkpoint (approve/modify/reject) |

### Knowledge Graph Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/knowledge-graph/load` | GET | Load and analyze KG |
| `/v2/knowledge-graph/nodes` | GET | Get nodes (optionally filtered) |
| `/v2/knowledge-graph/neighbors/{node_id}` | GET | Get node neighbors |

### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/metrics/summary` | GET | JSON metrics summary |
| `/status/{run_id}` | GET | Get run status |
| `/runs` | GET | List all runs |
| `/hypothesis/{run_id}` | GET | Get hypothesis result |

---

## Configuration

### Environment Variables (`.env`)

```bash
# LLM Provider (Required)
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=120

# Optional
OPENROUTER_HTTP_REFERER=https://your-app.com
OPENROUTER_APP_TITLE=Co-Scientist

# Literature Search (Optional)
ARXIV_MAX_RESULTS=10
PUBMED_API_KEY=your-pubmed-key
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### 1. Create Virtual Environment

```bash
cd backend/Services/co_scientist_service
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

---

## Running the Service

### Option 1: FastAPI Server

```bash
cd backend/Services/co_scientist_service
source co_scientist_venv/bin/activate
uvicorn src.main:app --reload --port 8000 --host 0.0.0.0
```

The API will be available at `http://localhost:8000`.

API Documentation: `http://localhost:8000/docs`

### Option 2: Streamlit Interactive UI

The Streamlit app provides an elegant bio-lab themed interface for testing the agent pipeline:

```bash
cd backend/Services/co_scientist_service
source co_scientist_venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

The UI will be available at `http://localhost:8501`.

#### Streamlit Features:
- **Bio-Lab Aesthetic**: Clean, modern design with emerald/teal color scheme
- **Step-by-step workflow visualization** with animated progress indicators
- **Formatted agent outputs** with hypothesis cards, score bars, and decision badges
- **HITL checkpoint UI** with approve/modify/reject buttons
- **Configurable workflow options** (enable/disable agents, literature search)
- **JSON export** of full workflow results to `data/workflow_outputs/`
- **Raw data viewer** with expandable JSON output

---

## Usage Examples

### Run Workflow via API

```bash
curl -X POST "http://localhost:8000/v2/run" \
  -H "Content-Type: application/json" \
  -d '{
    "kg_path": "data/knowledge_graphs/test_hemoglobin_kg.json",
    "query": "How does cold temperature affect hemoglobin oxygen binding?",
    "exploration_mode": "diverse",
    "max_iterations": 3
  }'
```

### Run HITL Workflow

```bash
# Start workflow with checkpoints
curl -X POST "http://localhost:8000/v2/hitl/run" \
  -H "Content-Type: application/json" \
  -d '{
    "kg_path": "data/knowledge_graphs/test_hemoglobin_kg.json",
    "query": "Investigate hemoglobin adaptations",
    "hitl_stages": ["scientist", "critic"]
  }'

# Check pending checkpoints
curl "http://localhost:8000/v2/hitl/checkpoints"

# Approve a checkpoint
curl -X POST "http://localhost:8000/v2/hitl/checkpoints/{checkpoint_id}/resolve" \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved"}'
```

### Test Individual Agents

```bash
cd backend/Services/co_scientist_service
source co_scientist_venv/bin/activate

# Test specific agent
python test_agents_output.py planner
python test_agents_output.py ontologist
python test_agents_output.py scientist
python test_agents_output.py scientist2
python test_agents_output.py critic

# Run full pipeline
python test_agents_output.py all
```

---

## Knowledge Graph Input Format

The service expects a JSON knowledge graph with this structure:

```json
{
  "knowledgeGraph": {
    "name": "HEMOGLOBIN",
    "mainObjective": "Study hemoglobin efficiency",
    "nodes": [
      {
        "id": "unique_node_id",
        "label": "Human-readable name",
        "type": "protein|structure|condition",
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
        "explanation": "RMSD < 2A across aligned residues"
      }
    ]
  }
}
```

---

## Testing

### Run All Tests

```bash
cd backend/Services/co_scientist_service
source co_scientist_venv/bin/activate

# Run all tests
python run_tests.py

# Quick tests only
python run_tests.py --quick

# Pytest with verbose output
python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_hitl.py -v
```

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Health Check | 2 | Pass |
| API Models | 2 | Pass |
| State Manager | 3 | Pass |
| Multi-Path | 2 | Pass |
| HITL Workflow | 4 | Pass |
| Agents | 5 | Pass |
| Integration | 3 | Pass |

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Knowledge Graph Loading | ✅ Complete | JSON parsing, validation, confidence field support |
| Graph Indexing | ✅ Complete | Adjacency, reverse adjacency, hub detection |
| Path Finding | ✅ Complete | 4 strategies (shortest, random, diverse, weighted) |
| Subgraph Extraction | ✅ Complete | Context expansion, hub inclusion |
| Multi-Path Exploration | ✅ Complete | Rich subgraphs with multiple strategies |
| Planner Agent | ✅ Complete | Path selection with confidence scoring |
| Ontologist Agent | ✅ Complete | Semantic interpretation of concepts |
| Scientist Agent | ✅ Complete | 7-point hypothesis framework |
| Scientist2 Agent | ✅ Complete | Quantitative expansion with literature |
| Critic Agent | ✅ Complete | Multi-criteria evaluation, type-safe |
| Connection Handling | ✅ Complete | Auto-retry with fresh client on errors |
| Type Safety | ✅ Complete | Handles list/dict variations from LLM |
| HITL Checkpoints | ✅ Complete | Configurable pause/resume points |
| Workflow Orchestration | ✅ Complete | Iterative critique loop |
| SSE Streaming | ✅ Complete | Real-time event streaming |
| LLM Integration | ✅ Complete | OpenRouter provider with retry logic |
| Response Validation | ✅ Complete | Pydantic schemas for all agents |
| Streamlit UI | ✅ Complete | Bio-lab themed interface |
| JSON Export | ✅ Complete | Results saved to data/workflow_outputs/ |
| Prometheus Metrics | ✅ Complete | Comprehensive observability |
| End-to-End Tests | ✅ Complete | Full test coverage (12/12 passing) |

---

## References

- **SciAgents Paper**: Ghafarollahi, A., & Buehler, M. J. (2024). "SciAgents: Automating scientific discovery through multi-agent intelligent graph reasoning"
- **OpenRouter API**: https://openrouter.ai/docs

---

## License

Internal use only - Selecao-QDesign project.
