"""
RAF Chatbot — Embedding Models and Data Contracts

Defines data models for embedding requests, responses, and vector storage.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# DOCUMENT MODELS
# ============================================================================

class Document(BaseModel):
    """A document chunk ready for embedding."""
    
    doc_id: str = Field(description="Unique document identifier")
    chunk_id: str = Field(description="Chunk identifier (doc_id:chunk_number)")
    content: str = Field(description="Text content to embed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    
    class Config:
        extra = "forbid"


class DocumentChunk(BaseModel):
    """A chunk of text extracted from a document."""
    
    chunk_id: str = Field(description="Unique chunk identifier")
    content: str = Field(description="Chunk text content")
    chunk_number: int = Field(ge=0, description="Chunk sequence number")
    char_start: int = Field(ge=0, description="Starting character position")
    char_end: int = Field(ge=0, description="Ending character position")
    file_path: str = Field(description="Source file path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    
    class Config:
        extra = "forbid"


# ============================================================================
# EMBEDDING MODELS
# ============================================================================

class EmbeddingRequest(BaseModel):
    """Request to generate embeddings for documents."""
    
    rag_id: str = Field(description="RAG identifier")
    documents: List[Document] = Field(description="Documents to embed")
    batch_size: Optional[int] = Field(default=32, description="Batch size for processing")
    normalize: Optional[bool] = Field(default=True, description="L2 normalize vectors?")
    
    class Config:
        extra = "forbid"


class EmbeddingVector(BaseModel):
    """A single embedding vector with metadata."""
    
    chunk_id: str = Field(description="Chunk identifier")
    vector: List[float] = Field(description="Embedding vector")
    dimension: int = Field(gt=0, description="Vector dimension")
    model_name: str = Field(description="Model used for embedding")
    normalized: bool = Field(default=False, description="Is vector L2 normalized?")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        extra = "forbid"


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""
    
    rag_id: str = Field(description="RAG identifier")
    vectors: List[EmbeddingVector] = Field(description="Generated embedding vectors")
    total_processed: int = Field(ge=0, description="Total documents processed")
    failed_count: int = Field(ge=0, description="Number of failed embeddings")
    model_name: str = Field(description="Model used")
    dimension: int = Field(gt=0, description="Vector dimension")
    processing_time_seconds: float = Field(ge=0, description="Total processing time")
    
    class Config:
        extra = "forbid"


class EmbeddingError(BaseModel):
    """An error during embedding generation."""
    
    chunk_id: str = Field(description="Chunk that failed to embed")
    error_message: str = Field(description="Error description")
    error_type: str = Field(description="Type of error (e.g., 'timeout', 'oom')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When error occurred")
    
    class Config:
        extra = "forbid"


# ============================================================================
# QDRANT VECTOR STORAGE MODELS
# ============================================================================

class VectorPayload(BaseModel):
    """Payload stored with vector in Qdrant."""
    
    chunk_id: str = Field(description="Chunk identifier")
    file_path: str = Field(description="Source file path")
    content: str = Field(description="Original text content")
    chunk_number: int = Field(ge=0, description="Chunk sequence number")
    char_start: int = Field(ge=0, description="Character position in file")
    char_end: int = Field(ge=0, description="Character position in file")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    ingested_at: datetime = Field(default_factory=datetime.utcnow, description="When ingested")
    
    class Config:
        extra = "forbid"


class VectorPointCreate(BaseModel):
    """Point to create in Qdrant collection."""
    
    id: int = Field(description="Unique point ID (hash of chunk_id)")
    vector: List[float] = Field(description="Embedding vector")
    payload: VectorPayload = Field(description="Associated metadata and content")
    
    class Config:
        extra = "forbid"


class QdrantCollectionInfo(BaseModel):
    """Information about a Qdrant collection."""
    
    collection_name: str = Field(description="Collection name")
    vector_size: int = Field(gt=0, description="Vector dimension")
    points_count: int = Field(ge=0, description="Number of vectors in collection")
    status: str = Field(description="Collection status (e.g., 'green')")
    
    class Config:
        extra = "forbid"


# ============================================================================
# MODEL MANAGEMENT MODELS
# ============================================================================

class ModelInfo(BaseModel):
    """Information about a loaded embedding model."""
    
    model_name: str = Field(description="Hugging Face model identifier")
    model_id: str = Field(description="Internal model identifier (hash)")
    dimension: int = Field(gt=0, description="Output vector dimension")
    max_seq_length: int = Field(ge=128, description="Max input sequence length")
    is_loaded: bool = Field(default=False, description="Is model in memory?")
    loaded_at: Optional[datetime] = Field(default=None, description="When model was loaded")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    class Config:
        extra = "forbid"


class ModelCache(BaseModel):
    """Model cache state."""
    
    max_models: int = Field(ge=1, description="Max models to keep in memory")
    loaded_models: Dict[str, ModelInfo] = Field(default_factory=dict, description="Currently loaded models")
    total_parameters: int = Field(ge=0, description="Total parameters in memory")
    
    class Config:
        extra = "forbid"


class ModelLoadRequest(BaseModel):
    """Request to load an embedding model."""
    
    model_name: str = Field(description="Hugging Face model identifier")
    device: str = Field(default="cpu", description="Device to load on (cpu/cuda/mps)")
    use_cache: bool = Field(default=True, description="Cache model after loading?")
    
    class Config:
        extra = "forbid"


class ModelLoadResponse(BaseModel):
    """Response from model loading."""
    
    model_name: str = Field(description="Model identifier")
    dimension: int = Field(gt=0, description="Output vector dimension")
    max_seq_length: int = Field(ge=128, description="Max input sequence length")
    device: str = Field(description="Device loaded on")
    load_time_seconds: float = Field(ge=0, description="Load time")
    success: bool = Field(description="Was loading successful?")
    
    class Config:
        extra = "forbid"


# ============================================================================
# BATCH PROCESSING MODELS
# ============================================================================

class BatchEmbeddingJob(BaseModel):
    """A batch embedding job."""
    
    job_id: str = Field(description="Unique job identifier")
    rag_id: str = Field(description="RAG identifier")
    total_documents: int = Field(ge=1, description="Total documents to process")
    documents_processed: int = Field(ge=0, description="Documents processed so far")
    documents_failed: int = Field(ge=0, description="Documents that failed")
    status: str = Field(description="Job status (pending/processing/completed/failed)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    errors: List[EmbeddingError] = Field(default_factory=list, description="Errors encountered")
    
    class Config:
        extra = "forbid"


class BatchEmbeddingProgress(BaseModel):
    """Progress update for a batch embedding job."""
    
    job_id: str = Field(description="Job identifier")
    documents_processed: int = Field(ge=0, description="Documents processed")
    documents_failed: int = Field(ge=0, description="Documents failed")
    percent_complete: float = Field(ge=0, le=100, description="Percentage complete")
    estimated_time_remaining_seconds: Optional[float] = Field(default=None, description="ETA")
    errors: List[EmbeddingError] = Field(default_factory=list, description="Errors so far")
    
    class Config:
        extra = "forbid"


# ============================================================================
# STATISTICS AND MONITORING
# ============================================================================

class EmbeddingStatistics(BaseModel):
    """Statistics about embedding generation."""
    
    total_documents_embedded: int = Field(ge=0, description="Total documents embedded")
    total_failed: int = Field(ge=0, description="Total failures")
    avg_time_per_document_ms: float = Field(ge=0, description="Average time per document")
    total_vectors_in_qdrant: int = Field(ge=0, description="Total vectors stored")
    model_name: str = Field(description="Current embedding model")
    last_embedding_time: Optional[datetime] = Field(default=None, description="Last embedding time")
    
    class Config:
        extra = "forbid"


class EmbeddingServiceHealth(BaseModel):
    """Health status of embedding service."""
    
    status: str = Field(description="Service status (healthy/degraded/unhealthy)")
    model_loaded: bool = Field(description="Is embedding model loaded?")
    qdrant_connected: bool = Field(description="Is Qdrant reachable?")
    last_check_at: datetime = Field(default_factory=datetime.utcnow, description="Last health check")
    error_rate_percent: float = Field(ge=0, le=100, description="Recent error rate %")
    
    class Config:
        extra = "forbid"