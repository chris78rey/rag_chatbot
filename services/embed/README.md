# Embedding Service — RAF Chatbot

## Overview

The Embedding Service generates vector embeddings for document chunks and stores them in Qdrant vector database. This service bridges the document ingest pipeline (SP4) with vector retrieval (SP7).

**Key Responsibilities**:
- ✅ Load embedding models from Hugging Face
- ✅ Generate embeddings for text chunks
- ✅ Batch processing for efficiency
- ✅ Cache loaded models to save memory
- ✅ Store vectors in Qdrant with metadata
- ✅ Error handling and retry logic
- ✅ Service health monitoring

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────┐
│         Embedding Service (SP6)                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  EmbeddingService (Orchestrator)         │  │
│  │  - Manages end-to-end workflow           │  │
│  │  - Coordinates components                │  │
│  └────────┬─────────────────────────────────┘  │
│           │                                     │
│  ┌────────┴──────────┬──────────────┬──────────┐
│  │                   │              │          │
│  ▼                   ▼              ▼          ▼
│ ModelManager   EmbeddingGenerator  QdrantVectorStore
│ - Load models  - Batch embedding   - Collection mgmt
│ - Cache mgmt   - L2 normalize      - Vector storage
│ - Unload       - Error handling    - Health check
│
└─────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   Hugging Face          Qdrant DB
   (Models)              (Vectors)
```

### Data Flow

```
Documents (from SP4)
        │
        ▼
┌───────────────────┐
│ EmbeddingService  │
├───────────────────┤
│ 1. Load model     │──→ ModelManager ──→ Hugging Face
│ 2. Batch chunks   │
│ 3. Generate vecs  │
│ 4. Normalize      │
│ 5. Store vectors  │──→ QdrantVectorStore ──→ Qdrant
└───────────────────┘
        │
        ▼
Embedding Response
(vectors + errors)
```

---

## Core Classes

### 1. ModelManager

**Purpose**: Load and cache embedding models from Hugging Face.

**Key Methods**:
```python
load_model(model_name: str) -> Tuple[ModelInfo, model]
    Load a model, with caching and cache eviction

unload_model(model_name: str) -> bool
    Unload a model from memory

list_loaded_models() -> List[ModelInfo]
    Get all currently loaded models

get_model_info(model_name: str) -> Optional[ModelInfo]
    Get info about a specific model
```

**Features**:
- Lazy loading (load only when needed)
- Configurable cache size (default: 3 models)
- LRU eviction when cache is full
- Device selection (cpu/cuda/mps)

**Example**:
```python
manager = ModelManager(max_models=2, device="cpu")

# First load
info, model = manager.load_model("sentence-transformers/all-MiniLM-L6-v2")
print(f"Dimension: {info.dimension}")  # 384

# Already loaded
info2, model2 = manager.load_model("sentence-transformers/all-MiniLM-L6-v2")
# Returns cached model (no reload)
```

---

### 2. EmbeddingGenerator

**Purpose**: Generate embeddings for document chunks.

**Key Methods**:
```python
embed_documents(documents: List[Document], rag_config: RagConfig) 
    -> EmbeddingResponse
    Generate embeddings for a list of documents
```

**Features**:
- Batch processing (configurable batch size)
- L2 normalization (optional)
- Error handling per chunk
- Deterministic processing
- Performance tracking

**Example**:
```python
from services.embed import EmbeddingGenerator, Document
from services.api.config import ConfigLoader

# Load config
rag_config = ConfigLoader.load_rag_config("configs/rags/policies.yaml")

# Create generator
manager = ModelManager(max_models=2)
generator = EmbeddingGenerator(manager)

# Create documents
docs = [
    Document(
        doc_id="doc1",
        chunk_id="doc1:0",
        content="This is a document chunk to embed.",
        metadata={"file": "policy.pdf"}
    ),
    Document(
        doc_id="doc2",
        chunk_id="doc2:0",
        content="Another document chunk.",
        metadata={"file": "guide.pdf"}
    ),
]

# Generate embeddings
response = generator.embed_documents(docs, rag_config)

print(f"Vectors: {len(response.vectors)}")
print(f"Errors: {len(response.failed_count)}")
print(f"Time: {response.processing_time_seconds}s")
```

---

### 3. QdrantVectorStore

**Purpose**: Manage vector storage in Qdrant database.

**Key Methods**:
```python
create_collection(collection_name: str, vector_size: int) -> bool
    Create a Qdrant collection

upsert_vectors(collection_name: str, vectors: List[EmbeddingVector],
               chunks_metadata: Dict) -> int
    Store vectors in Qdrant

