# RAF Chatbot — Configuration Validation Rules

This document details all validation rules applied to client and RAG configurations.

## Overview

Configuration validation is performed using **Pydantic models** which provide:
- **Type safety**: Fields are validated against expected types
- **Range checking**: Numeric values are bounded
- **Format validation**: URLs, IDs, and paths follow expected formats
- **Business logic**: Complex constraints (e.g., chunk_overlap < chunk_size)

## Client Configuration (`client.yaml`)

### App Settings

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `host` | string | - | `0.0.0.0` | Listen address (IP or hostname) |
| `port` | integer | 1-65535 | 8000 | Valid network port |
| `log_level` | enum | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Must be one of specified values |
| `environment` | enum | development, staging, production | development | Deployment environment |
| `name` | string | - | RAF Chatbot | Application display name |

**Validation Rules:**
- `port` must be between 1 and 65535
- `log_level` must be one of the allowed values (case-sensitive)
- `environment` must match deployment stage
- All fields are required (no null values)

### Qdrant Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `url` | string | - | - | Connection URL |
| `api_key` | string | - | null | Optional API key |
| `timeout_s` | integer | 1-300 | 30 | Timeout in seconds |
| `max_retries` | integer | 0-10 | 3 | Retry attempts |

**Validation Rules:**
- `url` must start with `http://` or `https://`
- `url` is required (non-null)
- `timeout_s` must be between 1 and 300 seconds
- `max_retries` must be between 0 and 10
- `api_key` can be null (optional)

### Redis Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `url` | string | - | - | Connection URL |
| `password` | string | - | null | Optional password |
| `db` | integer | 0-15 | 0 | Database index |
| `timeout_s` | integer | 1-60 | 10 | Timeout in seconds |
| `max_pool_size` | integer | 1-100 | 20 | Connection pool size |

**Validation Rules:**
- `url` must start with `redis://` or `rediss://`
- `url` is required (non-null)
- `db` must be between 0 and 15 (Redis standard)
- `timeout_s` must be between 1 and 60 seconds
- `max_pool_size` must be between 1 and 100
- `password` can be null (optional)

### LLM Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `provider` | string | - | openrouter | LLM provider name |
| `api_key_env_var` | string | - | OPENROUTER_API_KEY | Environment variable for API key |
| `default_model` | string | - | - | Default LLM model ID |
| `fallback_model` | string | - | null | Fallback model ID |
| `timeout_s` | integer | 1-300 | 60 | Request timeout |
| `max_retries` | integer | 0-10 | 2 | Retry attempts |
| `max_tokens_default` | integer | 1-32000 | 1024 | Default max tokens |

**Validation Rules:**
- `default_model` is required (non-null)
- `timeout_s` must be between 1 and 300 seconds
- `max_retries` must be between 0 and 10
- `max_tokens_default` must be between 1 and 32000
- `fallback_model` can be null

### Paths Configuration

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `sources_root` | string | /app/data/sources | Root directory for RAG sources |
| `rags_config_dir` | string | /app/configs/rags | Directory with RAG configs |
| `logs_dir` | string | /app/logs | Application logs directory |
| `templates_dir` | string | /app/configs/templates | Prompt templates directory |

**Validation Rules:**
- All paths should be absolute paths
- Paths are required (non-null)
- No validation of path existence (done at runtime)

### Concurrency Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `global_max_inflight_requests` | integer | 1-10000 | 100 | Max concurrent requests |
| `global_rate_limit` | integer | 1-100000 | 1000 | Requests per second |
| `request_timeout_s` | integer | 1-600 | 120 | Request timeout |

**Validation Rules:**
- All values must be positive integers
- `global_max_inflight_requests` between 1-10000
- `global_rate_limit` between 1-100000
- `request_timeout_s` between 1-600 seconds

### Security Configuration

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `behind_nginx` | boolean | true | Behind reverse proxy? |
| `trusted_proxies` | list[string] | ["127.0.0.1"] | Trusted IPs |
| `cors_origins` | list[string] | [] | CORS allowed origins |
| `require_api_key` | boolean | false | Require API key? |
| `api_key_header` | string | X-API-Key | API key header name |

