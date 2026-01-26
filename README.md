# PROJECT SPECIFICATION: QDESIGN
**Platform:** QDesign, a Collaborative AI-Driven Biological Design Workbench
**Hackathon Submission:** Use Case 4 (Multimodal Biological Design & Discovery)

---
## Team Members

### Development Team
- Ghassen Naouar
- Moetez Fradi
- Ahmed Saad
- Ghassen Naouar

**Screenshots of our current implementation:**

#### Dashboard Interface
![Dashboard](Screenshots/dashboard.png)
*Main dashboard showing the QDesign workbench interface*

#### Data Pool Visualization  
![Data Pool](Screenshots/data-pool.png)
*Visualization of the protein data collection and management system*

#### Data Visualization Components
![Data Visualization](Screenshots/data-visualisation.png)
*Interactive data visualization tools for exploring biological structures and relationships*

## 1. Executive Summary
**QDesign** is a "Human-in-the-Loop" generative workbench for biological engineering. Unlike standard search engines that simply retrieve data, or chatbots that hallucinate answers, QDesign creates a **structured, visual workspace**. It combines **Multimodal Retrieval** (linking 3D structure to scientific text) with **Agentic Reasoning** to actively propose, critique, and refine new biological designs (such as enzymes or drug targets).

### Core Philosophy
1.  **No Chatbots:** The interface is a Dashboard/Workbench, not a conversation window.
2.  **Vector-Native:** Biological similarity (shape, function, sequence) is the core logic driver.
3.  **Explainable:** Every suggestion provides an evidence trail (papers, similar experiments).

---

## 2. System Architecture (High-Level)

The system is composed of four distinct layers:

### A. The Ingestion & Embedding Layer
Responsible for converting raw biological data into a unified vector space.
*   **Structure Encoder:** Converts 3D coordinates (PDB files) into dense vectors capturing geometric topology and binding sites.
*   **Sequence Encoder:** Converts protein sequences into dense vectors
*   **Semantic Encoder:** Converts scientific literature (Abstracts, Methods) into semantic vectors.
*   **Visual Encoder:** Converts microscopy/experimental images into visual vectors.
*   **Normalization Engine:** Cleans and formats metadata (Temperature, pH, Organism) for database payloads.

### B. The Memory Core (Vector Database)
The central "Brain" of the architecture.
*   **Storage:** Stores multimodal vectors in a unified collection.
*   **Indexing:** Uses HNSW indexing for sub-second retrieval.
*   **Payload Management:** Stores rich metadata for precise filtering (e.g., "Filter by Toxicity < Low").

### C. The Orchestration & Inference Engine
The "Logic" layer that connects user intent to data.
*   **Agent Router:** Deconstructs user queries (e.g., "Find stable variants") into multi-step workflows.
*   **Generative Reasoner:** An LLM-based component that analyzes retrieved candidates and generates new hypotheses (e.g., "Mutate Residue X to Y").
*   **Critique Module:** A self-reflection loop that evaluates generated designs against safety/viability constraints.

### D. The Interactive Workbench (Client)
The visual interface for the scientist.
*   **3D Molecular Viewer:** Renders protein structures interactively.
*   **Latent Space Map:** A 2D visualization of the vector space, showing clusters of related proteins.
*   **Knowledge Graph:** A node-link visualization showing relationships between proteins, papers, and experiments.
*   **Real-time collaboration:** All updates are real-time for all project users.

---

## 3. Detailed Data Flow & Input/Output

### 3.1 Inputs (Multimodal)
The system must accept the following inputs from the user:
1.  **Text Constraints:** Natural language goals (e.g., "Optimize for heat stability").
2.  **Structural Files:** 3D protein files (PDB/CIF format).
3.  **Sequences:** Amino acid strings (FASTA format).
4.  **Images (Optional):** Chemical structure drawings or microscopy data.