get_collection_info(collection_name: str) -> Optional[QdrantCollectionInfo]
    Get collection statistics

delete_collection(collection_name: str) -> bool
    Delete a collection
```

**Features**:
- Collection lifecycle management
- Batch upserting vectors
- Metadata storage with vectors
- Health monitoring
- Error handling

**Example**:
```python
from services.embed import QdrantVectorStore

store = QdrantVectorStore(
    qdrant_url="http://qdrant:6333",
    api_key=None
)

# Create collection
created = store.create_collection(
    collection_name="policies_docs",
    vector_size=384,
)

if created:
    # Upsert vectors
    num_stored = store.upsert_vectors(
        collection_name="policies_docs",
        vectors=response.vectors,
        chunks_metadata=metadata_dict,
    )
    print(f"Stored {num_stored} vectors")

# Get info
info = store.get_collection_info("policies_docs")
print(f"Points in collection: {info.points_count}")
```

---

### 4. EmbeddingService

**Purpose**: Orchestrate embedding generation and storage end-to-end.

**Key Methods**:
```python
process_rag(rag_id: str, rag_config: RagConfig, 
           documents: List[Document]) -> Tuple[int, int]
    Process all documents for a RAG
    Returns: (vectors_stored, error_count)

health_check() -> Dict[str, bool]
    Check service health
```

**Example**:
```python
from services.embed import EmbeddingService, Document
from services.api.config import ClientConfig, ConfigLoader

# Load configs
client_config = ClientConfig(...)  # or load from YAML
rag_config = ConfigLoader.load_rag_config("configs/rags/policies.yaml")

# Create service
service = EmbeddingService(
    qdrant_url=client_config.qdrant.url,
    qdrant_api_key=client_config.qdrant.api_key,
    max_cached_models=2,
    device="cpu",
)

# Create documents from chunks (from SP4)
documents = [
    Document(
        doc_id=chunk.doc_id,
        chunk_id=chunk.chunk_id,
        content=chunk.content,
        metadata={"file_path": chunk.file_path, ...}
    )
    for chunk in chunks
]

# Process RAG
vectors_stored, errors = service.process_rag(
    rag_id="policies",
    rag_config=rag_config,
    documents=documents,
)

print(f"Stored {vectors_stored} vectors, {errors} errors")

# Check health
health = service.health_check()
print(f"Service healthy: {all(health.values())}")
```

---

## Integration with Other Subprojects

### Depends On (Inputs)
- **SP3 (YAML Config)**: `RAGConfig` for embedding settings
  - `embeddings.model_name` — Which model to use
  - `embeddings.dimension` — Expected vector dimension
  - `embeddings.batch_size` — Batch processing size
  - `embeddings.normalize` — L2 normalization
  - `collection.name` — Qdrant collection to create

- **SP4 (Ingest Pipeline)**: Document chunks
  - `DocumentChunk` with text content
  - Metadata (file path, char positions)

- **SP2 (Docker Services)**: Qdrant and optional GPU
  - Qdrant API endpoint
  - CUDA/GPU if available

### Feeds Into (Outputs)
- **SP7 (Vector Retrieval)**: Embeddings stored in Qdrant
  - Vector database ready for similarity search
  - Metadata for ranking and filtering

- **SP8 (LLM Integration)**: Retrieved chunks
  - Top-K chunks sent to LLM for context

---

## Configuration

### From RAG YAML

```yaml
embeddings:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32
  normalize: true

collection:
  name: "policies_docs"
  recreation_policy: "skip"  # or "recreate"
```

### From Client Config

```yaml
qdrant:
  url: "http://qdrant:6333"
  api_key: null
  timeout_s: 30
```

---

## Error Handling

### Common Errors

**1. Model Not Found**
```
RuntimeError: Cannot load model 'invalid-model': Model not found on Hugging Face
```
**Fix**: Verify model name in RAG config (e.g., `sentence-transformers/all-MiniLM-L6-v2`)

**2. Out of Memory**
```
RuntimeError: CUDA out of memory. Tried to allocate 512.00 MiB
```
**Fix**: Reduce `batch_size` in RAG config or use CPU instead of GPU

**3. Qdrant Connection Failed**
```
RuntimeError: Failed to connect to Qdrant at http://qdrant:6333
```
**Fix**: Verify Qdrant is running (`docker-compose up qdrant`) and URL is correct

**4. Dimension Mismatch**
```
ValueError: Vector dimension 768 does not match collection dimension 384
```
**Fix**: Ensure `embeddings.dimension` matches actual model output dimension

### Error Recovery

The service implements automatic error handling:

```python
# Per-chunk error handling
try:
    vector = generator.embed_documents([doc], rag_config)
