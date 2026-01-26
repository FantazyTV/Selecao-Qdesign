# Pipeline Module

Comprehensive data processing pipeline for ingesting, normalizing, enriching, and embedding scientific data across multiple modalities (text, sequences, structures, images).

**Status**: Production-ready with comprehensive monitoring and testing

**Version**: 1.0.0

**Last Updated**: January 2026

## Overview

The pipeline is a modular system designed to process scientific data from multiple sources into semantic vectors stored in a vector database (Qdrant). It supports four primary data modalities:

- **Text**: Research papers, abstracts, documentation
- **Protein Sequences**: FASTA format biological sequences
- **Protein Structures**: PDB format 3D structural data
- **Images**: Scientific diagrams, microscopy images, and visualizations

## Directory Structure

```
pipeline/
├── collectors/          # Fetch data from external sources (arXiv, bioRxiv, local)
├── ingestion/           # Parse and extract content from files
├── normalization/       # Standardize and clean content
├── enrichment/          # Extract metadata and features
├── embedding/           # Convert content to semantic vectors
├── storage/             # Qdrant vector database integration
├── orchestration/       # Main pipeline orchestrator
├── monitoring/          # Real-time health and quality tracking
├── scripts/             # Utility scripts for data download and processing
├── tests/               # Comprehensive test suite for all data types
├── config.py            # Configuration settings
├── logger.py            # Logging setup
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Pipeline Components

### Collectors - Data Sources

The collectors component fetches data from external sources and converts it into a standardized format. The pipeline supports the following data sources:

#### ArXiv Collector
Fetches research papers directly from the arXiv preprint server. This is ideal for accessing academic papers on topics like protein engineering, machine learning, and computational biology. The collector can search by keywords, filter by subject category, and automatically downloads paper metadata including authors, abstracts, publication dates, and links to PDF versions.

#### BioRxiv Collector
Collects preprints from bioRxiv (Cold Spring Harbor Laboratory), which specializes in life science research. Useful for obtaining the latest biology, bioinformatics, and biochemistry papers that may not yet be peer-reviewed. The collector retrieves paper metadata and provides links to full-text PDFs.

#### Local File Collector
Processes files from the local filesystem. This allows you to:
- Process data already downloaded to your computer
- Work with proprietary or restricted datasets not available through public APIs
- Combine multiple data sources in a single pipeline run

**Supported local file types**:
- Text: PDF files, plain text documents
- Sequences: FASTA format files (.fasta, .fa, .faa, .fna)
- Structures: PDB format files (.pdb)
- Images: JPG, PNG, BMP, GIF, WebP images

### Ingestion - Content Extraction

The ingestion component parses various file formats and extracts the actual content and metadata. Different ingesters handle different file types:

#### Text Ingester
Reads plain text (.txt) files with automatic encoding detection, preserving formatting and structure.

#### PDF Ingester
Extracts text from PDF documents. Handles multi-page PDFs, preserves document structure, and extracts metadata like title and author information. Gracefully handles corrupted PDFs by skipping problematic sections.

#### Sequence Ingester
Parses FASTA format files containing biological sequences. Extracts individual sequences, their identifiers, and descriptions. Validates sequence characters and handles both DNA and protein sequences.

#### Structure Ingester
Parses PDB (Protein Data Bank) format files. Extracts 3D coordinates, identifies protein chains and residues, detects ligands and other heteroatoms, and validates structural integrity.

#### Image Ingester
Loads image files using PIL/Pillow. Extracts image dimensions, format information, color mode, and handles various image types gracefully.

### Normalization - Data Standardization

The normalization component cleans and standardizes content to ensure consistency across different data types and sources.

#### Text Normalization
Removes control characters and non-printable characters, normalizes whitespace by collapsing multiple spaces and removing extra line breaks, strips leading and trailing whitespace, and ensures UTF-8 encoding consistency.

#### Sequence Normalization
Converts sequences to uppercase for consistency, removes whitespace and gap characters, validates that only standard amino acids or nucleotides are present, and standardizes IUPAC codes.

#### Structure Normalization
Validates protein coordinate data for integrity, checks for valid amino acid residues, removes duplicate atoms, and standardizes atom naming conventions.

### Enrichment - Feature Extraction

The enrichment component extracts meaningful features and metadata from content, enabling better understanding and analysis.

#### Text Enrichment
Extracts statistics like word count, sentence count, paragraph count, vocabulary size, and reading level. Performs named entity recognition to identify people, organizations, and locations. Identifies key technical terms and scientific concepts specific to the domain.

#### Sequence Enrichment
Analyzes amino acid composition and frequency. Calculates molecular weight, isoelectric point, and net charge. Measures hydrophobicity and other biochemical properties relevant to protein function and behavior.

#### Structure Enrichment
Analyzes the number of protein chains and atoms in the structure. Extracts information about experimental methods (X-ray crystallography, cryo-EM, NMR) and resolution. Calculates structural statistics like surface area and radius of gyration.

### Embedding - Vectorization

The embedding component converts content into fixed-dimensional semantic vectors suitable for similarity search and machine learning applications. Each data type has its own embedding model optimized for its content characteristics.

#### Text Embeddings (384 dimensions)
Uses SentenceTransformer models trained on diverse text datasets. Captures semantic meaning, relationships between concepts, and document similarity. Enables finding papers on similar topics and clustering by research theme.

#### Sequence Embeddings (384 dimensions)
Creates embeddings trained to understand protein sequence similarity and evolutionary relationships. Captures functional similarity between proteins and amino acid patterns. Enables finding homologous proteins and identifying sequence families.

#### Image Embeddings (3072 dimensions)
Extracts visual features including texture, color distribution, and structural elements. Captures composition and layout of scientific diagrams. Enables finding similar scientific figures and visual documents. Falls back to PIL-based feature extraction if needed.

#### Structure Embeddings (256 dimensions)
Lightweight embeddings based on structural properties rather than heavy deep learning models. Captures secondary structure composition, surface properties, and fold characteristics. Requires minimal computational resources and no GPU.

### Storage - Vector Database

The storage component persists vectors and metadata in Qdrant, a specialized vector database designed for semantic search.

#### Qdrant Collections
The pipeline automatically creates and manages four collections in Qdrant, one for each data modality:

- **qdesign_text**: Stores text embeddings (384-dimensional vectors) with document metadata
- **qdesign_sequences**: Stores sequence embeddings (384-dimensional vectors) with protein information
- **qdesign_images**: Stores image embeddings (3072-dimensional vectors) with visual metadata
- **qdesign_structures**: Stores structure embeddings (256-dimensional vectors) with protein structure information

Each collection uses HNSW indexing for fast approximate nearest neighbor search, enabling rapid similarity queries across millions of vectors.

### Orchestration - Pipeline Coordination

The orchestration component coordinates all pipeline stages, managing data flow from collection through storage. It handles component registration, execution sequencing, error handling, and data transformation between stages.

### Monitoring - Health & Quality Tracking

Real-time monitoring system tracks three critical aspects of pipeline operation:

#### Health Monitoring
Tracks ingestion success rates per source, identifies failed sources and their error patterns, measures data freshness (how recent the data is), and alerts when success rates drop below acceptable thresholds (95% warning, 90% critical).

#### Quality Monitoring
Detects and counts errors in data processing, identifies duplicate records using content hashing, validates that required metadata fields are present and complete, checks embedding validity (no NaN or Inf values), and ensures embeddings have correct dimensions.

#### Balance Monitoring
Tracks the distribution of data across modalities (targeting 25% each), calculates a Gini coefficient to measure distribution inequality, ensures no single source dominates a modality, and detects imbalanced representations.

---

## Data Sources & Capabilities

### Supported Data Modalities

The pipeline can process four distinct types of scientific data, each with its own pipeline tailored to the specific format and characteristics.

#### Text Documents
- **Sources**: arXiv research papers, bioRxiv preprints, local PDF/text files
- **Formats**: PDF, plain text (.txt)
- **Processing**: Extract text → normalize → enrich with statistics and entities → embed semantically → store with metadata
- **Use Cases**: Literature review, paper retrieval by topic, semantic search across research

#### Protein Sequences
- **Sources**: UniProt protein databases, local FASTA files, sequence from PDB structures
- **Formats**: FASTA (.fasta, .fa, .faa, .fna)
- **Processing**: Parse sequences → normalize and validate → analyze composition and properties → embed with evolutionary context → store with sequence data
- **Use Cases**: Homology search, protein family identification, sequence-based retrieval

#### Protein Structures
- **Sources**: RCSB Protein Data Bank (PDB), local PDB files
- **Formats**: PDB structure format (.pdb)
- **Processing**: Parse coordinates and chains → validate structure → analyze structural properties → embed structural features → store with 3D information
- **Use Cases**: Structure-based similarity search, fold family classification, ligand interaction discovery

#### Images
- **Sources**: Scientific illustrations, microscopy images, diagrams, local image files
- **Formats**: JPG, PNG, BMP, GIF, WebP
- **Processing**: Load image → extract visual features → normalize dimensions → embed visual content → store with image metadata
- **Use Cases**: Figure retrieval, visual similarity search, diagram classification

### External Data Source Details

**arXiv**
- Contains millions of preprints across physics, mathematics, computer science, biology
- Covers topics: protein design, machine learning, computational methods
- API-based access with 3 requests per second rate limit
- Full PDF access for most papers
- Regular updates with new submissions daily

**bioRxiv**
- Specializes in life sciences preprints
- Covers: molecular biology, bioinformatics, biochemistry, structural biology
- Web-based access with automatic PDF linking
- Growing repository with daily new submissions

**RCSB Protein Data Bank**
- Official repository for 3D structures from X-ray, cryo-EM, NMR experiments
- Over 200,000 protein structures
- Complete experimental metadata
- Various download formats (PDB, mmCIF, etc.)

**Local Files**
- Unlimited storage of your own or proprietary data
- Flexible organization and file naming
- No rate limits or external dependencies
- Suitable for private or restricted datasets

---

## How to Use the Pipeline

### Step 1: Understanding Data Organization

The pipeline uses a specific directory structure for organizing downloaded and processed data:

**Data Directory Structure** (`/Data/` folder in project root):
```
Data/
├── text/              # Contains PDF and text documents
├── sequences/         # Contains FASTA sequence files
├── structures/        # Contains PDB structure files
└── images/            # Contains image files
```

When you download data, it gets organized into these folders automatically. You can also manually place files in these directories and the pipeline will process them.

### Step 2: Download Data

The pipeline provides a download script to acquire data from multiple sources. The script is located at `pipeline/scripts/download_data.py`.

#### Parameters for download_data.py

**Basic usage parameters**:
- `--all`: Download from all available sources (recommended for full setup)
- `--arxiv N`: Download N papers from arXiv (example: `--arxiv 100`)
- `--biorxiv N`: Download N papers from bioRxiv (example: `--biorxiv 50`)
- `--pdb N`: Download N protein structures from PDB (example: `--pdb 200`)
- `--images N`: Download N scientific images (example: `--images 100`)
- `--output-dir PATH`: Specify where to save downloaded data (default: `./Data/`)
- `--resume`: Resume incomplete downloads instead of starting over

#### How to Download Data

Run from the `backend/Services` directory:

**Download everything** (useful for initial setup):
```
python pipeline/scripts/download_data.py --all
```
This downloads a default amount of data from each source.

**Download specific amounts**:
```
python pipeline/scripts/download_data.py --arxiv 100 --biorxiv 50 --pdb 200 --images 100
```
This gives you precise control over how much data you want from each source.

**Download to specific location**:
```
python pipeline/scripts/download_data.py --output-dir /custom/path --all
```
Useful if you want data in a non-default location.

**Resume incomplete downloads**:
```
python pipeline/scripts/download_data.py --resume
```
If a download was interrupted, this continues from where it stopped.

#### Where Downloaded Data Goes

The download script automatically organizes files:
- arXiv and bioRxiv papers → `/Data/text/` (as PDF files)
- UniProt sequences → `/Data/sequences/` (as FASTA files)
- PDB structures → `/Data/structures/` (as PDB files)
- Images → `/Data/images/` (as JPG/PNG files)

You don't need to manually organize files; the script handles this automatically.

### Step 3: Process Data Through the Pipeline

Once data is downloaded and organized, process it through the pipeline using the appropriate script for your data type.

#### Processing All Local Data

Use `process_local_files.py` to process all downloaded data in one command:

Run from `backend/Services` directory:
```
python pipeline/scripts/process_local_files.py --data-types text sequence structure image
```

**Parameters for process_local_files.py**:
- `--data-types`: Specify which types to process (space-separated: `text sequence structure image`)
  - `text`: Process PDF and text documents
  - `sequence`: Process FASTA files
  - `structure`: Process PDB files
  - `image`: Process image files
- `--data-dir`: Path to data directory (default: `../../Data`)
- `--stats-only`: Only show statistics without processing

**Example uses**:
- Process only text: `--data-types text`
- Process text and sequences: `--data-types text sequence`
- Process everything: `--data-types text sequence structure image`

#### Processing Specific Data Types

For arXiv papers specifically (if you want more control):

**Collect and process arXiv papers** using `collect_arxiv.py`:

Parameters:
- `--query`: Search term (required, example: `--query "protein design"`)
- `--max-results`: Number of papers to collect (default: 10, example: `--max-results 100`)
- `--category`: Filter by arXiv category (optional, example: `--category "q-bio.BM"`)
- `--output`: Save paper list to JSON file (optional)
- `--sort-by`: Sort results by date or relevance (default: relevance)

**Common arXiv categories**:
- `q-bio.BM`: Biomolecules (proteins, DNA, etc.)
- `q-bio.PE`: Populations and Evolution
- `cs.LG`: Machine Learning
- `stat.ML`: Statistical Machine Learning

Run from `backend/Services`:
```
python pipeline/scripts/collect_arxiv.py --query "protein design" --max-results 100 --category "q-bio.BM"
```

For quick testing without full integration, use `collect_arxiv_simple.py`:
```
python pipeline/scripts/collect_arxiv_simple.py "protein design" 50
```
This quickly collects papers without additional options.

### Step 4: Understanding the Pipeline Workflow

#### Text Processing Workflow

When the pipeline processes text documents:

1. **Collection**: Finds all PDF and TXT files in the `/Data/text/` directory
2. **Ingestion**: Extracts text from PDFs (handling multiple pages) or reads TXT files
3. **Normalization**: Removes control characters, normalizes whitespace, ensures consistent encoding
4. **Enrichment**: Extracts statistics (word count, reading level) and identifies named entities (people, organizations)
5. **Embedding**: Converts text to 384-dimensional semantic vectors capturing document meaning
6. **Storage**: Saves vectors and metadata to `qdesign_text` collection in Qdrant

**Result**: Document can now be searched by semantic similarity to find papers on related topics.

#### Sequence Processing Workflow

When processing protein sequences:

1. **Collection**: Finds all FASTA files in `/Data/sequences/`
2. **Ingestion**: Parses FASTA format, extracts individual sequences and descriptions
3. **Normalization**: Converts to uppercase, removes gaps and whitespace, validates amino acids
4. **Enrichment**: Calculates amino acid composition, molecular weight, charge, and hydrophobicity
5. **Embedding**: Creates 384-dimensional vectors capturing sequence similarity
6. **Storage**: Saves vectors to `qdesign_sequences` collection with sequence data

**Result**: Sequences can be searched to find homologous proteins and identify sequence families.

#### Structure Processing Workflow

When processing protein structures:

1. **Collection**: Finds all PDB files in `/Data/structures/`
2. **Ingestion**: Parses PDB format, extracts coordinates, chains, and heteroatoms
3. **Normalization**: Validates coordinates, standardizes atom names, checks integrity
4. **Enrichment**: Analyzes structural properties (size, chains, experimental method)
5. **Embedding**: Creates 256-dimensional vectors based on structural characteristics
6. **Storage**: Saves vectors to `qdesign_structures` collection with structure metadata

**Result**: Structures can be retrieved by 3D similarity to find proteins with similar folds.

#### Image Processing Workflow

When processing images:

1. **Collection**: Finds all image files (JPG, PNG, BMP, GIF, WebP) in `/Data/images/`
2. **Ingestion**: Loads images and extracts metadata (dimensions, format)
3. **Normalization**: Ensures consistent handling across different image types
4. **Enrichment**: Extracts visual features (color distribution, texture, structure)
5. **Embedding**: Creates 3072-dimensional vectors capturing visual content
6. **Storage**: Saves vectors to `qdesign_images` collection with image metadata

**Result**: Images can be searched to find visually similar scientific diagrams and figures.

### Step 5: Verify Qdrant Connection

Before processing data, verify that Qdrant is running and accessible:

Run from `backend/Services`:
```
python pipeline/scripts/verify_qdrant.py
```

This script shows:
- Qdrant server connection status
- Available collections and their vector counts
- Vector dimensions per collection
- Total vectors in database

If Qdrant is not running, you'll need to start it:
```
docker run -p 6333:6333 qdrant/qdrant:latest
```

---

## Configuration

Configuration settings are defined in `config.py`. Key settings include:

**Qdrant Connection**:
- Default URL: `http://localhost:6333`
- Default timeout: 30 seconds
- Collections are created automatically