**Validation Rules:**
- `trusted_proxies` must contain valid IP addresses
- `cors_origins` must be valid URLs (when specified)
- `api_key_header` is used only if `require_api_key` is true

### Cache Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `enabled` | boolean | - | true | Cache enabled? |
| `ttl_seconds` | integer | 1-86400 | 3600 | Cache TTL |
| `backend` | enum | redis, memory | redis | Cache backend |

**Validation Rules:**
- `ttl_seconds` must be between 1 second and 1 day (86400 seconds)
- `backend` must be either "redis" or "memory"

### Sessions Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `enabled` | boolean | - | true | Sessions enabled? |
| `ttl_seconds` | integer | 1-604800 | 86400 | Session TTL |
| `max_history_turns` | integer | 1-100 | 10 | Max history turns |

**Validation Rules:**
- `ttl_seconds` must be between 1 second and 7 days (604800 seconds)
- `max_history_turns` must be between 1 and 100

### Monitoring Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `enable_metrics` | boolean | - | true | Prometheus metrics? |
| `enable_tracing` | boolean | - | false | Distributed tracing? |
| `trace_sample_rate` | float | 0.0-1.0 | 0.1 | Sampling rate |

**Validation Rules:**
- `trace_sample_rate` must be between 0.0 and 1.0 (0% to 100%)

### Error Handling Configuration

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `return_stack_traces` | boolean | false | Return stack traces in responses? |
| `log_full_errors` | boolean | true | Log full errors server-side? |
| `default_error_message` | string | An error occurred. | Default error message |

**Validation Rules:**
- Setting `return_stack_traces: true` is not recommended for production

---

## RAG Configuration (`<rag_id>.yaml`)

### RAG Identification

| Field | Type | Rule |
|-------|------|------|
| `rag_id` | string | Unique identifier |
| `display_name` | string | Human-readable name |
| `description` | string | RAG description (optional) |

**Validation Rules:**
- `rag_id` must contain only alphanumeric characters and underscores: `^[a-zA-Z0-9_]+$`
- `rag_id` is required (non-null)
- `display_name` is required (non-null)
- `description` can be null or empty

### Collection Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `name` | string | - | - | Collection name in Qdrant |
| `recreation_policy` | enum | skip, recreate, append | skip | Policy on collection exists |
| `shard_number` | integer | 1-32 | 1 | Number of shards |

**Validation Rules:**
- `name` is required (non-null)
- `recreation_policy` must be one of: skip, recreate, append
- `shard_number` must be between 1 and 32

### Embeddings Configuration

| Field | Type | Range | Rule |
|-------|------|-------|------|
| `model_name` | string | - | Hugging Face model ID (required) |
| `dimension` | integer | 64-4096 | Vector dimension (required) |
| `batch_size` | integer | 1-1024 | Batch size for embedding |
| `normalize` | boolean | - | L2 normalize embeddings? |

**Validation Rules:**
- `model_name` is required (non-null)
- `dimension` must be between 64 and 4096
- `batch_size` must be between 1 and 1024
- `dimension` should match the actual model's output dimension

### Chunking Configuration

| Field | Type | Range | Rule |
|-------|------|-------|------|
| `splitter` | enum | recursive_character, semantic | Splitter type |
| `chunk_size` | integer | 64-4096 | Chunk size in characters |
| `chunk_overlap` | integer | 0-1024 | Overlap in characters |
| `separator` | string | - | Primary separator |
| `secondary_separators` | list[string] | - | Fallback separators |

**Validation Rules:**
- `splitter` must be one of: recursive_character, semantic
- `chunk_size` must be between 64 and 4096 characters
- `chunk_overlap` must be between 0 and 1024 characters
- **CRITICAL:** `chunk_overlap` **must be less than** `chunk_size`
  - Example: chunk_size=512, chunk_overlap=128 ✓
  - Example: chunk_size=512, chunk_overlap=512 ✗ (INVALID)
- `separator` should be a string (default: `\n\n`)

### Retrieval Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `top_k` | integer | 1-50 | 5 | Top K documents to retrieve |
| `score_threshold` | float | 0.0-1.0 | 0.5 | Minimum similarity score |
| `max_context_chunks` | integer | 1-100 | 10 | Maximum chunks in context |
| `rerank` | boolean | - | false | Enable reranking? |
| `filter_duplicates` | boolean | - | true | Remove duplicate chunks? |

