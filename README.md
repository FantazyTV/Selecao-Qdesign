# PROJECT SPECIFICATION: QDESIGN
**Platform:** QDesign, a Collaborative AI-Driven Biological Design Workbench
**Hackathon Submission:** Use Case 4 (Multimodal Biological Design & Discovery)

## The solution in short:

Qdesign is a workspace for scientist where they can **create** "projects" (like rooms), specify the project's objectives, constraints and notes and **upload** their own files (pdfs, cif, safta, images and text), annotate and comment them and visualize them before **creating a tailored knowledge graph** for their project, powered by **Qdarnt**. The knowledge graph consists of nodes of multimodal files (mixed together) and edges that represent the semantic meaning or the relation between the two nodes. Then they can expand the knowledge graph from the search engine, comment data points and mark them as high trust or not.. and finally run a coscientist that takes all the data of the workspace and tries to reach the objective without violating constraints. the response of the scientist is in chunks, and each chunk is commentable (explain this further, don't use this paper...) so the co scientist can built up a new response based on that. we also feature git like history for each secondary objective of the project and cover exporting research into pdf format in the template of IEEE research papers.

## Objectives

QDesign addresses critical challenges in modern biological research:

1. **Data Fragmentation**: Scientists work with data scattered across multiple formats and sources
2. **Hidden Connections**: Valuable relationships between proteins, papers, and experiments remain undiscovered
3. **Explainability Gap**: Traditional vector search doesn't explain *why* proteins are similar in biological terms
4. **Collaboration Friction**: Difficult to share context and insights across research teams
5. **Knowledge Transfer**: Hard to document and reproduce research workflows

**Solution**: A unified platform where scientists can create projects, define objectives and constraints, upload multimodal data, explore semantic relationships through knowledge graphs, expand understanding via intelligent search, and leverage AI to accelerate discovery—all with full biological interpretability.

## Video URL:

https://youtu.be/1vimfGWMWEE

## Live URL (no LLM and retrieval endpoints included because of free tier limitations):

https://qdesign.moetezfradi.me 

you can use these credentials: **123@gmail.com** password: **123456** to login and see the project shown in the video demo.
See the data pool content, the knowledge graph and the elements of it (yes, with visualisation for most nodes !)

You can also create your own account and join a project with this code: **WKYQ35**

---
## Team Members

### Development Team
- Ghassen Naouar
- Moetez Fradi
- Ahmed Saad
- Ghassen Naouar

**Screenshots of our implementation:**

#### Dashboard Interface
![Dashboard](Screenshots/dashboard.png)
*Main dashboard showing the QDesign workbench interface*

![Data Pool](Screenshots/data-pool.png)
*Visualization of the protein data collection and management system*

#### Data Visualization Components
![Data Visualization](Screenshots/data-visualisation.png)
*Interactive data visualization tools for exploring biological structures and relationships*

#### Generated knowledge graph powered by Qdrant
![Knowledge Graph](Screenshots/knowledge_graph.png)
*Multimodel Knowledge Graph, with expalanation edges and nodes for pdfs, images, structures and sequences*


Qdesing is  **Vector-Native:** Biological similarity (shape, function, sequence) is the core logic driver, and **Explainable:** Every retrieval and suggestion provides an evidence trail (papers, similar experiments).

## Technologies

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.1.4 | React framework with SSR |
| React | 19.2.3 | UI library |
| TypeScript | Latest | Type safety |
| Tailwind CSS | 4.x | Styling |
| Socket.io Client | 4.8.3 | Real-time communication |
| @xyflow/react | 12.10.0 | Knowledge graph visualization |
| NGL | 2.4.0 | 3D molecular structure viewer |
| React PDF | 10.3.0 | PDF rendering |
| Zustand | 5.0.10 | State management |
| TanStack Query | 5.90.20 | Server state management |
| Framer Motion | 12.29.0 | Animations |

### Backend - Core (NestJS)
| Technology | Version | Purpose |
|------------|---------|---------|
| NestJS | 11.0.1 | Backend framework |
| Node.js | 18+ | Runtime |
| MongoDB | 9.1.5 (Mongoose) | Database for users, projects, files |
| Socket.io | 4.8.3 | WebSocket server |
| JWT | 11.0.2 (@nestjs/jwt) | Authentication |
| Passport | 0.7.0 | Auth middleware |
| Axios | 1.13.4 | HTTP client |

### Backend - Microservices (Python)
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.0+ | REST API framework |
| Python | 3.10+ | Runtime |
| Uvicorn | 0.27.0+ | ASGI server |
| Pydantic | 2.0.0+ | Data validation |
| LangChain | Latest | LLM orchestration |
| LangGraph | Latest | Agent workflows |

