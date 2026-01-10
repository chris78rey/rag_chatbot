# API Application Module

This module contains the FastAPI application logic for the RAF Chatbot, including vector retrieval, context management, and query processing.

## Structure

```
services/api/app/
├── __init__.py              # Module exports
├── qdrant_client.py         # Qdrant vector database client
├── retrieval.py             # Context retrieval logic
├── models.py                # Pydantic data models
└── routes/
    ├── __init__.py          # Routes initialization
    └── query.py             # Query endpoint implementation
```

## Components

### 1. Qdrant Client (`qdrant_client.py`)

Low-level interface to Qdrant vector database.

**Functions:**
- `get_client()` — Get singleton QdrantClient instance
- `ensure_collection(name, dim)` — Create collection if not exists
- `upsert_chunks(collection, chunks, vectors)` — Insert/update vectors with metadata
- `search(collection, vector, top_k)` — Search similar vectors
- `delete_collection(name)` — Delete collection for reindexing

**Usage:**
```python
from app.qdrant_client import ensure_collection, search

# Create collection
ensure_collection("my_rag_collection", vector_dim=1536)

# Search for similar vectors
results = search("my_rag_collection", query_vector, top_k=5)
```

### 2. Retrieval Module (`retrieval.py`)

High-level context retrieval for RAG queries.

**Functions:**
- `get_embedding(text, model_name)` — Generate embedding for text (async)
- `retrieve_context(rag_id, question, top_k, score_threshold)` — Retrieve relevant chunks (async)

**Usage:**
```python
from app.retrieval import retrieve_context
import asyncio

async def main():
    chunks = await retrieve_context(
        rag_id="policies",
        question="How many vacation days?",
        top_k=5
    )
    for chunk in chunks:
        print(f"Score: {chunk['score']}, Text: {chunk['text'][:50]}...")

asyncio.run(main())
```

### 3. Data Models (`models.py`)

Pydantic models for request/response validation and serialization.

**Models:**
- `ContextChunk` — Retrieved chunk from Qdrant
  - `id` (str) — Unique point ID
  - `source` (str) — File path
  - `text` (str) — Chunk content
  - `score` (float) — Similarity score (0-1)

- `QueryRequest` — User query input
  - `rag_id` (str) — RAG identifier
  - `question` (str) — User question
  - `top_k` (int, optional) — Number of results (default: 5)
  - `session_id` (str, optional) — Session tracking
  - `score_threshold` (float, optional) — Minimum score

- `QueryResponse` — Query response output
  - `rag_id` (str) — RAG queried
  - `answer` (str) — Generated answer
  - `context_chunks` (List[ContextChunk]) — Retrieved chunks
  - `latency_ms` (int) — Processing time
  - `cache_hit` (bool) — From cache?
  - `session_id` (str) — Session ID
  - `timestamp` (datetime) — Response time

### 4. Query Route (`routes/query.py`)

FastAPI endpoint for RAG queries.

**Endpoint:**
- `POST /query` — Process RAG query
  - Input: `QueryRequest`
  - Output: `QueryResponse`
  - Returns: 200 OK with response, 422 validation error, 500 server error

**Features:**
- Automatic request validation
- Async context retrieval
- Latency measurement
- Session ID generation
- Error handling with HTTP exceptions

## Configuration

### Environment Variables

```bash
QDRANT_URL="http://localhost:6333"      # Qdrant server URL
QDRANT_API_KEY=""                       # Optional API key
EMBEDDING_MODEL="text-embedding-ada-002" # Embedding model name
```

### RAG Configuration (YAML)

```yaml
retrieval:
  top_k: 5
  score_threshold: 0.7
  
collection:
  name: "my_rag_collection"
  
embeddings:
  dimension: 1536
  normalize: true
  model_name: "text-embedding-ada-002"
```

## Collection Naming Convention

- Pattern: `{rag_id}_collection`
- Example: `policies_collection`, `handbook_collection`
- Uniqueness: One collection per RAG for independent management

## Payload Structure

Each Qdrant point contains:

```json
{
  "source_path": "docs/policy.pdf",
  "page": 0,
  "chunk_index": 12,
  "text": "Chunk content here..."
}
```

## Integration Points

### Inputs
- **SP5 (Config Loader)** → RAGConfig with retrieval settings
- **SP6 (Embedding Service)** → Indexed vectors in Qdrant
- **User Input** → QueryRequest via HTTP

### Outputs
- **SP8 (LLM Integration)** ← Context chunks for prompting
- **Cache Layer** ← Query results for caching
- **Monitoring** ← Latency and performance metrics

## Testing

### Run All Tests
```bash
pytest tests/test_retrieval.py -v
```

### Run Specific Tests
```bash
pytest tests/test_retrieval.py::TestQdrantClient -v
pytest tests/test_retrieval.py::TestRetrieval -v
pytest tests/test_retrieval.py::TestIntegration -v
```

### Seed Demo Data
```bash
python scripts/seed_demo_data.py
```

### Test Query Endpoint
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo",
    "question": "What is FastAPI?",
    "top_k": 5
  }'
```

## Performance Considerations

1. **Batch Operations**: Vector upserting supports batches for efficiency
2. **Score Threshold**: Filter results by similarity score to reduce noise
3. **Top-K Limiting**: Adjust top_k based on context window size
4. **Normalization**: L2 normalization improves cosine similarity accuracy
5. **Vector Dimension**: Must match embedding model (default: 1536)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Collection not found | Qdrant returned 404 | Seed demo data or ingest documents |
| Connection refused | Qdrant not running | `docker compose up -d qdrant` |
| Dimension mismatch | Vector size ≠ collection size | Verify embedding dimension in config |
| Empty results | No similar chunks | Adjust score threshold or question |
| Validation error | Invalid request model | Check required fields (rag_id, question) |

## Next Steps

- **SP8**: Integrate with LLM (OpenRouter) for response generation
- **Cache**: Add Redis caching for retrieval results
- **Monitoring**: Track latency, costs, and usage metrics
- **Real Embeddings**: Replace dummy embeddings with actual API calls

## Dependencies

```
fastapi>=0.100.0
pydantic>=2.0.0
qdrant-client>=2.0.0
python>=3.10
```

Install with:
```bash
pip install -r services/api/requirements.txt
```

## Documentation

- [Qdrant Integration](../../docs/qdrant.md) — Vector database details
- [Configuration Guide](../../docs/configuration.md) — RAG config reference
- [API Documentation](../../docs/architecture.md) — System architecture

---

**Status**: ✅ Subproject 7 Complete  
**Last Updated**: 2025-01-10  
**Next**: Subproject 8 (LLM Integration)