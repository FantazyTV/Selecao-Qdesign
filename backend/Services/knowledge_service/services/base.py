"""Base service with shared dependencies"""

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseKnowledgeService:
    """Base class with shared dependencies and utilities"""

    def __init__(self, db: Session, qdrant_client=None, embedder=None):
        """Initialize with database and optional clients"""
        self.db = db
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.logger = logger
