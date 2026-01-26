# Pipeline Tests

This directory contains comprehensive tests for each data type supported by the QDesign pipeline.

## Test Files

### 1. **test_image_pipeline.py**
Tests the complete image processing pipeline:
- **Formats:** JPG, PNG, GIF, WEBP, TIFF, BMP
- **Steps:** Collection → Ingestion → Embedding → Qdrant Storage
- **Embedding:** PIL-based feature extraction (3072 dimensions)
- **Usage:**
  ```bash
  python pipeline/tests/test_image_pipeline.py
  ```

### 2. **test_text_pipeline.py**
Tests the complete text processing pipeline:
- **Formats:** TXT, Markdown-formatted text
- **Steps:** Collection → Ingestion → Embedding → Qdrant Storage
- **Embedding:** FastEmbed text encoder (384 dimensions)
- **Usage:**
  ```bash
  python pipeline/tests/test_text_pipeline.py
  ```

### 3. **test_sequence_pipeline.py**
Tests the complete biological sequence processing pipeline:
- **Formats:** FASTA (protein, DNA, RNA)
- **Steps:** Collection → Ingestion → Embedding → Qdrant Storage
- **Embedding:** FastEmbed sequence encoder (384 dimensions)
- **Usage:**
  ```bash
  python pipeline/tests/test_sequence_pipeline.py
  ```

### 4. **test_structure_pipeline.py**
Tests the complete protein structure processing pipeline:
- **Formats:** PDB (Protein Data Bank)
- **Steps:** Collection → Ingestion → Embedding → Qdrant Storage
- **Embedding:** Lightweight feature extraction without heavy dependencies (256 dimensions)
- **Features Extracted:**
  - C-alpha coordinate statistics
  - Distance and angle distributions
  - Radius of gyration
  - Bounding box dimensions
  - Residue composition
- **Usage:**
  ```bash
  python pipeline/tests/test_structure_pipeline.py
  ```

## Helper Scripts

### **create_sample_images.py**
Generates sample images for testing the image pipeline:
- Creates 16 synthetic images covering various visualization types
- Includes: protein structures, DNA helices, molecular diagrams, graphs, microscopy, heatmaps, spectra, patterns
- **Usage:**
  ```bash
  python pipeline/tests/create_sample_images.py
  ```
- **Output:** Images saved to `Data/images/diagrams/`

## Running All Tests

Run all data type tests sequentially:

```bash
# Test image pipeline
python pipeline/tests/test_image_pipeline.py

# Test text pipeline
python pipeline/tests/test_text_pipeline.py

# Test sequence pipeline
python pipeline/tests/test_sequence_pipeline.py

# Test structure pipeline
python pipeline/tests/test_structure_pipeline.py
```

Or run them all at once with a shell script:

```bash
for test in pipeline/tests/test_*_pipeline.py; do
  echo "Running $test..."
  python "$test"
  echo ""
done
```

## Expected Output

Each test reports:
- ✅ Collection statistics (files found, total size)
- ✅ Ingestion results (parsing success rate)
- ✅ Embedding statistics (vectors created, dimension, time)
- ✅ Storage confirmation (Qdrant vector counts)
- ✅ Final summary (SUCCESS/FAILED)

Example output:
```
======================================================================
IMAGE PIPELINE TEST - Collect, Ingest, Embed, Store
======================================================================

STEP 1: Prepare images
----------------------------------------------------------------------
Using existing 16 images

STEP 2: Collect local images
----------------------------------------------------------------------
Collected 16 images in 0.00s
  1. protein_structure.jpg (0.04 MB)
  ...

STEP 3: Ingest images
----------------------------------------------------------------------
Ingested 16 images in 0.01s

STEP 4: Embed images to vectors
----------------------------------------------------------------------
Embedded 16 images in 0.74s

STEP 5: Store vectors in Qdrant
----------------------------------------------------------------------
Stored 16 vectors in 0.12s

Qdrant Status:
  • qdesign_images: 26 vectors
  • qdesign_text: 26 vectors
  • qdesign_sequences: 35 vectors
  • qdesign_structures: 24 vectors

======================================================================
TEST SUMMARY
======================================================================
Total images processed: 16
Successfully embedded: 16
Stored in Qdrant: 16
Errors: 0
Status: SUCCESS
======================================================================
```

## Requirements

### System Requirements
- Python 3.8+
- Qdrant running (see backend/Core/docker-compose.yml)

### Python Dependencies
```bash
# Image processing
pip install pillow

# Text/Sequence embedding
pip install fastembed

# Vector storage
pip install qdrant-client

# Scientific computing
pip install numpy scipy
```

## Troubleshooting

### "Qdrant connection failed"
Ensure Qdrant is running:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### "No images/text/sequences found"
Check that data files exist in the correct locations:
- Images: `Data/images/diagrams/`
- Text: `Data/text/`
- Sequences: `Data/sequences/`
- Structures: `Data/structures/`

Run the helper script to generate sample files:
```bash
python pipeline/tests/create_sample_images.py
```

### "Embedding failed"
Check the error logs in the test output. Common causes:
- File format not supported
- Corrupted data file
- Missing dependencies (install pillow, fastembed, etc.)

## Test Results Tracking

Each test creates embeddings in the following Qdrant collections:
- `qdesign_images` - Image vectors (3072 dims)
- `qdesign_text` - Text vectors (384 dims)
- `qdesign_sequences` - Sequence vectors (384 dims)
- `qdesign_structures` - Structure vectors (256 dims)

Track progress across tests to verify the pipeline works with diverse data types.
