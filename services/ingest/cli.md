# 📝 RAF Chatbot — Ingest CLI Documentation

## Overview

The Ingest CLI provides command-line tools for managing document ingestion into the RAG system.

Commands are executed via:
```bash
python -m services.ingest.cli <command> <subcommand> [options]
```

---

## Quick Reference

### Submit Documents
```bash
python -m services.ingest.cli ingest submit --rag <rag_id> --path <path>
```

### Check Status
```bash
python -m services.ingest.cli ingest status --job <job_id>
```

### Reindex RAG
```bash
python -m services.ingest.cli ingest reindex --rag <rag_id>
```

### Queue Status
```bash
python -m services.ingest.cli queue status
```

---

## Commands

### 1. ingest submit

Submit documents for ingestion.

**Usage:**
```bash
python -m services.ingest.cli ingest submit --rag <rag_id> --path <path> [options]
```

**Required Arguments:**
- `--rag <rag_id>` — RAG identifier (must match config in configs/rags/<rag_id>.yaml)
- `--path <path>` — Directory containing documents (typically data/sources/<rag_id>/incoming)

**Optional Arguments:**
- `--reindex` — Force reindex (clear existing collection first)
- `--skip-validation` — Skip file validation (not recommended)
- `--dry-run` — Show what would be submitted without actually submitting

**Examples:**

Submit all documents in incoming folder:
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming
```

Reindex (clear and rebuild collection):
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --reindex
```

Dry run (preview without submitting):
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --dry-run
```

**Output:**
```
✓ Validated 3 documents
  - my_policy.pdf (2.3 MB) ✓
  - handbook.pdf (1.8 MB) ✓
  - faq.txt (0.2 MB) ✓

Submitted job: rag-policies_rag-1704882600-a7b2c3d4
Track status: ingest status --job rag-policies_rag-1704882600-a7b2c3d4
```

**Return Code:**
- `0` — Success
- `1` — Validation error
- `2` — Submission error
- `3` — Configuration error

---

### 2. ingest status

Check the status of an ingestion job.

**Usage:**
```bash
python -m services.ingest.cli ingest status --job <job_id> [options]
```

**Required Arguments:**
- `--job <job_id>` — Job identifier (returned by `ingest submit`)

**Optional Arguments:**
- `--follow` — Watch status in real-time (updates every 2 seconds)
- `--verbose` — Show detailed information (timings, chunk details)
- `--output json` — Output as JSON (for scripting)

**Examples:**

Check status once:
```bash
python -m services.ingest.cli ingest status --job rag-policies_rag-1704882600-a7b2c3d4
```

Watch in real-time:
```bash
python -m services.ingest.cli ingest status \
  --job rag-policies_rag-1704882600-a7b2c3d4 \
  --follow
```

Verbose output:
```bash
python -m services.ingest.cli ingest status \
  --job rag-policies_rag-1704882600-a7b2c3d4 \
  --verbose
```

JSON output (for scripting):
```bash
python -m services.ingest.cli ingest status \
  --job rag-policies_rag-1704882600-a7b2c3d4 \
  --output json
```

**Output (Normal):**
```
Job: rag-policies_rag-1704882600-a7b2c3d4
Status: processing
Progress: 2/3 files
  - my_policy.pdf ✓ (done, 21 chunks)
  - handbook.pdf ⏳ (processing, 12/18 chunks)
  - faq.txt ⏳ (queued)

Estimated time remaining: ~2 minutes
```

**Output (JSON):**
```json
{
  "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
  "rag_id": "policies_rag",
  "status": "processing",
  "submitted_at": "2025-01-10T20:15:30Z",
  "started_at": "2025-01-10T20:15:35Z",
  "files": [
    {
      "filename": "my_policy.pdf",
      "status": "done",
      "chunks": 21,
      "embeddings": 21,
      "completed_at": "2025-01-10T20:16:00Z"
    },
    {
      "filename": "handbook.pdf",
      "status": "processing",
      "chunks": 18,
      "embeddings": 12
    },
    {
      "filename": "faq.txt",
      "status": "queued"
    }
  ],
  "total_chunks": 39,
  "total_embeddings": 33,
  "estimated_remaining": 120
}
```

**Status Values:**
- `queued` — Waiting in queue
- `processing` — Worker is processing
- `done` — Successfully completed
- `failed` — Failed after retries
- `cancelled` — Cancelled by user

---

### 3. ingest reindex

Reindex an entire RAG (clear and rebuild collection).

**Usage:**
```bash
python -m services.ingest.cli ingest reindex --rag <rag_id> [options]
```

**Required Arguments:**
- `--rag <rag_id>` — RAG identifier

**Optional Arguments:**
- `--force` — Skip confirmation prompt
- `--from-processed` — Use files in processed/ folder (not incoming/)
- `--preserve-collection` — Keep existing collection, only update documents (slower)

**Examples:**

Reindex with confirmation:
```bash
python -m services.ingest.cli ingest reindex --rag policies_rag
```

Force reindex without prompt:
```bash
python -m services.ingest.cli ingest reindex --rag policies_rag --force
```

Reindex from processed files:
```bash
python -m services.ingest.cli ingest reindex \
  --rag policies_rag \
  --from-processed \
  --force
