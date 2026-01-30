# Multi-Modal Retrieval Service

An advanced AI-powered service for processing multi-modal data pools and generating knowledge graphs for biomedical research objectives.

## 🚀 Features

- **Multi-Modal Data Processing**: Handle PDF, CIF, PDB, FASTA, text, and image files
- **Depth-2 Graph Generation**: Apply high-level tools on inputs AND their results for richer graphs
- **AI-Powered Analysis**: Specialized LLM tools for content analysis and relationship detection  
- **Knowledge Graph Generation**: Create linked graphs showing relationships between data entries
- **PDF Intelligence**: Extract proteins, find similar documents, and related images from PDFs
- **Image Processing**: Find related PDFs based on image content via OCR or metadata
- **Protein Analysis**: Query by ID, sequence, or structure with vector similarity search
- **Objective-Based Intelligence**: Analyze content relevance to specific research goals
- **Scalable Architecture**: Both synchronous and asynchronous processing options

## 🎯 New in v2.0: Multimodal Depth-2 Graphs

### What's New

The service now generates **depth-2 graphs** for PDF and image inputs:

#### PDF Processing Pipeline
```
PDF → Extract Text → [3 parallel operations]
  ├─> Extract proteins mentioned (PDB IDs, UniProt IDs, names)
  ├─> Find similar PDFs (vector similarity)
  └─> Find related images (CLIP similarity)
  └─> Merge all 3 graphs
```

#### Image Processing Pipeline  
```
Image → Parse (OCR) → Find related PDFs
  └─> Return graph with Image→PDF relationships
```

### Benefits
- **Richer Context**: Multi-level relationships reveal hidden connections
- **Cross-Modal Links**: Connect proteins, papers, and images automatically
- **Research Discovery**: Find related work you might have missed
- **Knowledge Integration**: Unify disparate data sources into one graph

## 🏗️ Architecture Overview

### Core Components

1. **Multi-Modal Agent** (`agent/agent.py`)
   - Orchestrates the entire analysis pipeline
   - Handles multi-modal data processing and depth-2 graph generation
   - Implements iterative retrieval strategies
   - **NEW**: PDF and image processing with high-level tools

2. **High-Level Tools** (`agent/high_level_tools/`)
   - `protein_graph_from_query.py` - Query proteins by ID
   - `protein_graph_from_sequence.py` - Search by amino acid sequence
   - `protein_graph_from_cif.py` - Parse CIF/PDB structures
   - `protein_graph_from_pdf.py` - **NEW**: Extract proteins from PDFs
   - `pdf_graph_from_pdf.py` - **NEW**: Find similar PDFs
   - `image_graph_from_pdf.py` - **NEW**: Find related images
   - `pdf_graph_from_image.py` - **NEW**: Find PDFs from images

3. **File Parsers** (`agent/tools/parser/`)
   - PDF text extraction and metadata parsing
   - CIF/PDB protein structure analysis  
   - Image OCR processing
   - Text content analysis and entity extraction

4. **Graph Objects** (`graph/graph_objects.py`)
   - Node and Edge data structures
   - Graph manipulation and serialization
   - Graph merging utilities

5. **API Layer** (`api/retrieval_router.py`)
   - FastAPI endpoints for data pool analysis
   - Async job management
   - Utility endpoints for individual operations

## 📊 Data Flow

```
Data Pool Request → File Parsing → Content Analysis → Relationship Detection → Iterative Retrieval → Graph Synthesis → Response
```

### Detailed Process:

1. **Initial Processing**: Parse all data entries based on their types (PDF, CIF, PDB, text, images)
2. **Content Analysis**: Analyze relevance to research objectives using specialized LLMs
3. **Relationship Detection**: Find connections between data entries using AI analysis
4. **Graph Construction**: Create initial knowledge graph with nodes and edges
5. **Iterative Retrieval**: Expand graph by retrieving similar content based on objectives
6. **Synthesis**: Generate insights and recommendations from the complete graph

## 🔧 Installation & Setup

### Prerequisites

- Python 3.8+
- Optional: OCR dependencies for image processing
- Optional: BioPython for advanced structure parsing

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd retrieval_service

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### Environment Variables

```bash
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
```

## 🚦 Running the Service

### Development Mode

```bash
python app.py
```

### Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Usage

### Main Analysis Endpoint

**POST** `/api/v1/retrieval/analyze`

```json
{
  "dataPool": [
    {
      "_id": "unique-id",
      "type": "pdf|text|cif|pdb|image",
      "name": "filename.ext",
      "description": "optional description",
      "content": "base64 encoded or raw content",
      "addedBy": "user-id",
      "addedAt": "2026-01-26T15:58:44.470+00:00"
    }
  ],
  "mainObjective": "Increasing binding affinity of hemoglobin",
  "secondaryObjectives": [
    "Improving thermal stability",
    "Reducing aggregation"
  ],
  "Notes": [],
  "Constraints": []
}
```

### Response Format