### Vector Database & Embeddings
| Technology | Version | Purpose |
|------------|---------|---------|
| **XQdrant** | Custom Fork | Explainable vector search (see below) |
| Qdrant Client | 2.7.0+ | Vector DB client |
| Sentence Transformers | 3.3.1 | Text embeddings (all-MiniLM-L6-v2, 384-dim) |
| ESM-2 | 2.0.0+ (fair-esm) | Protein sequence embeddings (1280-dim) |
| CLIP | 1.0.0+ (openai-clip) | Image embeddings (512-dim) |
| PyTorch | 2.0.0+ | Deep learning backend |

### Data Pipeline
| Technology | Version | Purpose |
|------------|---------|---------|
| Biopython | Latest | Biological data parsing |
| NumPy | 2.4.1 | Numerical computing |
| Pandas | Latest | Data manipulation |
| Requests | 2.32.5 | HTTP requests |
| TQDM | 4.67.1 | Progress bars |

### Infrastructure
- **Database**: MongoDB (user data, projects), PostgreSQL (metadata)
- **Vector Store**: XQdrant (custom Rust-based fork of Qdrant)
- **Message Queue**: Built-in async task handling
- **Package Managers**: pnpm (frontend), pip (backend)


## System Architecture (High-Level)

**XQdrant** is our own modified version of qdrant that allows us to interpret biological similarities (more on that in the docs below) and is the brain of the whole project, it contains 4 collections : structures and sequences embedded using ESM2, pdfs using all-MiniLM-L6-v2 and images using CLIP for text + image based similarity search.

**MongoDB** is where we store the actual files, users and proejcts data.

**Core** is the main server that the ui communicates with, it is the only component communicating with the mongodb database and calls other micro services.

we have 2 main **Services** one for the knowledge graph generation / expansion and one for the co scientist.

The **UI** updates in real-time to ensure easy collaboratoin between users.

see a detailed architecture image:
https://drive.google.com/file/d/1Q-FJCkogA3mnIx0_51hClG9zEKPq8VBq/view?usp=sharing

## Qdrant Integration & XQdrant

### The Challenge with Standard Qdrant

Traditional vector databases like Qdrant excel at finding similar items using metrics like cosine similarity. However, they provide a **black box** result: "These two proteins are 95% similar"—but *why*? For biological research, understanding the *biological reasons* for similarity is **GOLD**.

### Our Solution: XQdrant

**XQdrant** is our custom fork of Qdrant with an added **explainability layer** written in Rust. It answers the "why" question by identifying which embedding dimensions contribute most to similarity.

#### How It Works

1. **Standard Search**: User queries for proteins similar to a target structure
2. **Qdrant Core**: Computes cosine similarity across 1280-dimensional ESM2 embeddings
3. **Explainability Module** (`explainability.rs`): 
   - Analyzes the two vectors being compared
   - Identifies the top 10 dimensions with highest contribution to similarity
   - Returns dimension IDs and contribution scores

4. **Biological Interpretation**: 
   - Each ESM2 dimension is pre-mapped to biological properties (via probing experiments, see more about it in [Interpretability Docs](docs/interpretability_README.md))
   - Mapping stored in `esm2_dim_to_biological_property.json`
   - Properties include: secondary structure (alpha helix, beta sheet), surface exposure, flexibility, charge distribution, hydrophobicity, etc.

5. **Result**: User sees "These proteins are similar because they both have high alpha-helix content (dim 1160: 87.8% contribution) and similar surface exposure (dim 234: 5.9% contribution)"

#### API Example

**Request with Explanation:**
```bash
curl -X POST "http://localhost:6333/collections/structures/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.23, -0.15, ..., 0.44],
    "limit": 10,
    "with_explanation": true
  }'
```

**Response:**
```json
{
  "result": [{
    "id": 42,
    "score": 0.9999999,
    "score_explanation": {
      "top_dimensions": [
        {"dimension": 1160, "contribution": 0.87828344},
        {"dimension": 234, "contribution": 0.059287537},
        {"dimension": 736, "contribution": 0.0019410067},
        ...
      ]
    }
  }]
}
```

**Interpreted Result:**
- **Dimension 1160** (87.8% contribution) → Alpha-helix propensity
- **Dimension 234** (5.9% contribution) → Surface accessibility
- **Dimension 736** (0.19% contribution) → Charge distribution

### Vector Collections

XQdrant maintains four specialized collections:

| Collection | Embedding Model | Dimensions | Use Case |
|------------|-----------------|------------|----------|
| `qdesign_structures` | ESM-2 (structure-aware) | 1280 | PDB/CIF files, 3D protein similarity |
| `qdesign_sequences` | ESM-2 (sequence) | 1280 | FASTA sequences, homology search |
| `qdesign_text` | all-MiniLM-L6-v2 | 384 | PDFs, papers, text documents |
| `qdesign_images` | CLIP ViT-B-32 | 512 | Diagrams, microscopy, chemical structures |

