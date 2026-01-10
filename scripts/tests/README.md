# RAF Chatbot — Testing Scripts

## Quick Start (No API Keys)

### Prerequisites
- Docker and Docker Compose installed
- Python 3.9+
- Project dependencies installed

### Step 1: Start Docker Services

```bash
cd G:\zed_projects\raf_chatbot
docker-compose up -d
```

Wait 10-15 seconds for services to start.

### Step 2: Run the End-to-End Test

```bash
python scripts/tests/test_e2e_no_apikeys.py
```

### Expected Output

```
======================================================================
  RAF CHATBOT — END-TO-END TEST (No API Keys Required)
======================================================================

✅ SP1: Foundation & Scaffolding
✅ SP2: Docker Compose Base
✅ SP3: Configuration (YAML)
✅ SP4: Document Ingest Pipeline
✅ SP5: Configuration Loader & Validation
✅ SP6: Embedding Service & Vector Indexing

======================================================================
  TEST 1: Load & Validate Configurations (SP5)
======================================================================

✅ Client config file found
✅ RAG config file found

======================================================================
  TEST 2: Create Test Documents (SP4)
======================================================================

✅ Created: document_1.txt
✅ Created: document_2.txt
✅ Created: document_3.txt

... (more tests) ...

======================================================================
  TEST SUMMARY
======================================================================

✅ PASS — Config Loading (SP5)
✅ PASS — Document Creation (SP4)
✅ PASS — Embedding Generation (SP6)
✅ PASS — Qdrant Connection (SP2)
✅ PASS — Redis Connection (SP2)

📊 Results: 5/5 tests passed

✅ All tests passed! System is ready.
```

## Available Tests

### `test_e2e_no_apikeys.py`
End-to-end test of Subprojects 1-6 without any API keys.

**What it tests:**
- Configuration loading and validation (SP5)
- Document creation (SP4)
- Embedding generation with dummy vectors (SP6)
- Qdrant vector database connection (SP2)
- Redis cache connection (SP2)

**Run:**
```bash
python scripts/tests/test_e2e_no_apikeys.py
```

## Troubleshooting

### Docker services not running
```bash
docker-compose up -d
docker-compose ps
```

### Python module import errors
```bash
pip install -r services/api/requirements.txt
pip install -r services/ingest/requirements.txt
```

### Qdrant connection failed
```bash
docker-compose logs qdrant
docker-compose restart qdrant
```

### Redis connection failed
```bash
docker-compose logs redis
docker-compose restart redis
```

## Next Steps

1. ✅ Run the end-to-end test
2. ✅ Verify all 5/5 tests pass
3. ✅ Check configuration validation tests:
   ```bash
   pytest tests/test_config_validation.py -v
   ```
4. ✅ Proceed to Subproject 7: Vector Retrieval & Ranking

## Project Status

- **Completed**: 6/10 subprojects (60%)
- **Current**: Testing SP1-SP6
- **Next**: Subproject 7 (Vector Retrieval & Ranking)
- **API Keys**: None required until SP8 (LLM Integration)

## Quick Commands

```bash
# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f qdrant
docker-compose logs -f redis

# Stop services
docker-compose down

# Full reset
docker-compose down -v
docker-compose up -d
```

---

**Path**: `G:\zed_projects\raf_chatbot\scripts\tests\README.md`