```json
{
  "graphs": [
    {
      "nodes": [
        {
          "id": "node-id",
          "type": "document|protein|structure|sequence|concept",
          "label": "Human readable label",
          "metadata": {},
          "relevance_score": 0.85
        }
      ],
      "edges": [
        {
          "from_id": "source-node",
          "to_id": "target-node", 
          "type": "similarity|references|relates_to",
          "score": 0.75,
          "evidence": "Explanation of relationship"
        }
      ]
    }
  ],
  "summary": "Executive summary of findings",
  "processing_stats": {},
  "recommendations": []
}
```

### Other Endpoints

- `GET /api/v1/retrieval/health` - Health check
- `POST /api/v1/retrieval/analyze-async` - Async analysis
- `GET /api/v1/retrieval/status/{job_id}` - Job status
- `GET /api/v1/retrieval/result/{job_id}` - Job result
- `POST /api/v1/retrieval/parse-file` - Parse single file
- `POST /api/v1/retrieval/extract-entities` - Extract entities
- `POST /api/v1/retrieval/analyze-relationships` - Analyze relationships

## 🧪 Example Usage

See `examples/api_usage_example.py` for complete examples:

```python
from examples.api_usage_example import RetrievalServiceClient

client = RetrievalServiceClient("http://localhost:8000")
result = client.analyze_sync(your_data_pool_request)
print(f"Generated {len(result['graphs'])} knowledge graphs")
```

## 🧠 AI Components

### Specialized LLM Tools

1. **Content Relevance Analyzer**: Evaluates how content aligns with research objectives
2. **Relationship Detector**: Identifies connections between different data entries
3. **Entity Extractor**: Finds proteins, genes, chemicals, and other biological entities
4. **Retrieval Strategist**: Plans what additional data to retrieve
5. **Insight Synthesizer**: Generates final analysis and recommendations

### Graph Intelligence

- **Centrality Analysis**: Identifies most important nodes
- **Clustering Detection**: Finds groups of related content
- **Coverage Assessment**: Evaluates completeness relative to objectives
- **Quality Validation**: Ensures graph structure integrity

## 🛠️ Configuration

### File Parser Settings

Supports multiple file types with intelligent content extraction:

- **PDF**: Text extraction, metadata parsing, scientific keyword detection
- **CIF/PDB**: Protein structure analysis, entity extraction
- **Images**: OCR text extraction (requires pytesseract)
- **Text**: Entity detection, code identification, domain classification

### LLM Model Configuration

Default models can be configured via environment variables:
- Analysis tasks: `anthropic/claude-3-haiku` (fast, cost-effective)
- Synthesis tasks: `anthropic/claude-3-sonnet` (higher quality)

## 🔍 Monitoring & Logging

- Comprehensive logging to `retrieval_service.log`
- Processing statistics tracking
- Job status monitoring for async operations
- Error handling and recovery

## 📈 Performance Considerations

- **Thread Pool**: CPU-intensive operations run in separate threads
- **Async Support**: Non-blocking operations for better concurrency
- **Content Caching**: Parsed content cached to avoid reprocessing
- **Iterative Processing**: Controlled retrieval to manage resource usage

## 🧪 Testing

### Quick Validation (No Server Required)

```bash
# Windows
run_validation.bat

# Unix/Linux/Mac
chmod +x run_validation.sh
./run_validation.sh

# Or directly
python validate_agent.py
```

This validates:
- ✅ Backward compatibility (existing PDB/sequence processing)
- ✅ New PDF functionality (depth-2 graphs)
- ✅ Mixed input types (text + PDF + sequence)

### Full Integration Test (Server Required)

1. **Start the server**:
```bash
python app.py
```

2. **Run the comprehensive test**:
```bash
python test_multimodal_retrieval.py
```

This tests all input types:
- CIF structure file (`pdbs/1EZA.cif`)
- FASTA sequence file (`fastas/Q9ZSM8.fasta`)
- PDF document (simulated research paper)
- Text query ("insulin")

Results are saved to `multimodal_retrieval_result_TIMESTAMP.json`

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/api/v1/retrieval/health

# Get service stats
curl http://localhost:8000/api/v1/retrieval/stats

# Submit processing request (see test_multimodal_retrieval.py for full example)
curl -X POST "http://localhost:8000/api/v1/retrieval/process" \
  -H "Content-Type: application/json" \
  -d @test_request.json

# Check job status
curl http://localhost:8000/api/v1/retrieval/status/{job_id}

# Get results
curl http://localhost:8000/api/v1/retrieval/result/{job_id}
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "content=Sample biomedical text&file_type=text&file_name=test.txt"
```

## 🔮 Future Enhancements

- Real embedding generation (currently using placeholders)
- Enhanced vector similarity search integration
- More sophisticated graph algorithms
- Multi-language support
- Advanced visualization export
- Integration with external biomedical databases

## 🤝 Contributing

This service is designed to be extensible. Key extension points:

- Add new file parsers in `agent/tools/file_parser.py`
- Implement new LLM tools in `agent/tools/llm_analysis.py`
- Extend graph analysis in `utils/processing.py`
- Add new endpoints in `api/retrieval_router.py`

## 📝 License

[Add your license information here]

---

**Built with ❤️ for advancing biomedical research through AI-powered knowledge graph generation.**