**Rate Limiting**:
- arXiv: 3 requests per second (API limit)
- bioRxiv: 2 requests per second
- Request timeout: 30 seconds
- Automatic retry: up to 3 times on failure

**Logging**:
- Default level: INFO
- Log file: `pipeline.log`

You can override settings using environment variables (prefix with `PIPELINE_` or `QDRANT_`).

---

## Running Tests

The pipeline includes comprehensive tests for each data type to verify everything works correctly.

#### Test Scripts

Each test simulates the complete pipeline for a specific data modality:

**Test Text Pipeline** (creates sample documents and processes them):
```
python -m pipeline.tests.test_text_pipeline
```
Tests PDF/text ingestion, normalization, enrichment, embedding, and storage.

**Test Sequence Pipeline** (creates sample FASTA files and processes them):
```
python -m pipeline.tests.test_sequence_pipeline
```
Tests sequence parsing, validation, enrichment, embedding, and storage.

**Test Structure Pipeline** (creates sample PDB files and processes them):
```
python -m pipeline.tests.test_structure_pipeline
```
Tests PDB parsing, enrichment, structure embedding, and storage.

**Test Image Pipeline** (creates sample images and processes them):
```
python -m pipeline.tests.test_image_pipeline
```
Tests image loading, metadata extraction, visual embedding, and storage.