```

**Output:**
```
⚠️  This will:
  1. Clear collection: policies_rag_docs
  2. Reindex 3 documents from data/sources/policies_rag/incoming/

Continue? (yes/no): yes

✓ Cleared collection: policies_rag_docs
✓ Submitted reindex job: rag-policies_rag-reindex-1704882601-b8c3d4e5

Track progress: ingest status --job rag-policies_rag-reindex-1704882601-b8c3d4e5
```

**Warning:**
- This operation is destructive (clears collection)
- All previously indexed documents are removed
- Use `--preserve-collection` for safer updates

---

### 4. queue status

Check the status of the ingestion queue.

**Usage:**
```bash
python -m services.ingest.cli queue status [options]
```

**Optional Arguments:**
- `--watch` — Monitor queue in real-time
- `--timeout <seconds>` — Timeout for watch mode (default: 300)
- `--output json` — Output as JSON

**Examples:**

Check queue once:
```bash
python -m services.ingest.cli queue status
```

Watch queue in real-time:
```bash
python -m services.ingest.cli queue status --watch --timeout 600
```

JSON output:
```bash
python -m services.ingest.cli queue status --output json
```

**Output (Normal):**
```
Redis Queue Status
Location: rag:ingest:queue
Connection: redis://redis:6379/0

Queue Length: 5 jobs
  - Processing: 1
  - Queued: 4

Active Jobs:
  rag-policies_rag-1704882600-a7b2c3d4 (2 min remaining)

Queued Jobs:
  1. rag-faq_rag-1704882500-c9d4e5f6
  2. rag-procedures_rag-1704882480-d0e5f6g7
  3. rag-policies_rag-1704882460-e1f6g7h8
  4. rag-faq_rag-1704882440-f2g7h8i9

Worker Status: Connected
  - Redis connection: ✓
  - Qdrant connection: ✓
  - Last heartbeat: 2 seconds ago
```

**Output (JSON):**
```json
{
  "queue_name": "rag:ingest:queue",
  "connection": "redis://redis:6379/0",
  "queue_length": 5,
  "processing": 1,
  "queued": 4,
  "active_jobs": [
    {
      "job_id": "rag-policies_rag-1704882600-a7b2c3d4",
      "rag_id": "policies_rag",
      "status": "processing",
      "started_at": "2025-01-10T20:15:35Z",
      "estimated_remaining": 120
    }
  ],
  "worker": {
    "connected": true,
    "redis_ok": true,
    "qdrant_ok": true,
    "last_heartbeat": "2025-01-10T20:17:30Z"
  }
}
```

---

## Global Options

Available for all commands:

### --config <path>
Specify alternate configuration file.
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --config /path/to/client.yaml
```

### --log-level <level>
Set logging level: DEBUG, INFO, WARNING, ERROR.
```bash
python -m services.ingest.cli ingest status \
  --job <job_id> \
  --log-level DEBUG
```

### --redis-url <url>
Override Redis connection URL.
```bash
python -m services.ingest.cli queue status \
  --redis-url redis://custom-redis:6379/0
```

### --quiet
Suppress non-error output.
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --quiet
```

---

## Exit Codes

- `0` — Success
- `1` — Validation error (bad arguments, missing files, etc.)
- `2` — Submission/execution error (queue full, worker error, etc.)
- `3` — Configuration error (bad YAML, missing RAG, etc.)
- `4` — Connection error (Redis/Qdrant unavailable)
- `5` — Timeout error

---

## Common Workflows

### Workflow 1: Submit and Monitor

```bash
# Submit documents
JOB_ID=$(python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --quiet)

echo "Job ID: $JOB_ID"

# Monitor in real-time
python -m services.ingest.cli ingest status --job $JOB_ID --follow
```

### Workflow 2: Batch Ingestion with Script

```bash
#!/bin/bash

# Submit each RAG
for rag_id in policies_rag faq_rag procedures_rag; do
  python -m services.ingest.cli ingest submit \
    --rag $rag_id \
    --path data/sources/$rag_id/incoming
done

# Monitor all jobs
python -m services.ingest.cli queue status --watch
```

### Workflow 3: Reindex with Verification

```bash
# Reindex
python -m services.ingest.cli ingest reindex \
  --rag policies_rag \
  --force

