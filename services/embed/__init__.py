"""
RAF Chatbot — Embedding Service Module

Provides embedding generation and vector storage capabilities.

Exports:
- EmbeddingService: Main service for embedding documents
- ModelManager: Manages model lifecycle
- EmbeddingGenerator: Generates embeddings for chunks
- QdrantVectorStore: Vector storage in Qdrant
- Data models: Document, EmbeddingVector, EmbeddingResponse, etc.
"""

from .models import (
    Document,
    DocumentChunk,
    EmbeddingRequest,
    EmbeddingVector,
    EmbeddingResponse,
    EmbeddingError,
    VectorPayload,
    VectorPointCreate,
    ModelInfo,
    ModelCache,
    QdrantCollectionInfo,
    BatchEmbeddingJob,
    EmbeddingStatistics,
    EmbeddingServiceHealth,
)

from .service import (
    ModelManager,
    EmbeddingGenerator,
    QdrantVectorStore,
    EmbeddingService,
)

__all__ = [
    # Models
    "Document",
    "DocumentChunk",
    "EmbeddingRequest",
    "EmbeddingVector",
    "EmbeddingResponse",
    "EmbeddingError",
    "VectorPayload",
    "VectorPointCreate",
    "ModelInfo",
    "ModelCache",
    "QdrantCollectionInfo",
    "BatchEmbeddingJob",
    "EmbeddingStatistics",
    "EmbeddingServiceHealth",
    # Services
    "ModelManager",
    "EmbeddingGenerator",
    "QdrantVectorStore",
    "EmbeddingService",
]