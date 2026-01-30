"""
Qdrant Ingestion Script for PDFs and Images
- Ingests PDFs into Qdrant collection 'pdfs', storing file path in payload
- Ingests images into Qdrant collection 'images' using CLIP embeddings, storing file path in payload
"""

import os
from pathlib import Path
from typing import List
import qdrant_client
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from PIL import Image
import torch
import clip
import fitz  # PyMuPDF for PDF text extraction

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
PDF_DIR = DATA_DIR / "text" / "papers"
IMG_DIRS = [DATA_DIR / "images" / "diagrams", DATA_DIR / "images" / "microscopy"]

# Qdrant setup
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))

client = qdrant_client.QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Models
pdf_model = SentenceTransformer("all-MiniLM-L6-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)

# --- PDF Ingestion ---
def extract_pdf_text(pdf_path: Path) -> str:
    try:
        doc = fitz.open(str(pdf_path))
        text = " ".join(page.get_text() for page in doc)
        return text.strip()
    except Exception as e:
        print(f"Failed to extract text from {pdf_path}: {e}")
        return ""

def ingest_pdfs_to_qdrant():
    client.recreate_collection(
        collection_name="pdfs",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    points = []
    for idx, pdf_path in enumerate(pdf_files):
        text = extract_pdf_text(pdf_path)
        if not text:
            continue
        embedding = pdf_model.encode(text[:2000], normalize_embeddings=True)  # Truncate for speed
        points.append(PointStruct(
            id=idx,
            vector=embedding.tolist(),
            payload={"path": str(pdf_path)}
        ))
    if points:
        client.upsert(collection_name="pdfs", points=points)
        print(f"Ingested {len(points)} PDFs into Qdrant.")
    else:
        print("No PDFs ingested.")

# --- Image Ingestion ---
def get_image_files() -> List[Path]:
    files = []
    for d in IMG_DIRS:
        files.extend(d.glob("*.png"))
        files.extend(d.glob("*.jpg"))
        files.extend(d.glob("*.jpeg"))
    return files

def embed_image_clip(img_path: Path):
    try:
        image = Image.open(img_path).convert("RGB")
        image_input = clip_preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = clip_model.encode_image(image_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten()
    except Exception as e:
        print(f"Failed to embed image {img_path}: {e}")
        return None

def ingest_images_to_qdrant():
    client.recreate_collection(
        collection_name="images",
        vectors_config=VectorParams(size=512, distance=Distance.COSINE)
    )
    img_files = get_image_files()
    points = []
    for idx, img_path in enumerate(img_files):
        embedding = embed_image_clip(img_path)
        if embedding is None:
            continue
        points.append(PointStruct(
            id=idx,
            vector=embedding.tolist(),
            payload={"path": str(img_path)}
        ))
    if points:
        client.upsert(collection_name="images", points=points)
        print(f"Ingested {len(points)} images into Qdrant.")
    else:
        print("No images ingested.")

if __name__ == "__main__":
    ingest_pdfs_to_qdrant()
    ingest_images_to_qdrant()
