# 📋 RAF Chatbot — Configuration Documentation

## Overview

RAF Chatbot uses a **declarative configuration** approach with two levels:

1. **Client Configuration** (`client.yaml`) — Global settings for the entire system
2. **RAG Configurations** (`configs/rags/*.yaml`) — Per-RAG settings for each retrieval-augmented generation instance

This document describes all available configuration fields, their types, defaults, and usage.

---

## Architecture

```
┌─────────────────────────────────────┐
│     client.yaml (Global)            │
│  - App settings (host, port)        │
│  - Qdrant connection                │
│  - Redis connection                 │
│  - LLM defaults                     │
│  - Global rate limits               │
│  - Security settings                │
└─────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────┐
    │  Load RAG configs from configs/rags/         │
    │  - policies_rag.yaml                         │
    │  - procedures_rag.yaml                       │
    │  - faq_rag.yaml                              │
    └──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────┐
│  Runtime: Merged configuration ready for RAG system  │
│  - Global defaults + per-RAG overrides              │
└──────────────────────────────────────────────────────┘
```

---

## Client Configuration Reference

### File: `configs/client/client.yaml`

#### Application Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `app.host` | string | Yes | `0.0.0.0` | IP address to bind to. Use `127.0.0.1` for localhost only. |
| `app.port` | integer | Yes | `8000` | Port number for FastAPI server. |
| `app.log_level` | string | Yes | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `app.environment` | string | Yes | `development` | Environment type: development, staging, production |
| `app.name` | string | No | `RAF Chatbot` | Display name shown in API responses. |

**Example:**
```yaml
app:
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"
  environment: "production"
  name: "RAF Chatbot Institucional"
```

---

#### Qdrant Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `qdrant.url` | string | Yes | `http://qdrant:6333` | Qdrant server URL. Use Docker service name in container mode. |
| `qdrant.api_key` | string | No | `null` | Optional API key for Qdrant authentication. |
| `qdrant.timeout_s` | integer | No | `30` | Connection timeout in seconds. |
| `qdrant.max_retries` | integer | No | `3` | Number of retry attempts on connection failure. |

**Example:**
```yaml
qdrant:
  url: "http://qdrant:6333"
  api_key: null
  timeout_s: 30
  max_retries: 3
```

**Docker Environment:**
```yaml
qdrant:
  url: "http://qdrant:6333"  # Use service name from docker-compose
  api_key: null
```

**Remote Deployment:**
```yaml
qdrant:
  url: "https://qdrant.example.com:6333"
  api_key: "${QDRANT_API_KEY}"  # From environment variable
```

---

#### Redis Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `redis.url` | string | Yes | `redis://redis:6379/0` | Redis connection URL. |
| `redis.password` | string | No | `null` | Optional password for Redis authentication. |
| `redis.db` | integer | No | `0` | Database index (0-15). |
| `redis.timeout_s` | integer | No | `10` | Connection timeout in seconds. |
| `redis.max_pool_size` | integer | No | `20` | Connection pool size. |

**Example:**
```yaml
redis:
  url: "redis://redis:6379/0"
  password: null
  db: 0
  timeout_s: 10
  max_pool_size: 20
```

---

#### LLM Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `llm.provider` | string | Yes | `openrouter` | LLM provider: openrouter, openai, anthropic, etc. |
| `llm.api_key_env_var` | string | Yes | `OPENROUTER_API_KEY` | Environment variable name for API key. |
| `llm.default_model` | string | Yes | `meta-llama/llama-2-70b-chat` | Default model ID. |
| `llm.fallback_model` | string | No | `gpt-3.5-turbo` | Fallback model if default fails. |
| `llm.timeout_s` | integer | No | `60` | API request timeout in seconds. |
| `llm.max_retries` | integer | No | `2` | Number of retry attempts. |
| `llm.max_tokens_default` | integer | No | `1024` | Default max tokens in response. |

**Example:**
```yaml
llm:
  provider: "openrouter"
  api_key_env_var: "OPENROUTER_API_KEY"
  default_model: "meta-llama/llama-2-70b-chat"
  fallback_model: "gpt-3.5-turbo"
  timeout_s: 60
  max_retries: 2
  max_tokens_default: 1024
```

---

