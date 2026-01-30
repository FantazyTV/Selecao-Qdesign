# Backend/Services/Retrieval Service

This service builds knowledge graphs from multimodal data. It processes PDFs, images, protein sequences, and structures to create connected graphs.

## Retrieval Methods

### PDF Processing
- Extracts protein mentions using LLM analysis (PDB IDs, UniProt IDs, names)
- Finds similar PDFs via vector similarity search
- Locates related images using CLIP embeddings

### Image Processing
- Parses text via OCR
- Searches for related PDFs using extracted text or metadata
- Creates Image→PDF relationship graphs

### Protein Retrieval
- Queries by PDB ID: Direct vector lookup in Qdrant
- Queries by sequence: FASTA similarity search
- Queries by structure: CIF file parsing and embedding
- Resolves names: Web search for protein identifiers

### Graph Construction
- Builds nodes for documents, proteins, structures, sequences
- Creates edges for mentions, similarities, references
- Merges multiple graphs with deduplication
- Handles multimodal relationships

## Technical Implementation

### High-Level Tools
- `protein_graph_from_pdf.py`: LLM extraction + Qdrant retrieval
- `pdf_graph_from_pdf.py`: Vector similarity for document matching
- `image_graph_from_pdf.py`: CLIP-based image-PDF linking
- `pdf_graph_from_image.py`: Reverse image-to-PDF search

### API Endpoints
- `POST /api/v1/retrieval/process`: Main analysis with graph generation, returns a job id
- `GET /api/v1/retrieval/status/{job_id}`: Async job monitoring
- `GET /api/v1/retrieval/result/{job_id}`: returns the result if done

### LLM Integration
- Uses OpenRouter API for entity extraction and summarization
- Generates executive summaries and helpful notes
- Refines queries for better retrieval accuracy

each part of the service creates graphs, that are then merged together, normalized and sent back.

## Output:

Thanks to our interpretabiloty and XQdrant modules, we are able to make each eadge of the graph have an actual biological meaning, using the backend\Services\retrieval_service\esm2_dim_to_biological_property.json (this feature only works with protein to protein for convenience, since a pdf cannot be related to an image by a biological meaning, yet it can be implemented by doing another interpertabilty research on the text and image embedding models.)