except Exception as e:
    # Log error and continue with next chunk
    errors.append(EmbeddingError(
        chunk_id=doc.doc_id,
        error_message=str(e),
        error_type=type(e).__name__,
    ))
    continue
```

---

## Performance Optimization

### 1. Batch Size Tuning

**Larger batches** (64+): Faster, uses more memory
**Smaller batches** (8-16): Slower, uses less memory

Recommended: Start with `batch_size: 32` from config

### 2. Model Caching

Keep frequently used models in memory:
```python
service = EmbeddingService(
    qdrant_url="http://qdrant:6333",
    max_cached_models=3,  # Keep 3 models
)
```

### 3. Vector Normalization

L2 normalization is required for cosine similarity:
```yaml
embeddings:
  normalize: true  # Always true for retrieval
```

### 4. Device Selection

Use GPU if available:
```python
service = EmbeddingService(
    qdrant_url="http://qdrant:6333",
    device="cuda",  # or "cpu"
)
```

---

## Testing

### Unit Tests

Create `tests/test_embedding.py`:

```python
import pytest
from services.embed import EmbeddingService, Document
from services.api.config import RagConfig

def test_model_manager_load():
    from services.embed import ModelManager
    
    manager = ModelManager(max_models=2)
    info, model = manager.load_model("sentence-transformers/all-MiniLM-L6-v2")
    
    assert info.dimension == 384
    assert info.is_loaded

def test_embedding_generation():
    service = EmbeddingService(qdrant_url="http://qdrant:6333")
    
    docs = [Document(...), Document(...)]
    response = service.embedding_generator.embed_documents(docs, rag_config)
    
    assert len(response.vectors) > 0
    assert response.total_processed == 2

def test_vector_storage():
    store = QdrantVectorStore("http://qdrant:6333")
    
    created = store.create_collection("test_collection", 384)
    assert created
    
    num_stored = store.upsert_vectors("test_collection", vectors, metadata)
    assert num_stored > 0
```

---

## Monitoring

### Health Checks

```python
health = service.health_check()
# {
#     "service": True,
#     "models_loaded": True,
#     "qdrant_url": True,
# }
```

### Statistics

Track embedding statistics:
```python
stats = {
    "total_vectors_generated": 1500,
    "total_errors": 12,
    "avg_time_per_document_ms": 45.2,
    "models_in_cache": 2,
}
```

---

## Dependencies

### Required Python Packages

```
sentence-transformers>=2.2.0  # Embedding models
qdrant-client>=2.0.0          # Qdrant client
pydantic>=2.0                 # Data validation
pyyaml>=6.0                   # Config loading
numpy>=1.20                   # Vector operations
```

### Optional Dependencies

```
torch>=2.0          # For GPU support
transformers>=4.30  # For transformer models
```

---

## Future Enhancements

### SP6+ Planned Features

1. **Async Embedding Generation**
   - Non-blocking API for large batches
   - Queue-based processing

2. **Advanced Caching**
   - Redis-based embedding cache
   - Skip re-embedding identical chunks

3. **Model Optimization**
   - ONNX model conversion
   - Model quantization for faster inference

4. **Multi-GPU Support**
   - Distributed embedding across GPUs
   - Model parallelism for large models

5. **Reranking Integration**
   - Cross-encoder reranking
   - BM25 hybrid retrieval

---

## Troubleshooting

### Issue: Slow Embedding Generation

**Symptoms**: Takes >1 minute to embed 100 documents

**Solutions**:
1. Increase `batch_size` in config (use 64 instead of 32)
2. Switch to GPU if available (`device="cuda"`)
3. Use lighter model (e.g., `all-MiniLM-L6-v2` instead of `all-mpnet-base-v2`)

### Issue: Memory Errors

**Symptoms**: `RuntimeError: CUDA out of memory`

**Solutions**:
1. Reduce `batch_size` to 8-16
2. Switch to CPU mode
3. Reduce `max_cached_models` from 3 to 1

### Issue: Qdrant Connection Fails

**Symptoms**: `RuntimeError: Connection refused`

**Solutions**:
1. Check Qdrant is running: `docker-compose ps`
2. Check URL is correct in config
3. Verify network connectivity: `curl http://qdrant:6333/health`

---

## References

- **Models**: https://www.sbert.net/docs/pretrained_models.html
- **Qdrant**: https://qdrant.tech/documentation/
- **Sentence Transformers**: https://www.sbert.net/
- **Vector Search**: https://www.pinecone.io/learn/vector-similarity/

---

**Last Updated**: 2024
**Status**: ✅ Implementation Ready
**Next**: SP7 — Vector Retrieval & Ranking