### 3.2 Outputs (The Deliverable)
The system must return a "Workspace State" object containing:
1.  **Ranked Candidates:** A list of existing proteins that match the criteria, sorted by vector similarity + payload filtering.
2.  **Generated Designs:** Novel (mutated) protein sequences suggested by the AI.
3.  **Visual Overlays:** Data to highlight specific regions in the 3D viewer (e.g., "Color the active site Red").
4.  **Evidence Graph:** A subgraph of related research papers and experiments that justify the results.
5.  **Explainability Log:** Textual reasoning (e.g., "Candidate A was chosen because its binding pocket is 95% similar to Target B").

---

## 4. Functional Capabilities (The "Must Haves")

### Feature 1: The "Latent Space" Navigator
*   **Requirement:** The user must be able to see the "Universe" of proteins plotted on a 2D map.
*   **Logic:** Apply dimensionality reduction (e.g., UMAP/t-SNE) to the high-dimensional vectors stored in the memory core.
*   **Interaction:** Clicking a point on the map loads the 3D structure in the viewer.

### Feature 2: Hybrid Multimodal Search
*   **Requirement:** Users can search by "Shape" and "Description" simultaneously.
*   **Logic:** The search engine must combine **Dense Vector Score** (Structure similarity) and **Sparse/Dense Vector Score** (Text relevance) with a weighted algorithm.
*   **Example:** "Find proteins shaped like *This File* but mentioned in papers about *Plastic Degradation*."

### Feature 3: The Generative Mutation Loop
*   **Requirement:** The system must not just *find* proteins, but *improve* them.
*   **Logic:**
    1.  Retrieve the Top-K nearest neighbors to the input.
    2.  Align sequences to find differences.
    3.  Use the Inference Engine to identify which differences correlate with the desired property (e.g., Stability).
    4.  Propose a specific mutation (e.g., "W159H").

### Feature 4: Safety & Feasibility Guardrails
*   **Requirement:** The system must flag potentially toxic or impossible designs.
*   **Logic:** A dedicated "Critic" agent checks the generated output against a database of known toxins or physical constraints (using payload filters).

---



## 5. Validation Strategy (The "Golden Run")

To ensure victory, the team will optimize the system for one specific, verifiable scenario:
**Scenario:** **Plastic-Degrading Enzyme Optimization.**
1.  **Input:** A known, weak PETase enzyme (e.g., from *Ideonella sakaiensis*).
2.  **Goal:** "Improve thermal stability."
3.  **Expected System Action:**
    *   System retrieves thermostable hydrolases.
    *   System identifies a structural motif (e.g., a disulfide bridge) present in the stable ones but missing in the input.
    *   System suggests a mutation to introduce that motif.
4.  **Proof:** The system cites the PDB ID of the stable neighbor as evidence.

---

## 6. Why This Architecture Wins
1.  **Feasibility:** By restricting the "Universe" of data to a specific domain (e.g., enzymes), we ensure the AI models perform well without needing supercomputers.
2.  **Compliance:** It strictly adheres to "No Chatbot" by using a Workbench UI.
3.  **Innovation:** It moves beyond RAG (Retrieval) into **Generative Design**, which is the frontier of biotech AI.
4.  **Visuals:** The combination of 3D molecules and 2D Latent Maps provides the "Mind Blowing" factor required for the demo.

---

# Current Working Implementation (As‑Is)

This section describes what works today, what is missing, and how to reproduce the working environment.

## What Works
- **Qdrant** running in Docker and populated with sequence + structure + text embeddings.
- **PostgreSQL** running in Docker and storing sequences + metadata.
- **Sequence embeddings** using **ESM C (esmc_300m)** from the EvolutionaryScale ESM library.
- **Structure embeddings** via CA‑distance histograms (baseline structure signal).
- **Text embedding pipeline** using **Gemini embeddings** (requires API key).
- **Search API** (FastAPI) with:
    - sequence search
    - hybrid search (sequence + Gemini text embeddings + optional structure fusion)
    - simple mutation suggestions (diff‑based)
