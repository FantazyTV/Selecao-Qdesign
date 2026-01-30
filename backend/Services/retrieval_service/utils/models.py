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
    PROTEIN = "pdb"
    DOCUMENT = "pdf"
    IMAGE = "image"
    SEQUENCE = "sequence"
    STRUCTURE = "structure"
    OBJECTIVE = "objective"
    CONCEPT = "concept"
    ANNOTATION = "annotation"
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


# Updated GraphNode to match the provided TypeScript schema
class GraphNode(BaseModel):
    """Node model for API responses, matching frontend schema."""
    id: str
    type: str  # enum: ['pdb', 'pdf', 'image', 'sequence', 'text', 'annotation']
    label: str
    description: Optional[str] = None
    content: Optional[str] = None
    fileUrl: Optional[str] = None
    largeFileId: Optional[str] = None
    position: Optional[Dict[str, float]] = None  # {x: number, y: number}
    trustLevel: Optional[str] = 'high'  # enum: ['high', 'medium', 'low', 'untrusted']
    notes: Optional[list] = []  # Should be List[GraphNodeNote], but not defined here
    metadata: Optional[Dict[str, Any]] = None
    groupId: Optional[str] = None


# Updated GraphEdge to match the provided TypeScript schema
class GraphEdge(BaseModel):
    """Edge model for API responses, matching frontend schema."""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    correlationType: str  # enum: ['similar', 'cites', 'contradicts', 'supports', 'derived', 'custom']
    strength: Optional[float] = None  # min: 0, max: 1
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GraphData(BaseModel):
    """Complete graph representation."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = {}

class GraphAnalysisResponse(BaseModel):
    """Response model for graph analysis."""
    graph: GraphData
    summary: str
    processing_stats: Dict[str, Any] = {}
    notes: List[str] = []