from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    confidence: float = Field(ge=0.0, le=1.0)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: str | None = None


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    version: str
