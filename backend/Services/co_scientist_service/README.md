<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/OpenRouter-6366F1?style=for-the-badge&logo=openai&logoColor=white" alt="OpenRouter">
</p>

<h1 align="center">🧬 Co-Scientist</h1>

<p align="center">
  <strong>Multi-Agent Scientific Discovery System</strong><br>
  <sub>Automated hypothesis generation from biological knowledge graphs</sub>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-api">API</a>
</p>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🤖 5-Agent Pipeline
Specialized AI agents working in sequence:
- **Planner** → Knowledge graph pathfinding
- **Ontologist** → Semantic interpretation
- **Scientist** → Hypothesis generation
- **Scientist²** → Quantitative expansion
- **Critic** → Scientific evaluation

</td>
<td width="50%">

### 🎨 Modern Interface
- Bio-lab themed Streamlit UI
- Real-time progress visualization
- Formatted hypothesis cards
- Interactive score displays

</td>
</tr>
<tr>
<td width="50%">

### 🔬 Human-in-the-Loop
- Configurable review checkpoints
- Approve / Modify / Reject controls
- Expert intervention at any stage
- Full workflow transparency

</td>
<td width="50%">

### 📊 Production Ready
- Connection retry with auto-recovery
- Type-safe LLM response handling
- JSON export to `workflow_outputs/`
- Comprehensive error handling

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenRouter API key

### Installation

```bash
# Clone and navigate
cd backend/Services/co_scientist_service

# Create virtual environment
uv venv co_scientist_venv
source co_scientist_venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env
```

### Run the UI

```bash
streamlit run streamlit_app.py --server.port 8501
```

Open **http://localhost:8501** and click **🚀 Launch Discovery**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CO-SCIENTIST PIPELINE                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   📊 Knowledge Graph                                         │
│        │                                                     │
│        ▼                                                     │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐               │
│   │ PLANNER │───▶│ONTOLOGIST│───▶│ SCIENTIST│               │
│   │  🗺️     │    │    📖    │    │    🔬    │               │
│   └─────────┘    └──────────┘    └──────────┘               │
│                                        │                     │
│                                        ▼                     │
│                  ┌──────────┐    ┌──────────┐               │
│                  │  CRITIC  │◀───│SCIENTIST²│               │
│                  │    🎯    │    │    ⚗️    │               │
│                  └──────────┘    └──────────┘               │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────┐                            │
│              │ APPROVE/REVISE/ │                            │
│              │     REJECT      │                            │
│              └─────────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | Role | Output |
|-------|------|--------|
| 🗺️ **Planner** | Pathfinding in knowledge graph | Subgraph, path confidence |
| 📖 **Ontologist** | Semantic concept interpretation | Definitions, relationships |
| 🔬 **Scientist** | Hypothesis generation (7-point framework) | Testable hypothesis |
| ⚗️ **Scientist²** | Quantitative expansion | Predictions, protocols |
| 🎯 **Critic** | Scientific quality control | Scores, decision |

---

## 💻 Usage

### Streamlit UI

The interactive interface provides:

- **Sidebar Configuration** — Select knowledge graph, concepts, options
- **Pipeline Visualization** — Watch each agent process in sequence
- **Formatted Results** — Hypothesis cards, score bars, decision badges
- **HITL Checkpoints** — Review and modify outputs before continuing
- **JSON Export** — Download or auto-save results

### API Server

```bash
uvicorn src.main:app --reload --port 8000
```

**Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `POST /v2/run` | Run full workflow |
| `POST /v2/hitl/run` | Run with HITL checkpoints |
| `GET /v2/knowledge-graph/load` | Load & analyze KG |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics |

### Example Request

```bash
curl -X POST "http://localhost:8000/v2/run" \
  -H "Content-Type: application/json" \
  -d '{
    "kg_path": "data/knowledge_graphs/test_hemoglobin_kg.json",
    "query": "How does cold temperature affect hemoglobin?",
    "exploration_mode": "diverse"
  }'
```

---

## 📁 Project Structure

```
co_scientist_service/
├── src/
│   ├── agents/           # Multi-agent system
│   │   ├── planner_agent.py
│   │   ├── ontologist_agent.py
│   │   ├── scientist_agent.py
│   │   ├── scientist2_agent.py
│   │   ├── critic_agent.py
│   │   └── confidence.py
│   ├── knowledge_graph/  # KG processing
│   │   ├── loader.py
│   │   ├── pathfinding.py
│   │   └── subgraph.py
│   ├── orchestration/    # Workflow management
│   ├── providers/        # LLM integration
│   ├── prompts/          # Agent prompts
│   └── api/              # FastAPI routes
├── data/
│   ├── knowledge_graphs/ # Input KG files
│   └── workflow_outputs/ # Generated results
├── streamlit_app.py      # Interactive UI
├── requirements.txt
└── .env
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=120
```

### Knowledge Graph Format

```json
{
  "knowledgeGraph": {
    "nodes": [
      {
        "id": "hemoglobin_alpha",
        "label": "Hemoglobin Alpha",
        "type": "protein"
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "hemoglobin_alpha",
        "target": "oxygen_binding",
        "label": "enables",
        "strength": 0.95
      }
    ]
  }
}
```

---

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Pytest with coverage
python -m pytest tests/ -v

# Test specific agent
python test_agents_output.py scientist
```

**Test Status:** ✅ 12/12 passing

---

## 📚 References

- **SciAgents Paper**: Ghafarollahi & Buehler (2024) — *"SciAgents: Automating scientific discovery through multi-agent intelligent graph reasoning"*
- **OpenRouter**: https://openrouter.ai

---

<p align="center">
  <sub>Built with 🧬 by the Selecao-QDesign team</sub>
</p>