**Validation Rules:**
- `top_k` must be between 1 and 50
- `score_threshold` must be between 0.0 and 1.0
- `max_context_chunks` must be between 1 and 100
- Higher `top_k` values increase latency

### Prompting Configuration

| Field | Type | Range | Rule |
|-------|------|-------|------|
| `system_template_path` | string | - | System prompt template (required) |
| `user_template_path` | string | - | User prompt template (required) |
| `max_tokens` | integer | 1-32000 | Max response tokens |
| `temperature` | float | 0.0-2.0 | Randomness level |
| `top_p` | float | 0.0-1.0 | Nucleus sampling |
| `frequency_penalty` | float | -2.0 to 2.0 | Repeated token penalty |
| `presence_penalty` | float | -2.0 to 2.0 | Token presence penalty |

**Validation Rules:**
- `system_template_path` is required (non-null)
- `user_template_path` is required (non-null)
- `max_tokens` must be between 1 and 32000
- `temperature` must be between 0.0 and 2.0
  - 0.0 = deterministic (no randomness)
  - 1.0 = normal randomness
  - 2.0 = maximum randomness
- `top_p` must be between 0.0 and 1.0
- `frequency_penalty` and `presence_penalty` between -2.0 and 2.0

### Rate Limiting Configuration

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `requests_per_second` | integer | 1-1000 | 10 | Max RPS for this RAG |
| `burst_size` | integer | 1-10000 | 20 | Max burst requests |
| `per_user` | boolean | - | false | Apply limits per user? |

**Validation Rules:**
- `requests_per_second` must be between 1 and 1000
- `burst_size` must be between 1 and 10000
- Should be <= global_rate_limit from client config

### Error Messages Configuration

| Field | Type | Rule |
|-------|------|------|
| `no_context_message` | string | Message when no context found |
| `provider_error_message` | string | Message on LLM error |
| `timeout_message` | string | Message on request timeout |
| `rate_limit_message` | string | Message on rate limit hit |

**Validation Rules:**
- All fields are required (non-null)
- Messages should be user-friendly and non-technical

### Cache Configuration (Per-RAG)

| Field | Type | Range | Rule |
|-------|------|-------|------|
| `enabled` | boolean | - | Cache enabled for this RAG? |
| `ttl_seconds` | integer | 1-86400 | Cache TTL |
| `key_prefix` | string | - | Cache key prefix (required) |

**Validation Rules:**
- `key_prefix` must be non-empty string
- `ttl_seconds` must be between 1 and 86400 seconds
- `key_prefix` should match `rag_id` for clarity

### Sessions Configuration (Per-RAG)

| Field | Type | Range | Default | Rule |
|-------|------|-------|---------|------|
| `enabled` | boolean | - | true | Sessions enabled for this RAG? |
| `history_turns` | integer | 1-100 | 5 | Previous turns to remember |
| `ttl_seconds` | integer | 1-86400 | 3600 | Session TTL |
| `deduplicate_history` | boolean | - | true | Remove duplicate messages? |

**Validation Rules:**
- `history_turns` must be between 1 and 100
- `ttl_seconds` must be between 1 and 86400 seconds

### Sources Configuration

| Field | Type | Range | Rule |
|-------|------|-------|------|
| `directory` | string | - | Sources subdirectory name (required) |
| `allowed_extensions` | list[string] | - | Allowed file extensions (required) |
| `max_file_size_mb` | integer | 1-500 | Maximum file size in MB |
| `auto_reload` | boolean | - | Auto-reload when files change? |

**Validation Rules:**
- `directory` is required (non-null)
- `allowed_extensions` must have at least one extension
- Each extension must start with a dot: `.pdf`, `.txt`, `.md`, etc.
  - Valid: `[".pdf", ".txt"]` ✓
  - Invalid: `["pdf", "txt"]` ✗ (missing dots)
- `max_file_size_mb` must be between 1 and 500 MB
- Common extensions: .pdf, .txt, .md, .docx, .json, .csv

