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

class DataPoolComment(BaseModel):
    """Model for comments on data entries."""
    id: str
    text: str
    author: str
    created_at: datetime
    
class DataPoolItem(BaseModel):
    """Model for individual data entries in the data pool."""
    _id: str
    type: str  # 'pdb', 'pdf', 'image', 'sequence', 'text', 'other'
    name: str
    description: Optional[str] = None
    content: Optional[str] = None
    fileUrl: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    addedBy: str  # Will be ObjectId as string
    addedAt: datetime
    comments: List[DataPoolComment] = []

class ProcessingRequest(BaseModel):
    """Model for the simplified processing request."""
    name: str
    mainObjective: str
    secondaryObjectives: List[str] = []
    constraints: List[str] = []
    notes: List[str] = []
    description: Optional[str] = None
    dataPool: List[DataPoolItem]
    
    # Legacy support
    @property
    def Notes(self) -> List[str]:
        return self.notes
    
    @property 
    def Constraints(self) -> List[str]:
        return self.constraints

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
    notes: List[str] = []