**Test Monitoring System** (tests health, quality, and balance tracking):
```
python -m pipeline.tests.test_monitoring
```
Tests all monitoring components and report generation.

#### Current Test Results

All tests are passing with the following results:
- **Text**: 31 vectors stored in qdesign_text
- **Sequences**: 45 vectors stored in qdesign_sequences
- **Structures**: 37 vectors stored in qdesign_structures
- **Images**: 26 vectors stored in qdesign_images
- **Total**: 139 vectors across 4 modalities

---

## Monitoring & Quality Assurance

The pipeline includes real-time monitoring of data quality and pipeline health.

### What Gets Monitored

**Pipeline Health**:
- Ingestion success rate per source (target: >95%)
- Failed sources and error patterns
- Data freshness (how recent data is)
- Warnings when success drops below thresholds

**Data Quality**:
- Duplicate detection (identifies duplicate records)
- Metadata completeness (checks required fields are filled)
- Embedding validity (validates vector dimensions and values)
- Error rates during processing

**Modality Balance**:
- Distribution of data across modalities (target: 25% each)
- Source diversity (prevents over-reliance on single source)
- Collection balance (ensures even distribution across collections)

### Checking Status

After processing data, review the monitoring reports to understand data quality and pipeline health. Reports show:
- Overall status (HEALTHY, WARNING, UNHEALTHY, IMBALANCED)
- Metrics per monitoring component
- Issues and warnings with recommended thresholds
- Historical trends