#### Filesystem Paths

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `paths.sources_root` | string | Yes | `/app/data/sources` | Root directory for all RAG source files. |
| `paths.rags_config_dir` | string | Yes | `/app/configs/rags` | Directory containing RAG YAML files. |
| `paths.logs_dir` | string | No | `/app/logs` | Directory for application logs. |
| `paths.templates_dir` | string | No | `/app/configs/templates` | Directory containing prompt templates. |

**Example:**
```yaml
paths:
  sources_root: "/app/data/sources"
  rags_config_dir: "/app/configs/rags"
  logs_dir: "/app/logs"
  templates_dir: "/app/configs/templates"
```

---

#### Concurrency & Rate Limiting

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concurrency.global_max_inflight_requests` | integer | No | `100` | Maximum concurrent requests across all RAGs. |
| `concurrency.global_rate_limit` | integer | No | `1000` | Global requests per second limit. |
| `concurrency.request_timeout_s` | integer | No | `120` | Maximum duration for one request in seconds. |

**Example:**
```yaml
concurrency:
  global_max_inflight_requests: 100
  global_rate_limit: 1000
  request_timeout_s: 120
```

---

#### Security

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `security.behind_nginx` | boolean | No | `true` | Whether running behind Nginx reverse proxy. |
| `security.trusted_proxies` | list | No | `[127.0.0.1, nginx]` | Proxies to trust for X-Forwarded-* headers. |
| `security.cors_origins` | list | No | `[http://localhost:3000, http://localhost:8080]` | Allowed CORS origins. |
| `security.require_api_key` | boolean | No | `false` | Whether to require API key for all requests. |
| `security.api_key_header` | string | No | `X-API-Key` | HTTP header name for API key. |

**Example:**
```yaml
security:
  behind_nginx: true
  trusted_proxies:
    - "127.0.0.1"
    - "nginx"
    - "10.0.0.0/8"
  cors_origins:
    - "http://localhost:3000"
    - "https://example.com"
  require_api_key: false
  api_key_header: "X-API-Key"
```

---

#### Cache Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cache.enabled` | boolean | No | `true` | Enable global response caching. |
| `cache.ttl_seconds` | integer | No | `3600` | Cache time-to-live in seconds (1 hour). |
| `cache.backend` | string | No | `redis` | Cache backend: redis or memory. |

**Example:**
```yaml
cache:
  enabled: true
  ttl_seconds: 3600
  backend: "redis"
```

---

#### Session Management

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sessions.enabled` | boolean | No | `true` | Enable conversation session tracking. |
| `sessions.ttl_seconds` | integer | No | `86400` | Session TTL in seconds (24 hours). |
| `sessions.max_history_turns` | integer | No | `10` | Maximum conversation turns to remember. |

**Example:**
```yaml
sessions:
  enabled: true
  ttl_seconds: 86400
  max_history_turns: 10
```

---

#### Monitoring & Observability

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `monitoring.enable_metrics` | boolean | No | `true` | Enable Prometheus metrics endpoint. |
| `monitoring.enable_tracing` | boolean | No | `false` | Enable distributed tracing. |
| `monitoring.trace_sample_rate` | float | No | `0.1` | Tracing sample rate (0.0-1.0). |

**Example:**
```yaml
monitoring:
  enable_metrics: true
  enable_tracing: false
  trace_sample_rate: 0.1
```

---

#### Error Handling

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `error_handling.return_stack_traces` | boolean | No | `false` | Include stack traces in API responses. |
| `error_handling.log_full_errors` | boolean | No | `true` | Log full error details server-side. |
| `error_handling.default_error_message` | string | No | `An error occurred...` | User-facing error message. |

**Example:**
```yaml
error_handling:
  return_stack_traces: false
  log_full_errors: true
  default_error_message: "An error occurred. Please try again."
```

---

## RAG Configuration Reference

### File: `configs/rags/<rag_id>.yaml`

Each RAG configuration file defines settings for ONE retrieval-augmented generation instance.

#### RAG Identification

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `rag_id` | string | Yes | — | Unique identifier (alphanumeric + underscore). Used in API routes. |
| `display_name` | string | No | — | Human-readable name. |
| `description` | string | No | — | Description of this RAG's purpose. |

**Example:**
```yaml
rag_id: "policies_rag"
display_name: "Company Policies"
description: "RAG for company HR policies and procedures"
```

---

#### Collection Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection.name` | string | Yes | — | Qdrant collection name. Must be unique. |
| `collection.recreation_policy` | string | No | `skip` | Policy when collection exists: skip, recreate, or append. |
| `collection.shard_number` | integer | No | `1` | Number of shards (1 for small collections, >1 for large). |

**Example:**
```yaml
collection:
  name: "policies_rag_docs"
  recreation_policy: "skip"
  shard_number: 1
```

---

#### Embeddings Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `embeddings.model_name` | string | Yes | — | Hugging Face model ID for embeddings. |
| `embeddings.dimension` | integer | Yes | — | Vector dimension (depends on model). |
| `embeddings.batch_size` | integer | No | `32` | Batch size for embedding generation. |
| `embeddings.normalize` | boolean | No | `true` | L2 normalize embeddings. |

**Popular Models:**
- `sentence-transformers/all-MiniLM-L6-v2` (384 dims, fast)
- `sentence-transformers/all-mpnet-base-v2` (768 dims, accurate)
- `BAAI/bge-base-en-v1.5` (768 dims, multilingual)

**Example:**
```yaml
embeddings:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32
  normalize: true
```

---

#### Document Chunking

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `chunking.splitter` | string | No | `recursive_character` | Splitting strategy: recursive_character or semantic. |
| `chunking.chunk_size` | integer | No | `512` | Characters per chunk. |
| `chunking.chunk_overlap` | integer | No | `128` | Overlap between chunks to maintain context. |
| `chunking.separator` | string | No | `\n\n` | Primary separator. |
| `chunking.secondary_separators` | list | No | `[\n, , ]` | Fallback separators. |

**Example:**
```yaml
chunking:
  splitter: "recursive_character"
  chunk_size: 512
  chunk_overlap: 128
  separator: "\n\n"
  secondary_separators:
    - "\n"
    - " "
    - ""
```

---

#### Retrieval Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `retrieval.top_k` | integer | No | `5` | Number of documents to retrieve. |
| `retrieval.score_threshold` | float | No | `0.5` | Minimum similarity score (0.0-1.0). |
| `retrieval.max_context_chunks` | integer | No | `10` | Maximum chunks to include in context. |
| `retrieval.rerank` | boolean | No | `false` | Enable semantic reranking (slower but more accurate). |
| `retrieval.filter_duplicates` | boolean | No | `true` | Remove duplicate chunks. |

**Example:**
```yaml
retrieval:
  top_k: 5
  score_threshold: 0.5
  max_context_chunks: 10
  rerank: false
  filter_duplicates: true
```

---

#### Prompting & LLM Interaction

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompting.system_template_path` | string | Yes | — | Path to system prompt template. |
| `prompting.user_template_path` | string | Yes | — | Path to user prompt template. |
| `prompting.max_tokens` | integer | No | `1024` | Maximum tokens in LLM response. |
| `prompting.temperature` | float | No | `0.7` | Randomness (0.0=deterministic, 1.0=random). |
| `prompting.top_p` | float | No | `0.95` | Nucleus sampling parameter. |
| `prompting.frequency_penalty` | float | No | `0.0` | Penalty for repeated tokens. |
| `prompting.presence_penalty` | float | No | `0.0` | Penalty for token presence. |

**Example:**
```yaml
prompting:
  system_template_path: "/app/configs/templates/system_prompt.txt"
  user_template_path: "/app/configs/templates/user_prompt.txt"
  max_tokens: 1024
  temperature: 0.7
  top_p: 0.95
  frequency_penalty: 0.0
  presence_penalty: 0.0
```

---

#### Rate Limiting (Per RAG)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `rate_limit.requests_per_second` | integer | No | `10` | Max requests per second for this RAG. |
| `rate_limit.burst_size` | integer | No | `20` | Max burst requests. |
| `rate_limit.per_user` | boolean | No | `false` | Apply limits per user (requires auth). |

**Example:**
```yaml
rate_limit:
  requests_per_second: 10
  burst_size: 20
  per_user: false
```

---

#### Error Messages

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `errors.no_context_message` | string | No | — | Message when no relevant context found. |
| `errors.provider_error_message` | string | No | — | Message when LLM provider fails. |
| `errors.timeout_message` | string | No | — | Message when request times out. |
| `errors.rate_limit_message` | string | No | — | Message when rate limit exceeded. |

**Example:**
```yaml
errors:
  no_context_message: "No relevant information found for your query."
  provider_error_message: "The LLM service is temporarily unavailable."
  timeout_message: "Request timed out. Please try again."
  rate_limit_message: "Too many requests. Please try again later."
```

---

#### Caching (Per RAG)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cache.enabled` | boolean | No | `true` | Cache responses for this RAG. |
| `cache.ttl_seconds` | integer | No | `3600` | Cache TTL in seconds. |
| `cache.key_prefix` | string | No | — | Cache key prefix for organization. |

**Example:**
```yaml
cache:
  enabled: true
  ttl_seconds: 3600
  key_prefix: "policies_rag"
```

---

#### Session Management (Per RAG)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sessions.enabled` | boolean | No | `true` | Enable conversation history. |
| `sessions.history_turns` | integer | No | `5` | Number of previous turns to remember. |
| `sessions.ttl_seconds` | integer | No | `3600` | Session TTL in seconds. |
| `sessions.deduplicate_history` | boolean | No | `true` | Remove duplicate messages. |

**Example:**
```yaml
sessions:
  enabled: true
  history_turns: 5
  ttl_seconds: 3600
  deduplicate_history: true
```

---

#### Source Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sources.directory` | string | Yes | — | Subdirectory in `paths.sources_root`. |
| `sources.allowed_extensions` | list | No | — | File extensions to ingest (.pdf, .txt, .md, .docx). |
| `sources.max_file_size_mb` | integer | No | `50` | Maximum file size in MB. |
| `sources.auto_reload` | boolean | No | `true` | Auto-reload when files change. |

**Example:**
```yaml
sources:
  directory: "policies_sources"
  allowed_extensions:
    - ".pdf"
    - ".txt"
    - ".md"
    - ".docx"
  max_file_size_mb: 50
  auto_reload: true
```

---

#### Metadata & Indexing

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `metadata.extract_title` | boolean | No | `true` | Extract document title. |
| `metadata.extract_date` | boolean | No | `true` | Extract modification date. |
| `metadata.custom_fields` | list | No | `[]` | Additional metadata fields. |

**Example:**
```yaml
metadata:
  extract_title: true
  extract_date: true
  custom_fields:
    - "author"
    - "department"
```

---

#### Security (Per RAG)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `security.public` | boolean | No | `true` | Accessible without authentication. |
| `security.allowed_users` | list | No | `[]` | List of allowed user IDs (empty = all). |
| `security.require_consent` | boolean | No | `false` | Require data usage consent. |

**Example:**
```yaml
security:
  public: true
  allowed_users: []
  require_consent: false
```

---

#### Monitoring & Logging (Per RAG)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `monitoring.log_queries` | boolean | No | `true` | Log user queries. |
| `monitoring.log_responses` | boolean | No | `false` | Log LLM responses (be careful with PII). |
| `monitoring.collect_metrics` | boolean | No | `true` | Collect performance metrics. |
| `monitoring.alert_on_error` | boolean | No | `true` | Alert when errors occur. |

**Example:**
```yaml
monitoring:
  log_queries: true
  log_responses: false
  collect_metrics: true
  alert_on_error: true
```

---

#### Experimental Features

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `experimental.enable_reranking` | boolean | No | `false` | Use semantic reranking. |
| `experimental.enable_hyde` | boolean | No | `false` | Hypothetical Document Embeddings. |
| `experimental.enable_query_expansion` | boolean | No | `false` | Expand queries for better retrieval. |

**Example:**
```yaml
experimental:
  enable_reranking: false
  enable_hyde: false
  enable_query_expansion: false
```

---

## Usage Examples

### Example 1: Simple Client Configuration

**File:** `configs/client/client.yaml`

```yaml
app:
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"
  environment: "development"

qdrant:
  url: "http://qdrant:6333"

redis:
  url: "redis://redis:6379/0"

llm:
  provider: "openrouter"
  api_key_env_var: "OPENROUTER_API_KEY"
  default_model: "meta-llama/llama-2-70b-chat"

paths:
  sources_root: "/app/data/sources"
  rags_config_dir: "/app/configs/rags"

concurrency:
  global_max_inflight_requests: 100
  global_rate_limit: 1000
```

---

### Example 2: Company Policies RAG

**File:** `configs/rags/policies_rag.yaml`

```yaml
rag_id: "policies_rag"
display_name: "Company Policies"

collection:
  name: "policies_docs"

embeddings:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384

chunking:
  chunk_size: 512
  chunk_overlap: 128

retrieval:
  top_k: 5
  score_threshold: 0.5

prompting:
  system_template_path: "/app/configs/templates/system_prompt.txt"
  user_template_path: "/app/configs/templates/user_prompt.txt"
  max_tokens: 1024
  temperature: 0.7

sources:
  directory: "policies_sources"
  allowed_extensions: [".pdf", ".txt", ".md"]
```

---

### Example 3: FAQ RAG with Custom Settings

**File:** `configs/rags/faq_rag.yaml`

```yaml
rag_id: "faq_rag"
display_name: "Frequently Asked Questions"

collection:
  name: "faq_collection"

embeddings:
  model_name: "sentence-transformers/all-mpnet-base-v2"
  dimension: 768

retrieval:
  top_k: 3
  score_threshold: 0.6
  rerank: true  # Better accuracy for FAQs

rate_limit:
  requests_per_second: 20  # Higher limit for FAQ
  burst_size: 50

cache:
  enabled: true
  ttl_seconds: 7200  # 2 hours

sources:
  directory: "faq_sources"
  allowed_extensions: [".txt", ".md", ".json"]
```

---

## Important Rules

### 1. One RAG = One Collection

Each RAG configuration maps to **exactly one collection** in Qdrant. Do NOT share collections between RAGs.

```yaml
# ❌ WRONG: Multiple RAGs in same collection
policies_rag:
  collection_name: "shared_docs"
procedures_rag:
  collection_name: "shared_docs"

# ✅ CORRECT: Each RAG has unique collection
policies_rag:
  collection_name: "policies_docs"
procedures_rag:
  collection_name: "procedures_docs"
```

---

### 2. Environment Variables

API keys and sensitive data should use environment variables, NOT hardcoded values:

```yaml
# ❌ WRONG: Hardcoded API key
llm:
  api_key: "sk-1234567890abcdef"

# ✅ CORRECT: Use environment variable
llm:
  api_key_env_var: "OPENROUTER_API_KEY"  # Variable name
```

Then set in your environment:
```bash
export OPENROUTER_API_KEY="sk-1234567890abcdef"
```

---

### 3. Path Conventions

Use absolute paths inside containers; relative paths for local development:

**Docker:**
```yaml
paths:
  sources_root: "/app/data/sources"       # Absolute
  rags_config_dir: "/app/configs/rags"    # Absolute
```

**Local Development:**
```yaml
paths:
  sources_root: "./data/sources"          # Relative
  rags_config_dir: "./configs/rags"       # Relative
```

---

### 4. Template Files

Prompting requires two template files per RAG:

```yaml
prompting:
  system_template_path: "/app/configs/templates/system_prompt.txt"
  user_template_path: "/app/configs/templates/user_prompt.txt"
```

Templates use Jinja2 syntax with variables:
- `{{ context }}` — Retrieved documents
- `{{ query }}` — User query
- `{{ history }}` — Conversation history (if enabled)

---

### 5. Configuration Precedence

When loading configuration:

1. **Client defaults** (`client.yaml`)
2. **RAG-specific overrides** (`configs/rags/<rag_id>.yaml`)
3. **Environment variables** (highest priority)

Example:
```yaml
# client.yaml
cache:
  ttl_seconds: 3600

# configs/rags/faq_rag.yaml (overrides client)
cache:
  ttl_seconds: 7200  # 2 hours instead of 1 hour
```

---

## Validation Checklist

Before using configuration files:

- [ ] Client configuration has all required fields
- [ ] Each RAG config has unique `rag_id`
- [ ] Each RAG collection name is unique
- [ ] All paths exist or can be created
- [ ] Template files referenced in `prompting` exist
- [ ] Source directories exist in `paths.sources_root`
- [ ] Environment variables are set (e.g., `OPENROUTER_API_KEY`)
- [ ] Port numbers don't conflict
- [ ] Rate limits are reasonable for your deployment
- [ ] Error messages are clear and helpful

---

## Next Steps

1. Copy `client.yaml.example` to `client.yaml` and adjust for your environment
2. Create RAG configs by copying `example_rag.yaml` to `<rag_id>.yaml`
3. Create prompt template files referenced in RAG configs
4. Validate configuration with schema validation (Subproject 4)
5. Load and test configuration in application (Subproject 5+)

---

## Questions?

For issues or questions about configuration:
1. Check the validation checklist above
2. Review the examples in this document
3. Ensure environment variables are set correctly
4. Check application logs for configuration errors
```

</file_description>