- **UI** running on Next.js with a dashboard demo panel for hybrid search.
- **NestJS backend** running with **PostgreSQL + TypeORM** (auth + projects endpoints).

## What Does Not Work / Not Yet Wired
- **AlphaFold/EMBL‑EBI API integration** (not wired into backend or UI yet).
- **Full text corpus ingestion** (only a small sample JSONL tested).
- **Structure embeddings are baseline only** (no learned 3D encoder).
- **ESM3 generation** or Forge/SageMaker usage (not integrated).
- **Safety/critic module** (not implemented).
- **Realtime collaboration** (socket events exist but server integration not validated end‑to‑end).

## How to Reproduce the Working Environment

### 1) Services
- Ensure **Docker** is installed.
- Run **Qdrant** and **PostgreSQL** containers with persistent volumes.
    - Qdrant listens on **6333**.
    - Postgres listens on **5432**.

### 2) Python Environment
- Use the existing virtual environment at **.venv**.
- Required Python packages include: `esm`, `torch`, `biopython`, `qdrant-client`, `psycopg[binary]`, `fastapi`, `uvicorn`, `requests`, `tqdm`.

### 3) Data
- Place all PDB files (e.g., `*.pdb.gz`) in **Data/**.
- Optional: create **Data/abstracts.jsonl** with lines in the format:
    - `{ "pdb_id": "5xjh", "text": "abstract text..." }`

### 4) Environment Variables
- Set **GEMINI_API_KEY** in your shell for Gemini embeddings.
- Optional overrides for the API:
    - `QDRANT_URL` (default: `http://localhost:6333`)
    - `PG_DSN` (default: `postgresql://qdesign:qdesign@localhost:5432/qdesign`)
    - `QDRANT_COLLECTION` (default: `petase_sequences_esmc_esmc_300m`)
    - `QDRANT_TEXT_COLLECTION` (default: `petase_text_gemini`)
    - `ESMC_MODEL` (default: `esmc_300m`)
    - `EMBED_DEVICE` (default: `cpu`)

### 5) Pipelines
- **Sequence embedding pipeline:** [backend/Services/ingest/embedding_pipeline.py](backend/Services/ingest/embedding_pipeline.py)
    - Reads PDBs in **Data/**
    - Embeds sequences with **ESM C**
    - Writes vectors to Qdrant and metadata to Postgres
- **Text embedding pipeline:** [backend/Services/ingest/text_embedding_pipeline.py](backend/Services/ingest/text_embedding_pipeline.py)
    - Reads **Data/abstracts.jsonl**
    - Embeds text with **Gemini**
    - Writes vectors to Qdrant text collection

### 6) API Server
- **Search API:** [backend/Services/ingest/search_api.py](backend/Services/ingest/search_api.py)
    - Health endpoint: `/health`
    - Sequence search: `/search`
    - Hybrid search: `/search_hybrid`

### 7) App Backend + UI
- **NestJS Backend:** [backend/Core](backend/Core)
    - Base URL: `http://localhost:3001/api`
    - Auth: `/auth/register`, `/auth/login`, `/auth/session`, `/auth/logout`
    - Projects: `/projects`, `/projects/:id`, `/projects/join`, `/projects/:id/checkpoints`
- **Next.js UI:** [ui](ui)
    - Dev server: `http://localhost:3000`
    - Dashboard includes a hybrid search demo panel

## Known Constraints
- **CPU inference is slow** with ESM C; GPU support is limited by VRAM.
- **Gemini API key must not be committed**; keep it in environment variables only.
- **Hybrid search quality** depends on availability of text embeddings in `petase_text_gemini`.

## What We Should Add Next
1. **AlphaFold/EMBL‑EBI API adapter** (backend service + UI panel).
2. **Learned structure encoder** (replace CA‑distance histograms).
3. **Full text ingestion pipeline** (papers + metadata at scale).
4. **Safety/critic checks** (toxicity/feasibility filters).
5. **Realtime collaboration validation** (socket server + auth‑scoped events).