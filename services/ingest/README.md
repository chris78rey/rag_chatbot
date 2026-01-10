# 📋 RAF Chatbot — Ingest Service

## Overview

The Ingest Service is responsible for processing and indexing documents into the RAG system.

Documents flow through:
1. **CLI** — User submits documents via command line
2. **Queue** — Redis-based job queue (non-blocking)
3. **Worker** — Async worker processes documents
4. **Qdrant** — Vector database stores embeddings

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  User: Copy file to data/sources/<rag_id>/incoming  │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  CLI (services/ingest/cli.py)                       │
│  - Validates file                                   │
│  - Creates job                                      │
│  - Submits to Redis queue                           │
│  - Returns job_id                                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Redis Queue (rag:ingest:queue)                     │
│  - Stores job messages (JSON)                       │
│  - Persists state for reliability                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Worker (services/ingest/worker.py)                 │
│  - Polls Redis queue                               │
│  - Loads document (PDF/TXT/MD/DOCX)                 │
│  - Splits into chunks                              │
│  - Generates embeddings                            │
│  - Upserts to Qdrant                               │
│  - Updates job status                              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  File Movement & Status                             │
│  - Success: processed/                              │
│  - Failure: failed/                                 │
│  - Metadata: .meta.json                             │
└─────────────────────────────────────────────────────┘
```

---

## Components

### 1. CLI (cli.py)
Entry point for document ingestion.

**Responsibilities:**
- Parse command line arguments
- Validate file paths and RAG IDs
- Create job messages
- Push to Redis queue
- Report job status to user

**Commands:**
- `ingest submit` — Submit documents for processing
- `ingest status` — Check job status
- `ingest reindex` — Reindex entire RAG

See: `services/ingest/cli.md`

### 2. Worker (worker.py)
Background service that processes documents.

**Responsibilities:**
- Poll Redis queue for jobs
- Load and parse documents
- Split documents into chunks
- Generate embeddings
- Upsert to Qdrant
- Move files (incoming → processed/failed)
- Update job status
- Handle errors and retries

**Runs as:** Docker service `ingest-worker`

See: `services/ingest/worker.py`

### 3. Queue Contract (queue_contract.md)
Definition of Redis queue format and job lifecycle.

**Defines:**
- Queue key naming
- Job message structure (JSON)
- Job states and transitions
- Error handling

See: `services/ingest/queue_contract.md`

### 4. App (app.py)
Shared utilities for ingest service.

**Provides:**
- Document loaders (PDF, TXT, MD, DOCX)
- Text splitters (chunking)
- Embedding generators (via LangChain)
- File operations (move, delete, archive)
- Logging and error handling

See: `services/ingest/app.py`

---

## Configuration

Ingest behavior is configured in two places:

### 1. Client Configuration (`configs/client/client.yaml`)
Global defaults:
- `paths.sources_root` — Root directory for all sources
- `paths.rags_config_dir` — Where RAG configs are loaded from

### 2. RAG Configuration (`configs/rags/<rag_id>.yaml`)
Per-RAG settings:
- `sources.directory` — Subdirectory for this RAG
- `sources.allowed_extensions` — File types to accept
- `sources.max_file_size_mb` — Maximum file size
- `sources.auto_reload` — Auto-reload on file changes
- `chunking.splitter` — Splitting strategy
- `chunking.chunk_size` — Characters per chunk
- `chunking.chunk_overlap` — Overlap between chunks
- `embeddings.model_name` — Model for embeddings
- `embeddings.dimension` — Vector dimension

---

## Workflow Example

### Setup
```bash
# 1. Create RAG source directory
mkdir -p data/sources/policies_rag/{incoming,processed,failed}

# 2. Copy documents
cp my_policy.pdf data/sources/policies_rag/incoming/
cp handbook.pdf data/sources/policies_rag/incoming/
```

### Submission
```bash
# 3. Submit for ingestion
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming

# Returns: job_id = "rag-policies_rag-1234567890"
```

### Processing
```bash
# Worker automatically processes:
# - Reads my_policy.pdf
# - Splits into chunks
# - Generates embeddings
# - Uploads to Qdrant
# - Moves to processed/
```

### Monitoring
```bash
# 4. Check status
python -m services.ingest.cli ingest status --job rag-policies_rag-1234567890

# Returns: {"status": "done", "chunks": 42, "embeddings": 42}
```

### Query
```bash
# 5. Query is now available
curl http://localhost:8000/api/policies_rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our PTO policy?"}'
```

---

## File Organization

### Directory Structure
```
services/ingest/
├── README.md                (this file)
├── cli.md                   (CLI documentation)
├── queue_contract.md        (Queue format specification)
├── requirements.txt         (Python dependencies)
├── __init__.py              (Package marker)
├── app.py                   (Shared utilities)
├── cli.py                   (CLI implementation)
└── worker.py                (Worker implementation)
```

### Data Structure
```
data/sources/
├── policies_rag/
│   ├── incoming/            (files to process)
│   ├── processed/           (successfully processed)
│   └── failed/              (failed attempts)
└── faq_rag/
    ├── incoming/
    ├── processed/
    └── failed/
```

---

## Key Concepts

### Job ID Format
```
rag-<rag_id>-<timestamp>-<random>