---

## Supported Data Formats

| Data Type | File Formats | Supported Sources | Pipeline Steps |
|-----------|--------------|-------------------|-----------------|
| Text | PDF, TXT | arXiv, bioRxiv, local | Collect → Ingest → Normalize → Enrich → Embed → Store |
| Sequence | FASTA, FA | UniProt, local | Collect → Ingest → Normalize → Enrich → Embed → Store |
| Structure | PDB | PDB, local | Collect → Ingest → Normalize → Enrich → Embed → Store |
| Image | JPG, PNG, BMP, GIF, WebP | Wikimedia, local | Collect → Ingest → Normalize → Enrich → Embed → Store |

---

## Troubleshooting

**Problem**: "Qdrant connection refused"
- **Solution**: Ensure Qdrant is running. Start it with Docker or verify the URL in config.

**Problem**: "API rate limit exceeded"
- **Solution**: Wait a few seconds and retry. The pipeline includes automatic rate limiting to prevent this.

**Problem**: "Some PDF files fail to extract text"
- **Solution**: Some PDFs are scanned images or have unusual encoding. The pipeline logs these and continues with other files.

**Problem**: "Embedding process is slow"
- **Solution**: This is normal for large batches. The pipeline processes documents in order. Use `--data-types` to process only needed types.

