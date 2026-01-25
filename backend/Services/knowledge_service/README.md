# Knowledge Service

Manages the human-in-the-loop knowledge base curation for QDesign projects.

## Architecture

```
knowledge_service/
├── models/              Database models (KnowledgeBase, KnowledgeResource, ResourceAnnotation)
├── services/            Core business logic (KnowledgeService)
├── api/                 FastAPI routes
├── schemas/             Pydantic validation models
└── utils/               Helpers (keyword extraction, explanations)
```

## Features

### 1. Resource Discovery
- Parse project description and extract keywords
- Query Qdrant for proteins, papers, images
- Generate explanations for each match (why it's relevant)
- Rank by relevance score

### 2. Knowledge Base Curation
- View all discovered resources with explanations
- Delete irrelevant resources (soft delete)
- Add custom resources manually
- Annotate resources (comments, tags, confidence scores)
- Reorder by priority

### 3. Finalization & Export
- Lock knowledge base status
- Export validated resources for graph construction service

## Data Model

### KnowledgeBase
Main container for a project's knowledge base.

```
- id: Unique identifier
- project_id: Associated project
- status: discovering → ready → active
- total_resources: Count of included resources
- total_annotations: Count of annotations
- created_at, updated_at: Timestamps
```

### KnowledgeResource
Individual resource (protein, paper, image, etc.)

```
- id: Unique identifier
- knowledge_base_id: Parent knowledge base
- resource_type: protein | paper | image | experiment | custom
- source: alphafold | arxiv | biorxiv | manual | etc.
- external_id: UniProt ID, arXiv ID, etc.
- title: Resource title
- url: Link to resource
- relevance_score: 0-100 (based on semantic similarity)
- matching_keywords: List of matched terms
- explanation: Why it's included
- metadata: Source-specific data (pLDDT score, abstract, etc.)
- included: Boolean (false = soft deleted)
- order: User-defined priority
```

### ResourceAnnotation
User annotations on resources

```
- id: Unique identifier
- resource_id: Parent resource
- comment: Free-form text
- tags: List of user-defined tags
- confidence_score: 0-1 (user's confidence in relevance)
- created_by: User ID
- created_at, updated_at: Timestamps
```

## API Endpoints

### Discovery
```
POST /api/v1/knowledge/discover
  Input: project_id, project_description, top_k, min_relevance
  Output: KnowledgeBase with resources
```

### Retrieval
```
GET /api/v1/knowledge/{knowledge_base_id}
  Output: Full knowledge base with resources and annotations
```

### CRUD Operations
```
DELETE /api/v1/knowledge/resources/{resource_id}
  Soft delete a resource

POST /api/v1/knowledge/resources/custom
  Add custom resource

POST /api/v1/knowledge/resources/{resource_id}/annotate
  Add annotation

POST /api/v1/knowledge/{knowledge_base_id}/reorder
  Reorder resources by priority
```

### Finalization
```
POST /api/v1/knowledge/{knowledge_base_id}/finalize
  Mark as ready for graph construction

GET /api/v1/knowledge/{knowledge_base_id}/export
  Export for graph construction service
```

## Usage Example

```python
from knowledge_service import KnowledgeService
from sqlalchemy.orm import Session

# Initialize
service = KnowledgeService(db_session, qdrant_client, embedder)

# 1. Discover resources
kb = service.discover_resources(
    project_id="proj_123",
    project_description="Design biodegradable, high-strength proteins",
    top_k=20,
    min_relevance=0.6
)

# 2. Get and view knowledge base
kb_data = service.get_knowledge_base(kb.id)
for resource in kb_data["resources"]:
    print(f"{resource['title']}: {resource['relevance_score']}%")

# 3. Curate: delete irrelevant, add custom, annotate
service.delete_resource(resource_id="res_123")

custom_res = service.add_custom_resource(
    knowledge_base_id=kb.id,
    resource_type="paper",
    title="Novel protein folding",
    url="https://example.com",
    comment="High relevance for hierarchical structure"
)

service.annotate_resource(
    resource_id=custom_res.id,
    user_id="user_456",
    tags=["high-priority", "experimental"],
    confidence_score=0.9
)

# 4. Finalize
service.finalize_knowledge_base(kb.id)

# 5. Export for graph construction
export_data = service.export_for_graph_construction(kb.id)
```

## Integration Points

### With Qdrant
- Uses existing vector database
- Queries collections: qdesign_structures, qdesign_papers, qdesign_images
- Each collection contains metadata payloads with source info

### With Embedder
- Uses existing FastembedTextEmbedder (384-dim vectors)
- Embeds keywords from project description for semantic search

### With Graph Construction Service
- Exports finalized knowledge base
- Resources become nodes in knowledge graph
- Annotations provide edge weights and relationship hints

## Design Principles

1. **Clean separation of concerns**: Models, services, routes, schemas separate
2. **Modularity**: Easy to add new resource types or search strategies
3. **Explainability**: Every resource includes why it was selected
4. **Human control**: Full CRUD and annotation capabilities
5. **Soft deletes**: Resources marked as deleted, not removed
6. **Efficient queries**: Indexed by knowledge_base_id, resource_id

## Future Enhancements

- Advanced keyword extraction (spaCy NER, LLM-based)
- Duplicate detection and merging
- Batch operations for resources
- Search/filter within knowledge base
- Version history of knowledge bases
- Collaborative annotations (multiple users)
