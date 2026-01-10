# 📬 RAF Chatbot — Queue Contract Specification

## Overview

The Queue Contract defines the structure of messages in the Redis ingestion queue.

This ensures consistency between CLI (producer) and Worker (consumer).

---

## Queue Infrastructure

### Queue Location
```
Redis Database: 0 (default)
Queue Key: rag:ingest:queue
```

### Connection Details
From `configs/client/client.yaml`:
```yaml
redis:
  url: "redis://redis:6379/0"
  password: null
  db: 0
```

### Queue Type
- **Type**: Redis List (FIFO)
- **Broker**: Redis (single instance, no clustering)
- **Persistence**: Redis persistence (RDB/AOF)
- **Reliability**: At-least-once delivery

---

## Message Structure

### Job Message Format

Jobs in the queue are JSON objects with the following structure:

```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "source_path": "/app/data/sources/policies_rag/incoming/my_policy.pdf",
  "source_type": "pdf",
  "filename": "my_policy.pdf",
  "submitted_at": "2025-01-10T20:15:30.123456Z",
  "submitted_by": "cli",
  "options": {
    "reindex": false,
    "skip_validation": false,
    "preserve_metadata": true
  },
  "retry_count": 0,
  "max_retries": 3
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | Yes | Unique job identifier (format: `rag-<rag_id>-<timestamp>-<random>`) |
| `rag_id` | string | Yes | RAG identifier from configuration |
| `source_path` | string | Yes | Full absolute path to document file |
| `source_type` | string | Yes | File type: `pdf`, `txt`, `md`, or `docx` |
| `filename` | string | Yes | Original filename (for logging and file movements) |
| `submitted_at` | string | Yes | ISO 8601 timestamp with milliseconds (UTC) |
| `submitted_by` | string | No | Source of submission: `cli`, `api`, `scheduled` (default: `cli`) |
| `options` | object | No | Processing options (see below) |
| `retry_count` | integer | No | Current retry attempt (default: 0) |
| `max_retries` | integer | No | Maximum retry attempts (default: 3) |

### Options Object

```json
{
  "reindex": false,
  "skip_validation": false,
  "preserve_metadata": true
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `reindex` | boolean | false | Clear collection before processing |
| `skip_validation` | boolean | false | Skip file validation (not recommended) |
| `preserve_metadata` | boolean | true | Keep existing metadata when updating |

---

## Job ID Format

```
rag-<rag_id>-<timestamp>-<random>
```

Example: `rag-policies_rag-1704882600-a7b2c3d4`

### Components

- **Prefix**: `rag-` (constant)
- **RAG ID**: From configuration (e.g., `policies_rag`)
- **Timestamp**: Unix timestamp in seconds (e.g., `1704882600`)
- **Random**: 8-character random string (base16, e.g., `a7b2c3d4`)

### Generation (Python)

```python
import time
import secrets

rag_id = "policies_rag"
timestamp = int(time.time())
random_str = secrets.token_hex(4)  # 4 bytes = 8 hex chars
job_id = f"rag-{rag_id}-{timestamp}-{random_str}"
# Result: rag-policies_rag-1704882600-a7b2c3d4
```

---

## Job Status Tracking

### Status Key Format
```
rag:ingest:job:<job_id>
```

Example: `rag:ingest:job:rag-policies_rag-1704882600-a7b2c3d4`

### Status Value (JSON)

```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "filename": "my_policy.pdf",
  "status": "done",
  "submitted_at": "2025-01-10T20:15:30Z",
  "started_at": "2025-01-10T20:15:35Z",
  "completed_at": "2025-01-10T20:16:00Z",
  "duration_seconds": 25,
  "chunks_created": 21,
  "embeddings_generated": 21,
  "tokens_used": 5432,
  "error": null,
  "error_type": null,
  "retry_count": 0
}
```

### Status States

```
submitted
    ↓
queued
    ↓
processing
    ├─→ done (success)
    └─→ failed (after max_retries)
```

#### submitted
- Job created by CLI
- Not yet in queue
- Transitional state (< 1 second)

#### queued
- In Redis queue, waiting for worker
- No processing started

#### processing
- Worker has claimed job
- Document is being processed
- Can transition to `done` or `failed`

#### done
- Processing completed successfully
- File moved to `processed/`
- Metadata saved

#### failed
- Processing failed after max retries
- File moved to `failed/`
- Error details saved

---

## Redis Keys Schema

### Queue
```
rag:ingest:queue          (List, FIFO)
```

Contents: Job messages (JSON strings)

Operations:
- LPUSH: Add job (CLI)
- RPOP: Get job (Worker)
- LLEN: Queue length

### Job Status (Hash)
```
rag:ingest:job:<job_id>   (Hash)
```

Fields: `status`, `submitted_at`, `started_at`, `completed_at`, `chunks_created`, `error`, etc.

Operations:
- HSET: Update job status (Worker)
- HGET: Read job status (CLI)
- HGETALL: Get all status fields
- DEL: Delete after retention period

### Job Expiry
```
rag:ingest:job:<job_id>:ttl
```

TTL: 7 days (604800 seconds) after completion

Allows cleanup of old jobs.

---

## Message Examples

### Example 1: PDF Submission
```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "source_path": "/app/data/sources/policies_rag/incoming/employee_handbook.pdf",
  "source_type": "pdf",
  "filename": "employee_handbook.pdf",
  "submitted_at": "2025-01-10T20:15:30.123456Z",
  "submitted_by": "cli",
  "options": {
    "reindex": false,
    "skip_validation": false,
    "preserve_metadata": true
  },
  "retry_count": 0,
  "max_retries": 3
}
```

### Example 2: Text File with Reindex
```json
{
  "job_id": "rag-faq_rag-1704882601-b8c3d4e5",
  "rag_id": "faq_rag",
  "source_path": "/app/data/sources/faq_rag/incoming/faq_list.txt",
  "source_type": "txt",
  "filename": "faq_list.txt",
  "submitted_at": "2025-01-10T20:15:31.234567Z",
  "submitted_by": "cli",
  "options": {
    "reindex": true,
    "skip_validation": false,
    "preserve_metadata": false
  },
  "retry_count": 0,
  "max_retries": 3
}
```

### Example 3: Retry Attempt
```json
{
  "job_id": "rag-procedures_rag-1704882602-c9d4e5f6",
  "rag_id": "procedures_rag",
  "source_path": "/app/data/sources/procedures_rag/incoming/procedures.docx",
  "source_type": "docx",
  "filename": "procedures.docx",
  "submitted_at": "2025-01-10T20:15:32.345678Z",
  "submitted_by": "cli",
  "options": {
    "reindex": false,
    "skip_validation": false,
    "preserve_metadata": true
  },
  "retry_count": 2,
  "max_retries": 3
}
```

---

## Worker Processing Flow

```
┌─────────────────────────────────────┐
│ 1. Poll Queue (RPOP)                │
│    Get job message from Redis       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 2. Load Job Status                  │
│    Set status: "processing"         │
│    Set started_at: now()            │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 3. Load Document                    │
│    Read from source_path            │
│    Parse based on source_type       │
└────────────┬────────────────────────┘
             │
         ┌───┴─────┐
         │          │
    ┌────▼──┐   ┌──▼────┐
    │Success│   │ Error  │
    └────┬──┘   └──┬─────┘
         │         │
    ┌────▼────┐  ┌─▼──────────────┐
    │ 4.Split │  │ Retry Logic    │
    │ 5.Embed │  │ - Increment    │
    │ 6.Upsert│  │   retry_count  │
    │ 7.Move  │  │ - If < max_ret │
    │   File  │  │   → back queue │
    │ 8.Done  │  │ - Else → failed│
    └────┬────┘  └───────┬────────┘
         │               │
    ┌────▼───────────────▼────┐
    │ 9. Update Status        │
    │    Save metadata        │
    │    Cleanup temp data    │
    └────────────────────────┘
```

---

## Error Handling

### Recoverable Errors

These errors trigger a retry (up to `max_retries`):

- Network timeout (Redis, Qdrant, embedding API)
- Temporary service unavailable (503, 429)
- Disk space issue (may be transient)
- Out of memory (worker may recover)

**Behavior:**
1. Increment `retry_count`
2. If `retry_count < max_retries`, push job back to queue with backoff
3. Else, move to failed state

**Backoff Strategy:**
- 1st retry: 5 seconds delay
- 2nd retry: 10 seconds delay
- 3rd retry: 30 seconds delay

### Non-Recoverable Errors

These errors do NOT retry:

- File not found
- Unsupported file type
- Corrupted file (parse error)
- Invalid RAG ID
- Configuration error

**Behavior:**
1. Set status: `failed`
2. Write error to `failed/<filename>.error.json`
3. Move file to `failed/` directory
4. Log detailed error

### Error Response Format

```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "filename": "my_policy.pdf",
  "status": "failed",
  "submitted_at": "2025-01-10T20:15:30Z",
  "started_at": "2025-01-10T20:15:35Z",
  "failed_at": "2025-01-10T20:15:45Z",
  "error": "PDF header corrupted or invalid",
  "error_type": "ParseError",
  "error_code": "ERR_PDF_INVALID",
  "retry_count": 3,
  "max_retries": 3,
  "suggestions": [
    "Verify PDF is valid using: pdfinfo filename.pdf",
    "Try re-exporting the PDF from original source",
    "Check file permissions (must be readable)",
    "Try with --skip-validation flag (use with caution)"
  ],
  "traceback": "..."
}
```

---

## Concurrency & Thread Safety

### Redis Operations
- RPOP: Atomic, safe for multiple workers
- HSET: Atomic, safe for concurrent updates
- DEL: Atomic cleanup

### Multiple Workers
- Each worker polls independently
- No distributed lock needed (RPOP is atomic)
- Each job processed by single worker only

### No Job Stealing
- Once RPOP'd, job is removed from queue
- No way for another worker to pick it up
- If worker crashes, job is lost (future: job acknowledgment)

---

## Monitoring & Debugging

### Queue Health Check

```
Queue name: rag:ingest:queue
Connection: redis://redis:6379/0
Queue length: (LLEN result)
Processing: (count of active jobs)
Queued: (queue length - processing)
Worker connected: (last heartbeat < 5 seconds ago)
```

### Job Inspection

```bash
# Get queue length
LLEN rag:ingest:queue

# View oldest job in queue
LINDEX rag:ingest:queue -1

# Get job status
HGETALL rag:ingest:job:rag-policies_rag-1704882600-a7b2c3d4

# View all jobs (be careful with large queues)
LRANGE rag:ingest:queue 0 -1
```

### Status Query

```bash
# Get all active jobs
python -m services.ingest.cli queue status

# Get specific job
python -m services.ingest.cli ingest status --job rag-policies_rag-1704882600-a7b2c3d4

# Watch queue
python -m services.ingest.cli queue status --watch
```

---

## Future Enhancements

### Job Acknowledgment
Add job acknowledgment for fault tolerance:
- Worker sends ACK after success
- Job remains in queue until ACK
- Job returns to queue on worker timeout

### Dead Letter Queue
Add separate queue for permanently failed jobs:
```
rag:ingest:queue:dead-letter
```

### Priority Queue
Add priority levels:
```
rag:ingest:queue:high
rag:ingest:queue:normal
rag:ingest:queue:low
```

### Job Grouping
Group jobs by RAG to prevent queue starvation:
```
rag:ingest:queue:policies_rag
rag:ingest:queue:faq_rag
rag:ingest:queue:procedures_rag
```

---

## Implementation Checklist

### CLI (Producer)
- [ ] Parse command line arguments
- [ ] Validate file exists and RAG exists
- [ ] Generate unique job_id
- [ ] Create job message JSON
- [ ] Push to rag:ingest:queue (LPUSH)
- [ ] Create status key with "submitted" state
- [ ] Return job_id to user

### Worker (Consumer)
- [ ] Connect to Redis
- [ ] Poll queue (RPOP from rag:ingest:queue)
- [ ] Load job message
- [ ] Set status to "processing" and started_at
- [ ] Load document from source_path
- [ ] Split into chunks
- [ ] Generate embeddings
- [ ] Upsert to Qdrant
- [ ] Move file to processed/
- [ ] Update status to "done"
- [ ] Set completed_at and metadata
- [ ] Handle errors and retries
- [ ] Move failed files to failed/

### Status Tracking
- [ ] CLI can query job status from Redis
- [ ] Worker updates status in real-time
- [ ] Status includes progress (chunks, embeddings)
- [ ] Error messages stored for debugging

---

## Testing Checklist

- [ ] CLI creates valid JSON messages
- [ ] Worker processes messages from queue
- [ ] Status updates correctly
- [ ] Files move to correct directories
- [ ] Errors are handled and logged
- [ ] Retries work as expected
- [ ] Queue works under load (100+ jobs)
- [ ] Multiple workers don't conflict
- [ ] Redis persistence works (restart recovery)

---

## Summary

This contract ensures:
- **Consistency**: Predictable message format
- **Traceability**: Job IDs and status tracking
- **Reliability**: Error handling and retries
- **Scalability**: Simple FIFO queue supports multiple workers
- **Observability**: Status tracking for monitoring