"""
RAF Chatbot — Embedding Service

Main service for generating embeddings and storing vectors in Qdrant.
Handles model loading, caching, batch processing, and vector storage.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import hashlib
from datetime import datetime
import numpy as np

from services.api.config import RagConfig
from .models import (
    Document,
    EmbeddingVector,
    EmbeddingResponse,
    EmbeddingError,
    VectorPayload,
    VectorPointCreate,
    ModelInfo,
    ModelCache,
    QdrantCollectionInfo,
)


logger = logging.getLogger(__name__)


class ModelManager:
    """Manages embedding model lifecycle (loading, caching, unloading)."""
    
    def __init__(self, max_models: int = 3, device: str = "cpu"):
        """
        Initialize model manager.
        
        Args:
            max_models: Maximum number of models to keep in memory
            device: Device to load models on (cpu/cuda/mps)
        """
        self.max_models = max_models
        self.device = device
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.model_cache: Dict[str, any] = {}  # Actual loaded models
        
    def load_model(self, model_name: str) -> Tuple[ModelInfo, any]:
        """
        Load embedding model from Hugging Face.
        
        Args:
            model_name: Hugging Face model identifier (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
            
        Returns:
            Tuple of (ModelInfo, loaded_model)
            
        Raises:
            RuntimeError: If model loading fails
            ValueError: If model_name is invalid
        """
        # Check if already loaded
        if model_name in self.loaded_models:
            logger.info(f"Model {model_name} already loaded")
            return self.loaded_models[model_name], self.model_cache[model_name]
        
        # Check cache size
        if len(self.loaded_models) >= self.max_models:
            logger.warning(f"Model cache full ({self.max_models}), unloading oldest")
            self._unload_oldest_model()
        
        try:
            logger.info(f"Loading model: {model_name}")
            
            # Stub: In production, would load actual model
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer(model_name, device=self.device)
            
            model_info = ModelInfo(
                model_name=model_name,
                model_id=hashlib.md5(model_name.encode()).hexdigest(),
                dimension=384 if "MiniLM" in model_name else 768,
                max_seq_length=256 if "MiniLM" in model_name else 512,
                is_loaded=True,
                loaded_at=datetime.utcnow(),
            )
            
            self.loaded_models[model_name] = model_info
            self.model_cache[model_name] = None  # Placeholder for actual model
            
            logger.info(f"Model loaded: {model_name} (dim={model_info.dimension})")
            return model_info, None
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise RuntimeError(f"Cannot load model {model_name}: {str(e)}")
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Model to unload
            
        Returns:
            True if unloaded, False if not loaded
        """
        if model_name not in self.loaded_models:
            return False
        
        del self.loaded_models[model_name]
        if model_name in self.model_cache:
            del self.model_cache[model_name]
        
        logger.info(f"Model unloaded: {model_name}")
        return True
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a loaded model."""
        return self.loaded_models.get(model_name)
    
    def list_loaded_models(self) -> List[ModelInfo]:
        """List all currently loaded models."""
        return list(self.loaded_models.values())
    
    def _unload_oldest_model(self) -> None:
        """Unload the model that was used least recently."""
        if not self.loaded_models:
            return
        
        # Unload first model (FIFO)
        oldest_name = next(iter(self.loaded_models.keys()))
        self.unload_model(oldest_name)


class EmbeddingGenerator:
    """Generates embeddings for document chunks."""
    
    def __init__(self, model_manager: ModelManager):
        """
        Initialize embedding generator.
        
        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        
    def embed_documents(
        self,
        documents: List[Document],
        rag_config: RagConfig,
    ) -> EmbeddingResponse:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents: Documents to embed
            rag_config: RAG configuration (for model_name, dimension, batch_size)
            
        Returns:
            EmbeddingResponse with vectors or errors
        """
        model_name = rag_config.embeddings.model_name
        batch_size = rag_config.embeddings.batch_size
        normalize = rag_config.embeddings.normalize
        dimension = rag_config.embeddings.dimension
        
        # Load model
        try:
            model_info, model = self.model_manager.load_model(model_name)
        except RuntimeError as e:
            logger.error(f"Cannot load model: {e}")
            return EmbeddingResponse(
                rag_id=rag_config.rag_id,
                vectors=[],
                total_processed=0,
                failed_count=len(documents),
                model_name=model_name,
                dimension=dimension,
                processing_time_seconds=0.0,
            )
        
        vectors = []
        errors = []
        start_time = datetime.utcnow()
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Stub: In production, would call actual embedding model
                # embeddings = model.encode([doc.content for doc in batch], normalize_embeddings=normalize)
                
                for j, doc in enumerate(batch):
                    # Generate dummy embedding (1s)
                    vector = [1.0] * dimension
                    if normalize:
                        # L2 normalize
                        norm = np.sqrt(sum(v**2 for v in vector))
                        vector = [v / norm for v in vector]
                    
                    vectors.append(EmbeddingVector(
                        chunk_id=doc.doc_id,
                        vector=vector,
                        dimension=dimension,
                        model_name=model_name,
                        normalized=normalize,
                    ))
                    
            except Exception as e:
                logger.error(f"Error embedding batch {i//batch_size}: {e}")
                for doc in batch:
                    errors.append(EmbeddingError(
                        chunk_id=doc.doc_id,
                        error_message=str(e),
                        error_type=type(e).__name__,
                    ))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return EmbeddingResponse(
            rag_id=rag_config.rag_id,
            vectors=vectors,
            total_processed=len(documents),
            failed_count=len(errors),
            model_name=model_name,
            dimension=dimension,
            processing_time_seconds=processing_time,
        )


class QdrantVectorStore:
    """Manages vector storage in Qdrant."""
    
    def __init__(self, qdrant_url: str, api_key: Optional[str] = None):
        """
        Initialize Qdrant vector store.
        
        Args:
            qdrant_url: Qdrant API URL
            api_key: Optional API key for authentication
        """
        self.qdrant_url = qdrant_url
        self.api_key = api_key
        # Stub: In production, would create Qdrant client
        # from qdrant_client import QdrantClient
        # self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "cosine",
    ) -> bool:
        """
        Create a collection in Qdrant.
        
        Args:
            collection_name: Name of collection
            vector_size: Dimension of vectors
            distance_metric: Distance metric (cosine, euclidean, dot)
            
        Returns:
            True if created or already exists, False on error
        """
        try:
            # Stub: In production, would create collection
            logger.info(f"Collection {collection_name} created (size={vector_size})")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[EmbeddingVector],
        chunks_metadata: Dict[str, Dict],
    ) -> int:
        """
        Store embedding vectors in Qdrant.
        
        Args:
            collection_name: Target collection
            vectors: Embedding vectors to store
            chunks_metadata: Metadata for each chunk
            
        Returns:
            Number of vectors successfully stored
        """
        try:
            points = []
            for vector in vectors:
                payload = VectorPayload(
                    chunk_id=vector.chunk_id,
                    file_path=chunks_metadata.get(vector.chunk_id, {}).get("file_path", ""),
                    content=chunks_metadata.get(vector.chunk_id, {}).get("content", ""),
                    chunk_number=chunks_metadata.get(vector.chunk_id, {}).get("chunk_number", 0),
                    char_start=chunks_metadata.get(vector.chunk_id, {}).get("char_start", 0),
                    char_end=chunks_metadata.get(vector.chunk_id, {}).get("char_end", 0),
                    metadata=chunks_metadata.get(vector.chunk_id, {}).get("metadata", {}),
                )
                
                point = VectorPointCreate(
                    id=int(hashlib.md5(vector.chunk_id.encode()).hexdigest()[:8], 16),
                    vector=vector.vector,
                    payload=payload.dict(),
                )
                points.append(point)
            
            # Stub: In production, would upsert to Qdrant
            logger.info(f"Upserted {len(points)} vectors to {collection_name}")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            return 0
    
    def get_collection_info(self, collection_name: str) -> Optional[QdrantCollectionInfo]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection info or None if not found
        """
        try:
            # Stub: In production, would fetch from Qdrant
            return QdrantCollectionInfo(
                collection_name=collection_name,
                vector_size=384,
                points_count=0,
                status="green",
            )
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Collection to delete
            
        Returns:
            True if deleted, False on error
        """
        try:
            # Stub: In production, would delete from Qdrant
            logger.info(f"Collection {collection_name} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False


class EmbeddingService:
    """Main embedding service orchestrating all components."""
    
    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: Optional[str] = None,
        max_cached_models: int = 3,
        device: str = "cpu",
    ):
        """
        Initialize embedding service.
        
        Args:
            qdrant_url: Qdrant API URL
            qdrant_api_key: Optional API key
            max_cached_models: Max models to cache
            device: Device for model loading (cpu/cuda/mps)
        """
        self.model_manager = ModelManager(max_models=max_cached_models, device=device)
        self.embedding_generator = EmbeddingGenerator(self.model_manager)
        self.vector_store = QdrantVectorStore(qdrant_url, qdrant_api_key)
        
    def process_rag(
        self,
        rag_id: str,
        rag_config: RagConfig,
        documents: List[Document],
    ) -> Tuple[int, int]:
        """
        Process all documents for a RAG.
        
        Args:
            rag_id: RAG identifier
            rag_config: RAG configuration
            documents: Documents to embed
            
        Returns:
            Tuple of (vectors_stored, errors_count)
        """
        logger.info(f"Processing {len(documents)} documents for RAG {rag_id}")
        
        # Create Qdrant collection if needed
        collection_name = rag_config.collection.name
        self.vector_store.create_collection(
            collection_name,
            rag_config.embeddings.dimension,
        )
        
        # Generate embeddings
        response = self.embedding_generator.embed_documents(documents, rag_config)
        
        if not response.vectors:
            logger.warning(f"No vectors generated for {rag_id}")
            return 0, len(documents)
        
        # Prepare metadata
        chunks_metadata = {
            doc.doc_id: {
                "file_path": doc.metadata.get("file_path", ""),
                "content": doc.content[:200],  # First 200 chars
                "chunk_number": doc.metadata.get("chunk_number", 0),
                "char_start": doc.metadata.get("char_start", 0),
                "char_end": doc.metadata.get("char_end", 0),
                "metadata": doc.metadata,
            }
            for doc in documents
        }
        
        # Store in Qdrant
        stored = self.vector_store.upsert_vectors(
            collection_name,
            response.vectors,
            chunks_metadata,
        )
        
        logger.info(f"Processed {rag_id}: {stored} vectors stored, {response.failed_count} errors")
        return stored, response.failed_count
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check service health.
        
        Returns:
            Dict with health status of components
        """
        return {
            "service": True,
            "models_loaded": len(self.model_manager.loaded_models) > 0,
            "qdrant_url": self.vector_store.qdrant_url is not None,
        }