---

## Performance Characteristics

**Processing Speed** (approximate, per item):
- Text: 0.5-1 second per document
- Sequence: 0.5-1 second per sequence
- Image: 2-5 seconds per image
- Structure: 1-2 seconds per structure

**Storage Requirements** (approximate, per 1000 vectors):
- Text embeddings: 1.5 MB
- Sequence embeddings: 1.5 MB
- Image embeddings: 12 MB
- Structure embeddings: 1 MB

**Memory Usage**:
- Text/Sequence models: ~400 MB each
- Image model: ~500 MB
- Structure model: ~100 MB (lightweight)

---

## Summary - Getting Started in 5 Steps

1. **Check Setup**: Run `python pipeline/scripts/verify_qdrant.py` to confirm Qdrant is accessible

2. **Download Data**: Run `python pipeline/scripts/download_data.py --all` to download sample data

3. **Process Data**: Run `python pipeline/scripts/process_local_files.py --data-types text sequence structure image`

4. **Run Tests**: Execute test scripts to verify everything works with your data

5. **Check Results**: Use `verify_qdrant.py` to see stored vectors and counts per collection

The pipeline will automatically organize all data, process it through the full workflow, and store vectors in Qdrant for semantic search.

---

## Support & Documentation

For detailed component documentation, see:
- [monitoring/README.md](monitoring/README.md) - Monitoring system details
- [monitoring/INTEGRATION_GUIDE.md](monitoring/INTEGRATION_GUIDE.md) - Integration patterns
- [tests/README.md](tests/README.md) - Testing documentation
- `requirements.txt` - Python dependencies

---

## License

See parent project LICENSE

---

## Contact

For questions or issues, refer to the project documentation or contact the development team.