### Metadata Configuration

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `extract_title` | boolean | true | Extract document title? |
| `extract_date` | boolean | true | Extract modification date? |
| `custom_fields` | list[string] | [] | Additional metadata fields |

**Validation Rules:**
- `custom_fields` can be empty list
- Custom field names should be descriptive (e.g., "author", "category")

### Security Configuration (Per-RAG)

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `public` | boolean | true | Publicly accessible? |
| `allowed_users` | list[string] | [] | Allowed user IDs |
| `require_consent` | boolean | false | Require data usage consent? |

**Validation Rules:**
- If `public: false`, `allowed_users` must not be empty
- If `public: true`, `allowed_users` is ignored

### Monitoring Configuration (Per-RAG)

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `log_queries` | boolean | true | Log user queries? |
| `log_responses` | boolean | false | Log LLM responses? |
| `collect_metrics` | boolean | true | Collect metrics? |
| `alert_on_error` | boolean | true | Alert on errors? |

**Validation Rules:**
- Be cautious with `log_responses: true` (may contain PII)
- `log_queries` should be true for debugging

### Experimental Features Configuration

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `enable_reranking` | boolean | false | Enable semantic reranking? |
| `enable_hyde` | boolean | false | Enable HyDE? |
| `enable_query_expansion` | boolean | false | Enable query expansion? |

**Validation Rules:**
- These features are experimental and may impact performance
- Enable selectively and monitor impact

---

## Cross-Field Validation Rules

### Client + RAG Consistency

When loading both client and RAG configs:
- Each `rag_id` must be unique across all RAG YAML files
- `rate_limit.requests_per_second` (per RAG) should not exceed `global_rate_limit` (client)
- `cache.ttl_seconds` (per RAG) should not exceed `cache.ttl_seconds` (client)

### Embedding + Chunking Consistency

- `embeddings.dimension` must match the actual model's output dimension
  - Example: `sentence-transformers/all-MiniLM-L6-v2` outputs 384 dimensions
- `chunking.chunk_size` should be reasonable for your embedding model
  - Recommendation: 512-2048 characters per chunk

### Retrieval + LLM Consistency

- `retrieval.max_context_chunks` × `chunking.chunk_size` should not exceed LLM context window
  - Example: 10 chunks × 512 chars = 5120 chars ≈ 1280 tokens (safe for most models)
- `prompting.max_tokens` should be reasonable relative to LLM's context limit

---

## Error Messages and Debugging

When validation fails, Pydantic provides detailed error messages:

**Example 1: Invalid port number**
```
validation error for ClientConfig
app -> port
  ensure this value is less than or equal to 65535 (type=value_error.number.not_le; limit_value=65535)
```

**Example 2: Missing required field**
```
validation error for RagConfig
rag_id
  field required (type=value_error.missing)
```

**Example 3: Invalid enum value**
```
validation error for ClientConfig
app -> log_level
  value is not a valid enumeration member; permitted: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' (type=type_error.enum; enum_values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
```

---

## Best Practices

1. **Start from examples**: Use `client.yaml.example` and `example_rag.yaml` as templates
2. **Validate locally first**: Run tests before deploying (`pytest tests/test_config_validation.py`)
3. **Document custom settings**: If you override defaults, explain why
4. **Monitor validation errors**: Log validation failures for debugging
5. **Version your configs**: Keep configs in version control with explanatory comments
6. **Test edge cases**: Try boundary values (min/max) before production

---

## Implementation

The validation system is implemented in:
- **Models**: `services/api/config/models.py` — Pydantic model definitions
- **Loader**: `services/api/config/loader.py` — Config loading and validation
- **Tests**: `tests/test_config_validation.py` — Validation test suite

To load and validate configs in your code:

```python
from services.api.config import ConfigLoader, ClientConfig, RagConfig

# Load client config
client_config = ConfigLoader.load_client_config("configs/client/client.yaml")

# Load single RAG config
rag_config = ConfigLoader.load_rag_config("configs/rags/my_rag.yaml")

# Load all RAG configs
all_rags = ConfigLoader.load_all_rag_configs("configs/rags")
```

---

**Last Updated**: 2024