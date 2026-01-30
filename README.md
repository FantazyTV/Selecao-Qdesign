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
---

## 🔍 Qdrant Integration & XQdrant

### The Challenge with Standard Qdrant

Traditional vector databases like Qdrant excel at finding similar items using metrics like cosine similarity. However, they provide a **black box** result: "These two proteins are 95% similar"—but *why*? For biological research, understanding the *biological reasons* for similarity is crucial.

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
   - Each ESM2 dimension is pre-mapped to biological properties (via probing experiments)
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

### Inputs (Multimodal)
The system must accept the following inputs from the user:
1.  **Text and pdf**
2.  **Structural Files:** 3D protein files (PDB/CIF format).
3.  **Sequences:** Amino acid strings (FASTA format).
4.  **Images :** Chemical structure drawings or microscopy data.

---

## Documentation

For detailed information about each component, refer to the following README files in the [docs](docs/) folder:

- [Interpretability](docs/interpretability_README.md)
- [Data](docs/data_README.md)
- [Backend Core](docs/backend_core_README.md)
- [Backend Services - Retrieval Service](docs/backend_services_retrieval_service_README.md)
- [Backend Services - Coscientist Server](docs/backend_services_coscientist_server_README.md)
- [UI](docs/ui_README.md)
- [XQdrant](docs/XQdrant_README.md)
