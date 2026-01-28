from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class DataEntryType(str, Enum):
    """Supported data entry types."""
    PDF = "pdf"
    TEXT = "text" 
    PDB = "pdb"
    CIF = "cif"
    IMAGE = "image"
    FASTA = "fasta"
    UNKNOWN = "unknown"

class Comment(BaseModel):
    """Model for comments on data entries."""
    id: str
    text: str
    author: str
    created_at: datetime
    
class DataEntry(BaseModel):
    """Model for individual data entries in the data pool."""
    id: str = Field(..., alias="_id")
    type: DataEntryType
    name: str
    description: Optional[str] = ""
    content: str  # Base64 encoded or raw text content
    addedBy: str
    addedAt: datetime
    comments: List[Comment] = []
    
    class Config:
        validate_by_name = True

class DataPoolRequest(BaseModel):
    """Model for the complete request containing data pool and objectives."""
    dataPool: List[DataEntry]
    mainObjective: str
    secondaryObjectives: List[str] = []
    Notes: List[str] = []
    Constraints: List[str] = []

class NodeType(str, Enum):
    """Graph node types."""
    PROTEIN = "protein"
    DOCUMENT = "document"
    IMAGE = "image"
    SEQUENCE = "sequence"
    STRUCTURE = "structure"
    OBJECTIVE = "objective"
    CONCEPT = "concept"
    RELATIONSHIP = "relationship"

class EdgeType(str, Enum):
    """Graph edge types."""
    SIMILARITY = "similarity"
    REFERENCES = "references"
    CONTAINS = "contains"
    RELATES_TO = "relates_to"
    SUPPORTS = "supports"
    CONFLICTS = "conflicts"
    DERIVES_FROM = "derives_from"
    MENTIONS = "mentions"

class GraphNode(BaseModel):
    """Enhanced node model for API responses."""
    id: str
    type: NodeType
    label: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    content_summary: Optional[str] = None
    relevance_score: Optional[float] = None

class GraphEdge(BaseModel):
    """Enhanced edge model for API responses."""
    from_id: str
    to_id: str
    type: EdgeType
    score: Optional[float] = None
    evidence: Optional[str] = None
    provenance: Dict[str, Any] = {}

class GraphData(BaseModel):
    """Complete graph representation."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = {}

class GraphAnalysisResponse(BaseModel):
    """Response model for graph analysis."""
    graphs: List[GraphData]
    summary: str
    processing_stats: Dict[str, Any] = {}
    recommendations: List[str] = []