Example: rag-policies_rag-1704882600-a7b2c3d4
```

- `rag-` — Prefix
- `<rag_id>` — RAG identifier
- `<timestamp>` — Unix timestamp (seconds)
- `<random>` — Random 8-character string

### Job States
```
submitted → queued → processing → done/failed
```

- **submitted** — Job created by CLI
- **queued** — Waiting in Redis queue
- **processing** — Worker is processing
- **done** — Successfully completed
- **failed** — Failed after max retries

### File Transitions
```
incoming/ → processing (in-memory) → processed/ or failed/
```

- Worker reads from `incoming/`
- Processes in memory
- Moves to `processed/` on success
- Moves to `failed/` on error

---

## Error Handling

### Recoverable Errors
Examples: Network timeout, temporary Qdrant unavailable

**Behavior:**
- Retry up to 3 times
- Exponential backoff (1s, 2s, 4s)
- Error logged to worker logs

### Non-Recoverable Errors
Examples: Invalid PDF, unsupported file type, corrupted file

**Behavior:**
- File moved to `failed/`
- Error details written to `.error.json`
- Job marked as failed
- Does NOT retry

### Error Log Format
```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "filename": "my_policy.pdf",
  "error": "PDF parsing failed: invalid header",
  "error_type": "ParseError",
  "retry_count": 3,
  "timestamp": "2025-01-10T20:15:30Z",
  "suggestions": [
    "Verify PDF is not corrupted",
    "Try re-exporting PDF from source",
    "Check file permissions"
  ]
}
```

---

## Performance Considerations

### Concurrency
- CLI is synchronous (immediate return)
- Worker is async (multiple jobs simultaneously)
- Queue-based design allows horizontal scaling

### Memory Usage
- Large documents (>50MB) may exhaust memory
- Configure `sources.max_file_size_mb` appropriately
- Monitor worker memory in Docker stats

### Throughput
- Single worker can process ~5-10 docs/minute (depends on size and complexity)
- Add more workers (scale up) for higher throughput
- Queue provides backpressure (jobs wait if worker busy)

### Latency
- CLI submission: <100ms
- Queue wait time: depends on queue length
- Processing: 10s-5min per document (varies)
- Total: typically 1-10 minutes for medium docs

---

## Monitoring & Logging

### CLI Logs
```bash
python -m services.ingest.cli ingest submit ...
# Output: Job submitted: rag-policies_rag-1704882600-a7b2c3d4
#         Check status: ingest status --job <job_id>
```

### Worker Logs
```bash
docker logs raf_chatbot-ingest-worker-1
# Shows:
# - Jobs polled
# - Processing progress
# - Errors and retries
# - File movements
```

### Status Tracking
```bash
python -m services.ingest.cli ingest status --job <job_id>
# Output: 
# Status: done
# Chunks: 42
# Embeddings: 42
# Duration: 3.2 seconds
```

---

## Limitations & Future Improvements

### Current Limitations
- No OCR for scanned PDFs (MVP requirement: clear, born-digital PDFs)
- Single-threaded worker (can add threading)
- No resume on worker restart (jobs re-queued)
- No UI for monitoring

### Planned Improvements
- OCR support for scanned documents
- Multi-threaded worker
- Job persistence across restarts
- Web UI for monitoring
- Batch ingestion with progress bars
- Document versioning (update existing docs)

---

## Dependencies

### Python Packages (see requirements.txt)
- `fastapi` — API framework
- `pydantic` — Data validation
- `redis` — Queue broker
- `qdrant-client` — Vector DB client
- `langchain` — Loaders and splitters
- `pypdf` — PDF parsing
- `python-docx` — DOCX parsing

### External Services
- **Redis** — Job queue (docker service: `redis`)
- **Qdrant** — Vector database (docker service: `qdrant`)

### Docker Services
- `ingest-worker` — Worker container (runs continuously)
- See `docker-compose.yml` for configuration

---

## Getting Started

### 1. Review Architecture
Read this file and understand the flow.

### 2. Review CLI Documentation
See: `services/ingest/cli.md`

### 3. Review Queue Contract
Understand message format: `services/ingest/queue_contract.md`

### 4. Review Source Organization
See: `data/sources/README.md`

### 5. Start Services
```bash
make docker-up
```

### 6. Submit Test Document
```bash
echo "This is a test document" > data/sources/example_rag/incoming/test.txt
python -m services.ingest.cli ingest submit --rag example_rag --path data/sources/example_rag/incoming
```

### 7. Check Status
```bash
python -m services.ingest.cli ingest status --job <job_id>
```

---

## Troubleshooting

### "Command not found"
```bash
# Ensure you're in project root
cd G:\zed_projects\raf_chatbot

# Run with python module syntax
python -m services.ingest.cli ingest submit --rag example_rag --path data/sources/example_rag/incoming
```

### "Connection refused" (Redis)
```bash
# Ensure Redis is running
docker ps | grep redis

# If not running:
make docker-up
```

### "No such file or directory"
```bash
# Create source directories first
mkdir -p data/sources/example_rag/{incoming,processed,failed}

# Copy a test file
cp some_file.pdf data/sources/example_rag/incoming/
```

### "Job stuck in processing"
```bash
# Check worker logs
docker logs raf_chatbot-ingest-worker-1

# Worker may have crashed
# Check queue status
python -m services.ingest.cli queue status

# Restart worker
make docker-restart-ingest
```

---

## Questions?

Refer to:
- CLI usage: `services/ingest/cli.md`
- Queue format: `services/ingest/queue_contract.md`
- Source organization: `data/sources/README.md`
- Configuration: `docs/configuration.md`
- Docker setup: `deploy/compose/docker-compose.yml`
```

Now let me create the CLI documentation: