"""
QDesign Pipeline Configuration
Loads settings from .env and environment variables
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class CollectorConfig:
    """Configuration for data collectors"""
    arxiv_api_url: str = "http://export.arxiv.org/api/query"
    biorxiv_api_url: str = "https://api.biorxiv.org/details"
    pdb_api_url: str = "https://data.rcsb.org/rest/v1"
    request_timeout: int = 30
    max_retries: int = 3


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models"""
    device: str = "cpu"
    fastembed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    esm_model: str = "esm2_t12_35M_UR50D"
    batch_size: int = 32
    normalize: bool = True


@dataclass
class StorageConfig:
    """Configuration for Qdrant and PostgreSQL"""
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_text: str = "qdesign_text"
    qdrant_collection_structures: str = "qdesign_structures"
    qdrant_collection_sequences: str = "qdesign_sequences"
    qdrant_collection_images: str = "qdesign_images"
    
    pg_dsn: str = "postgresql://qdesign:qdesign@localhost:5432/qdesign"
    vector_size: int = 384  # fastembed default


@dataclass
class PipelineConfig:
    """Configuration for pipeline orchestration"""
    log_level: str = "INFO"
    log_file: str = "logs/pipeline.log"
    batch_size: int = 32
    max_workers: int = 4
    skip_existing: bool = True
    parallel: bool = True


class Config:
    """Main configuration class that loads from environment"""
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize configuration from .env file or environment variables
        
        Args:
            env_path: Path to .env file. If None, uses current directory.
        """
        # Load .env file if it exists
        if env_path is None:
            env_path = Path.cwd() / '.env'
        elif not Path(env_path).is_absolute():
            env_path = Path.cwd() / env_path
        
        if Path(env_path).exists():
            self._load_env_file(env_path)
        
        # Initialize sub-configs
        self.collector = CollectorConfig(
            arxiv_api_url=os.getenv("ARXIV_API_URL", "http://export.arxiv.org/api/query"),
            biorxiv_api_url=os.getenv("BIORXIV_API_URL", "https://api.biorxiv.org/details"),
            pdb_api_url=os.getenv("PDB_API_URL", "https://data.rcsb.org/rest/v1"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )
        
        self.embedding = EmbeddingConfig(
            device=os.getenv("EMBED_DEVICE", "cpu"),
            fastembed_model=os.getenv("FASTEMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            esm_model=os.getenv("ESM_MODEL", "esm2_t12_35M_UR50D"),
            batch_size=int(os.getenv("BATCH_SIZE", "32")),
            normalize=os.getenv("NORMALIZE_EMBEDDINGS", "true").lower() == "true",
        )
        
        self.storage = StorageConfig(
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_collection_text=os.getenv("QDRANT_COLLECTION_TEXT", "qdesign_text"),
            qdrant_collection_structures=os.getenv("QDRANT_COLLECTION_STRUCTURES", "qdesign_structures"),
            qdrant_collection_sequences=os.getenv("QDRANT_COLLECTION_SEQUENCES", "qdesign_sequences"),
            qdrant_collection_images=os.getenv("QDRANT_COLLECTION_IMAGES", "qdesign_images"),
            pg_dsn=os.getenv("PG_DSN", "postgresql://qdesign:qdesign@localhost:5432/qdesign"),
            vector_size=int(os.getenv("VECTOR_SIZE", "384")),
        )
        
        self.pipeline = PipelineConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/pipeline.log"),
            batch_size=int(os.getenv("BATCH_SIZE", "32")),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            skip_existing=os.getenv("SKIP_EXISTING", "true").lower() == "true",
            parallel=os.getenv("PARALLEL", "true").lower() == "true",
        )
    
    def _load_env_file(self, env_path: Path) -> None:
        """Load environment variables from .env file"""
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"Config(\n"
            f"  collector={self.collector},\n"
            f"  embedding={self.embedding},\n"
            f"  storage={self.storage},\n"
            f"  pipeline={self.pipeline}\n"
            f")"
        )
    
    # Properties for backward compatibility
    @property
    def arxiv_api_url(self) -> str:
        return self.collector.arxiv_api_url
    
    @property
    def biorxiv_api_url(self) -> str:
        return self.collector.biorxiv_api_url
    
    @property
    def pdb_api_url(self) -> str:
        return self.collector.pdb_api_url
    
    @property
    def request_timeout(self) -> int:
        return self.collector.request_timeout
    
    @property
    def max_retries(self) -> int:
        return self.collector.max_retries
    
    @property
    def device(self) -> str:
        return self.embedding.device
    
    @property
    def fastembed_model(self) -> str:
        return self.embedding.fastembed_model
    
    @property
    def esm_model(self) -> str:
        return self.embedding.esm_model
    
    @property
    def batch_size(self) -> int:
        return self.embedding.batch_size
    
    @property
    def normalize_embeddings(self) -> bool:
        return self.embedding.normalize
    
    @property
    def qdrant_url(self) -> str:
        return self.storage.qdrant_url
    
    @property
    def qdrant_text_collection(self) -> str:
        return self.storage.qdrant_collection_text
    
    @property
    def qdrant_sequence_collection(self) -> str:
        return self.storage.qdrant_collection_sequences
    
    @property
    def qdrant_structure_collection(self) -> str:
        return self.storage.qdrant_collection_structures
    
    @property
    def qdrant_image_collection(self) -> str:
        return self.storage.qdrant_collection_images
    
    @property
    def pg_dsn(self) -> str:
        return self.storage.pg_dsn
    
    @property
    def log_level(self) -> str:
        return self.pipeline.log_level
    
    @property
    def log_file(self) -> str:
        return self.pipeline.log_file


# Global config instance
_config: Optional[Config] = None


def get_config(env_path: Optional[str] = None) -> Config:
    """
    Get or create the global config instance
    
    Args:
        env_path: Path to .env file (only used on first call)
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(env_path)
    return _config