# Wait for completion
while true; do
  STATUS=$(python -m services.ingest.cli queue status --output json | jq '.processing')
  if [ "$STATUS" -eq 0 ]; then
    echo "✓ Reindexing complete"
    break
  fi
  echo "Waiting... ($STATUS jobs processing)"
  sleep 5
done
```

### Workflow 4: Check Queue Health

```bash
#!/bin/bash

# Check worker status
python -m services.ingest.cli queue status

# If queue is stuck, check worker logs
docker logs raf_chatbot-ingest-worker-1 | tail -100

# Restart worker if needed
docker restart raf_chatbot-ingest-worker-1
```

---

## Error Messages and Solutions

### "RAG not found: policies_rag"
```
Solution:
1. Check RAG ID is correct
2. Verify configs/rags/policies_rag.yaml exists
3. Reload configuration with --config flag
```

### "Path does not exist: data/sources/policies_rag/incoming"
```
Solution:
1. Create directories: mkdir -p data/sources/policies_rag/{incoming,processed,failed}
2. Verify path is absolute or relative to current directory
3. Check file permissions
```

### "File too large (5.2 MB > 50 MB limit)"
```
Solution:
1. Check sources.max_file_size_mb in configs/rags/<rag_id>.yaml
2. Split document into smaller parts
3. Increase limit if appropriate (check disk space first)
```

### "Redis connection refused"
```
Solution:
1. Ensure Redis is running: docker ps | grep redis
2. Start services: make docker-up
3. Check Redis URL: --redis-url flag
4. Check firewall/network
```

### "Qdrant connection refused"
```
Solution:
1. Ensure Qdrant is running: docker ps | grep qdrant
2. Start services: make docker-up
3. Check Qdrant URL in configuration
4. Check firewall/network
```

### "Job stuck in processing"
```
Solution:
1. Check worker logs: docker logs raf_chatbot-ingest-worker-1
2. Check queue status: ingest queue status
3. Restart worker: docker restart raf_chatbot-ingest-worker-1
4. Check worker resource usage: docker stats
```

---

## Tips and Best Practices

### 1. Use Dry-Run First
Always test before submitting large batches:
```bash
python -m services.ingest.cli ingest submit \
  --rag policies_rag \
  --path data/sources/policies_rag/incoming \
  --dry-run
```

### 2. Monitor Queue Health
Periodically check:
```bash
python -m services.ingest.cli queue status --watch
```

### 3. Use JSON Output for Scripting
For automation, use JSON output:
```bash
STATUS=$(python -m services.ingest.cli ingest status \
  --job $JOB_ID \
  --output json)

CHUNKS=$(echo $STATUS | jq '.total_chunks')
echo "Total chunks: $CHUNKS"
```

### 4. Batch Large Collections
For many documents, submit in batches:
```bash
# Submit 10 files at a time
for batch in {1..10}; do
  python -m services.ingest.cli ingest submit \
    --rag policies_rag \
    --path data/sources/policies_rag/incoming
  
  # Wait for queue to process
  while [ $(python -m services.ingest.cli queue status --output json | jq '.processing') -gt 0 ]; do
    sleep 5
  done
done
```

### 5. Verify After Ingestion
Always verify documents were ingested:
```bash
# Check file was moved
ls data/sources/policies_rag/processed/

# Check no files in failed
ls data/sources/policies_rag/failed/
```

---

## Troubleshooting Guide

### Debug Mode
```bash
python -m services.ingest.cli ingest status \
  --job <job_id> \
  --log-level DEBUG
```

### Check Worker Health
```bash
# View worker logs
docker logs raf_chatbot-ingest-worker-1 -f

# Monitor resources
docker stats raf_chatbot-ingest-worker-1

# Restart worker
docker restart raf_chatbot-ingest-worker-1
```

### Inspect Queue
```bash
# Connect to Redis directly
redis-cli -h redis -p 6379

# View queue contents
LRANGE rag:ingest:queue 0 -1

# View job status
HGETALL rag:ingest:job:rag-policies_rag-1704882600-a7b2c3d4
```

### Check Configuration
```bash
# Validate YAML
python -m services.config.loader validate configs/client/client.yaml

# Validate RAG config
python -m services.config.loader validate configs/rags/policies_rag.yaml
```

---

## Next Steps

1. **Setup directories**: Create data/sources/<rag_id>/{incoming,processed,failed}
2. **Add documents**: Copy files to data/sources/<rag_id>/incoming/
3. **Submit**: Use `ingest submit` command
4. **Monitor**: Use `ingest status` to track progress
5. **Query**: Documents are now available for RAG queries

---

## Additional Resources

- Queue format: `services/ingest/queue_contract.md`
- Service overview: `services/ingest/README.md`
- Source organization: `data/sources/README.md`
- Configuration: `docs/configuration.md`