### Interpretability Research

Our dimension-to-property mapping is based on **probing experiments** (inspired by [this BioRxiv paper](https://www.biorxiv.org/content/10.1101/2024.11.14.623630v1.full.pdf)):

1. Extract protein sequences from CIF files
2. Generate ESM2 embeddings
3. Compute biological properties: secondary structure, solvent accessibility, B-factor (flexibility)
4. Train linear probes to predict properties from embeddings
5. Analyze probe weights to identify important dimensions for each property
6. Map dimensions → biological meanings

All experiments are documented in [Interpretability/esm_cif_interpretability.ipynb](Interpretability/esm_cif_interpretability.ipynb).

### Reproducing XQdrant

```bash
# Clone the XQdrant repository
cd XQdrant

# Build from source (requires Rust toolchain)
cargo build --release

# Run the server
./target/release/qdrant-server

# Server will start on http://localhost:6333
```

Test explainability:
```bash
curl -X POST "http://localhost:6333/collections/structures/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [...],  # Your embedding vector
    "limit": 10,
    "with_explanation": true
  }'
```

---


---

## Inputs (Multimodal)
The system must accept the following inputs from the user:
1.  **Text and pdf**
2.  **Structural Files:** 3D protein files (PDB/CIF format).
3.  **Sequences:** Amino acid strings (FASTA format).
4.  **Images :** Chemical structure drawings or microscopy data.

---

## Setup & Installation

### Prerequisites

- **Node.js** 18+ and **pnpm**
- **Python** 3.10+
- **MongoDB** (local or MongoDB Atlas)
- **PostgreSQL** (optional, for metadata)
- **Rust** (for building XQdrant)
- **Docker** (optional, for containerized deployment)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/qdesign.git
cd qdesign
```

### Step 2: Backend Core Setup (NestJS)

```bash
cd backend/Core

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Edit .env with your settings:
# - MongoDB connection string
# - JWT secret
# - Service URLs (knowledge_service, retrieval_service, co_scientist_service)

# Run in development mode
npm run start:dev

# Server will start on http://localhost:3000
```

### Step 3: Frontend Setup (Next.js)

```bash
cd ../../ui

# Install dependencies
pnpm install

# Configure environment
cp .env.example .env.local

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:3000
# NEXT_PUBLIC_SOCKET_URL=http://localhost:3001

# Run development server
pnpm dev

# Run Socket.io server (in another terminal)
pnpm dev:socket

# Or run both together
pnpm dev:all

# Frontend: http://localhost:3000
# Socket server: http://localhost:3001
```

### Step 4: XQdrant Setup

```bash
cd ../XQdrant

# Build from source
cargo build --release

# Run the server
./target/release/qdrant-server

# XQdrant will start on http://localhost:6333
```

Alternatively, use Docker:
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage xqdrant/xqdrant:latest
```

### Step 5: Data Pipeline Setup

```bash
cd ../Data/pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Edit .env:
# - QDRANT_URL=http://localhost:6333
# - POSTGRES_DSN (if using PostgreSQL)

# Run test ingestion
python scripts/test_ingestion.py
```

### Step 6: Microservices Setup

#### Knowledge Service
```bash
cd ../../backend/Services/knowledge_service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run service
uvicorn main:app --reload --port 8001

# Service will start on http://localhost:8001
```

#### Retrieval Service
```bash
cd ../retrieval_service

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

uvicorn main:app --reload --port 8002
# Service: http://localhost:8002
```

#### Co-Scientist Service
```bash
cd ../co_scientist_service

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Configure LLM API keys (OpenAI, Anthropic, etc.)
uvicorn main:app --reload --port 8003
# Service: http://localhost:8003
```

### Step 7: Verify Installation

1. **Backend Core**: Visit http://localhost:3000/health
2. **Frontend**: Visit http://localhost:3000 (Next.js)
3. **XQdrant**: `curl http://localhost:6333/collections`
4. **Knowledge Service**: `curl http://localhost:8001/health`
5. **Retrieval Service**: `curl http://localhost:8002/health`
6. **Co-Scientist Service**: `curl http://localhost:8003/health`

### Environment Variables Summary

**Backend Core (.env)**:
```env
MONGODB_URI=mongodb://localhost:27017/qdesign
JWT_SECRET=your-secret-key
KNOWLEDGE_SERVICE_URL=http://localhost:8001
RETRIEVAL_SERVICE_URL=http://localhost:8002
COSCIENTIST_SERVICE_URL=http://localhost:8003
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_SOCKET_URL=http://localhost:3001
```

**Data Pipeline (.env)**:
```env
QDRANT_URL=http://localhost:6333
POSTGRES_DSN=postgresql://user:pass@localhost:5432/qdesign
```

**Microservices (.env)**:
```env
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your-key  # For Co-Scientist
```
## Usage Examples

### Example 1: Creating a Project and Uploading Data

```bash
# 1. Register and login via the UI
# Navigate to http://localhost:3000

# 2. Create a new project
# Click "New Project" → Name: "Protein Stability Analysis"
# Objective: "Identify thermostable protein variants"
# Constraints: "Temperature range 60-80°C, pH 6-8"

# 3. Upload data files
# Drag and drop:
#   - research_papers/thermostability_review.pdf
#   - structures/1ABC.pdb
#   - sequences/candidate_proteins.fasta
#   - images/stability_curve.png

# 4. Annotate files
# Click on 1ABC.pdb → View 3D structure in NGL viewer
# Add note: "Thermophilic enzyme from T. thermophilus"
# Set trust level: "High"
```

### Example 2: Generating a Knowledge Graph

```python
# Via API (or use the UI's "Generate Graph" button)
import requests

# Trigger graph generation
response = requests.post(
    "http://localhost:8001/knowledge-graph/generate",
    json={
        "project_id": "proj_12345",
        "similarity_threshold": 0.75,
        "max_connections": 50
    }
)

graph = response.json()
print(f"Generated {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

# Example edge with explanation:
edge = graph['edges'][0]
print(f"Connection: {edge['source']} → {edge['target']}")
print(f"Similarity: {edge['weight']}")
print(f"Reason: {edge['biological_explanation']}")
# Output: "Similar alpha-helix propensity (dim 1160: 85%), surface accessibility (dim 234: 6%)"
```

### Example 3: Querying XQdrant with Explanation

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Search for similar protein structures
results = client.search(
    collection_name="qdesign_structures",
    query_vector=[0.23, -0.15, ..., 0.44],  # ESM2 embedding of query protein
    limit=10,
    with_explanation=True  # Enable explainability
)

for result in results:
    print(f"Protein ID: {result.id}, Score: {result.score}")
    
    # Decode biological meaning
    for dim_contrib in result.score_explanation.top_dimensions:
        dim_id = dim_contrib['dimension']
        contribution = dim_contrib['contribution']
        
        # Map to biological property (using precomputed mapping)
        bio_property = dimension_to_property[dim_id]
        print(f"  - {bio_property}: {contribution*100:.1f}% contribution")
```

### Example 4: Using the AI Co-Scientist

```python
# Via API or UI
import requests

# Send query to Co-Scientist
response = requests.post(
    "http://localhost:8003/coscientist/query",
    json={
        "project_id": "proj_12345",
        "query": "What mutations could improve thermostability based on similar proteins in my knowledge graph?",
        "context": {
            "include_graph": True,
            "include_files": True,
            "constraints": ["Temperature: 60-80°C", "pH: 6-8"]
        }
    }
)

# Response is chunked for iterative refinement
for chunk in response.json()['chunks']:
    print(f"\n--- {chunk['type']} ---")
    print(chunk['content'])
    print(f"Evidence: {chunk['citations']}")
    
    # User can comment on each chunk:
    # "Explain the mechanism behind mutation L123A"
    # "Don't consider paper XYZ, it uses different conditions"
```
---

### Example 5: Expanding the Knowledge Graph

```bash
# Use the UI's "Expand Graph" feature
# 1. Select a node (e.g., a protein structure)
# 2. Click "Find Related"
# 3. Choose expansion sources:
#    - arXiv papers mentioning the protein
#    - PDB structures with >70% similarity
#    - Related sequences from UniProt

# The graph updates in real-time with new nodes/edges
```

### Example 6: Exporting Research to IEEE PDF

```javascript
// Via UI: Project → Export → IEEE Template
// Or programmatically:

const response = await fetch('/api/projects/proj_12345/export', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    format: 'ieee_pdf',
    include: ['abstract', 'methods', 'results', 'knowledge_graph', 'references']
  })
});

const blob = await response.blob();
// Download PDF with formatted research paper
```

## Documentation

For detailed information about each component, refer to the following README files in the [docs](docs/) folder:

- [Interpretability](docs/interpretability_README.md)
- [Data](docs/data_README.md)
- [Backend Core](docs/backend_core_README.md)
- [Backend Services - Retrieval Service](docs/backend_services_retrieval_service_README.md)
- [Backend Services - Coscientist Server](docs/backend_services_coscientist_server_README.md)
- [UI](docs/ui_README.md)
- [XQdrant](docs/XQdrant_README.md)
