"""
Pydantic models for RAF Chatbot configuration validation.

This module defines the schemas for:
- ClientConfig: Global application settings
- RagConfig: Per-RAG settings
- All nested models for subsections (qdrant, redis, llm, etc.)

Each model includes field validation, defaults, and documentation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re


# ============================================================================
# NESTED MODELS - Client Configuration
# ============================================================================

class AppSettings(BaseModel):
    """Application-level settings."""
    model_config = ConfigDict(extra="allow")
    
    host: str = Field(default="0.0.0.0", description="Listen on all interfaces")
    port: int = Field(default=8000, ge=1, le=65535, description="FastAPI server port")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    name: str = Field(default="RAF Chatbot", description="Display name")


class QdrantSettings(BaseModel):
    """Qdrant vector database configuration."""
    model_config = ConfigDict(extra="allow")
    
    url: str = Field(..., description="Connection URL")
    api_key: Optional[str] = Field(default=None, description="Optional API key")
    timeout_s: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Retry attempts")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class RedisSettings(BaseModel):
    """Redis cache & queue configuration."""
    model_config = ConfigDict(extra="allow")
    
    url: str = Field(..., description="Connection URL (e.g., redis://redis:6379/0)")
    password: Optional[str] = Field(default=None, description="Optional password")
    db: int = Field(default=0, ge=0, le=15, description="Database index")
    timeout_s: int = Field(default=10, ge=1, le=60, description="Timeout in seconds")
    max_pool_size: int = Field(default=20, ge=1, le=100, description="Pool size")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError("URL must start with redis:// or rediss://")
        return v


class LlmSettings(BaseModel):
    """LLM configuration."""
    model_config = ConfigDict(extra="allow")
    
    provider: str = Field(default="openrouter", description="LLM provider")
    api_key_env_var: str = Field(default="OPENROUTER_API_KEY", description="Env var for API key")
    default_model: str = Field(..., description="Default model name")
    fallback_model: Optional[str] = Field(default=None, description="Fallback model")
    timeout_s: int = Field(default=60, ge=1, le=300, description="Request timeout")
    max_retries: int = Field(default=2, ge=0, le=10, description="Retry attempts")
    max_tokens_default: int = Field(default=1024, ge=1, le=32000, description="Default max tokens")


class PathSettings(BaseModel):
    """Filesystem paths configuration."""
    model_config = ConfigDict(extra="allow")
    
    sources_root: str = Field(default="/app/data/sources", description="Root for RAG sources")
    rags_config_dir: str = Field(default="/app/configs/rags", description="RAG configs directory")
    logs_dir: str = Field(default="/app/logs", description="Logs directory")
    templates_dir: str = Field(default="/app/configs/templates", description="Templates directory")


class ConcurrencySettings(BaseModel):
    """Concurrency and rate limiting."""
    model_config = ConfigDict(extra="allow")
    
    global_max_inflight_requests: int = Field(
        default=100, ge=1, le=10000, description="Max concurrent requests"
    )
    global_rate_limit: int = Field(
        default=1000, ge=1, le=100000, description="Requests per second"
    )
    request_timeout_s: int = Field(
        default=120, ge=1, le=600, description="Request timeout"
    )


class SecuritySettings(BaseModel):
    """Security configuration."""
    model_config = ConfigDict(extra="allow")
    
    behind_nginx: bool = Field(default=True, description="Behind reverse proxy?")
    trusted_proxies: List[str] = Field(default=["127.0.0.1"], description="Trusted IP addresses")
    cors_origins: List[str] = Field(default=[], description="CORS allowed origins")
    require_api_key: bool = Field(default=False, description="Require API key?")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")


class CacheSettings(BaseModel):
    """Cache configuration."""
    model_config = ConfigDict(extra="allow")
    
    enabled: bool = Field(default=True, description="Cache enabled?")
    ttl_seconds: int = Field(default=3600, ge=1, le=86400, description="Cache TTL")
    backend: Literal["redis", "memory"] = Field(default="redis", description="Cache backend")


class SessionSettings(BaseModel):
    """Session configuration."""
    model_config = ConfigDict(extra="allow")
    
    enabled: bool = Field(default=True, description="Sessions enabled?")
    ttl_seconds: int = Field(default=86400, ge=1, le=2592000, description="Session TTL")
    max_history_turns: int = Field(default=10, ge=1, le=100, description="Max conversation turns")


class MonitoringSettings(BaseModel):
    """Monitoring configuration."""
    model_config = ConfigDict(extra="allow")
    
    enable_metrics: bool = Field(default=True, description="Enable metrics?")
    enable_tracing: bool = Field(default=False, description="Enable tracing?")
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Trace sample rate")


class ErrorHandlingSettings(BaseModel):
    """Error handling configuration."""
    model_config = ConfigDict(extra="allow")
    
    return_stack_traces: bool = Field(default=False, description="Return stack traces?")
    log_full_errors: bool = Field(default=True, description="Log full errors?")
    default_error_message: str = Field(
        default="An error occurred. Please try again.",
        description="Default error message"
    )


class ClientConfig(BaseModel):
    """Global client configuration."""
    model_config = ConfigDict(extra="allow")
    
    app: AppSettings = Field(default_factory=AppSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    concurrency: ConcurrencySettings = Field(default_factory=ConcurrencySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    sessions: SessionSettings = Field(default_factory=SessionSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    error_handling: ErrorHandlingSettings = Field(default_factory=ErrorHandlingSettings)


# ============================================================================
# NESTED MODELS - RAG Configuration
# ============================================================================

class RAGCollection(BaseModel):
    """Collection settings."""
    model_config = ConfigDict(extra="allow")
    
    name: str = Field(..., description="Qdrant collection name")
    vector_size: int = Field(default=384, ge=64, le=4096, description="Vector dimension")
    distance: Literal["cosine", "euclidean", "manhattan"] = Field(default="cosine", description="Distance metric")


class EmbeddingsSettings(BaseModel):
    """Embeddings configuration."""
    model_config = ConfigDict(extra="allow")
    
    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Model name")
    dimension: int = Field(default=384, ge=64, le=4096, description="Vector dimension")
    batch_size: int = Field(default=32, ge=1, le=512, description="Batch size")
    normalize: bool = Field(default=True, description="L2 normalize?")


class ChunkingSettings(BaseModel):
    """Document chunking configuration."""
    model_config = ConfigDict(extra="allow")
    
    splitter: Literal["recursive_character", "semantic"] = Field(
        default="recursive_character", description="Splitter type"
    )
    chunk_size: int = Field(default=512, ge=64, le=4096, description="Chunk size in chars")
    chunk_overlap: int = Field(default=128, ge=0, le=1024, description="Overlap in chars")
    separator: str = Field(default="\n\n", description="Primary separator")
    secondary_separators: List[str] = Field(
        default=["\n", " ", ""], description="Fallback separators"
    )

    @model_validator(mode='after')
    def validate_chunk_settings(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return self


class RetrievalSettings(BaseModel):
    """Retrieval settings."""
    model_config = ConfigDict(extra="allow")
    
    top_k: int = Field(default=5, ge=1, le=50, description="Top K results")
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Score threshold")
    max_context_chunks: int = Field(default=10, ge=1, le=100, description="Max chunks")
    rerank: bool = Field(default=False, description="Enable reranking?")
    filter_duplicates: bool = Field(default=True, description="Filter duplicates?")


class PromptingSettings(BaseModel):
    """Prompting configuration."""
    model_config = ConfigDict(extra="allow")
    
    system_template_path: str = Field(..., description="System prompt template path")
    user_template_path: str = Field(..., description="User prompt template path")
    max_tokens: int = Field(default=1024, ge=1, le=32000, description="Max tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top P")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")


class RateLimitSettings(BaseModel):
    """Rate limiting per RAG."""
    model_config = ConfigDict(extra="allow")
    
    requests_per_second: int = Field(default=10, ge=1, le=1000, description="Requests/sec")
    burst_size: int = Field(default=20, ge=1, le=10000, description="Burst size")
    per_user: bool = Field(default=False, description="Per-user limits?")


class ErrorMessagesSettings(BaseModel):
    """Error messages configuration."""
    model_config = ConfigDict(extra="allow")
    
    no_context_message: str = Field(
        default="No relevant information found for your query.",
        description="No context message"
    )
    provider_error_message: str = Field(
        default="The LLM service is temporarily unavailable.",
        description="Provider error message"
    )
    timeout_message: str = Field(
        default="Request timed out. Please try again.",
        description="Timeout message"
    )
    rate_limit_message: str = Field(
        default="Too many requests. Please try again later.",
        description="Rate limit message"
    )


class RAGCacheSettings(BaseModel):
    """Per-RAG cache configuration."""
    model_config = ConfigDict(extra="allow")
    
    enabled: bool = Field(default=True, description="Cache enabled?")
    ttl_seconds: int = Field(default=3600, ge=1, le=86400, description="Cache TTL")


class RAGSessionSettings(BaseModel):
    """Per-RAG session configuration."""
    model_config = ConfigDict(extra="allow")
    
    enabled: bool = Field(default=True, description="Sessions enabled?")
    ttl_seconds: int = Field(default=86400, ge=1, le=2592000, description="Session TTL")
    max_history_turns: int = Field(default=10, ge=1, le=100, description="Max conversation turns")


class SourcesSettings(BaseModel):
    """Sources configuration."""
    model_config = ConfigDict(extra="allow")
    
    directory: str = Field(..., description="Source directory path")
    extensions: List[str] = Field(default=[".txt", ".pdf", ".md"], description="Allowed extensions")
    recursive: bool = Field(default=True, description="Recursive search?")
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, description="Max file size")

    @field_validator('extensions')
    @classmethod
    def validate_extensions(cls, v):
        for ext in v:
            if not ext.startswith('.'):
                raise ValueError(f"Extension must start with '.': {ext}")
        return v


class MetadataSettings(BaseModel):
    """Metadata configuration."""
    model_config = ConfigDict(extra="allow")
    
    extract: bool = Field(default=True, description="Extract metadata?")
    fields: List[str] = Field(default=["title", "author", "date"], description="Metadata fields")
    required_fields: List[str] = Field(default=[], description="Required fields")


class RAGSecuritySettings(BaseModel):
    """Per-RAG security configuration."""
    model_config = ConfigDict(extra="allow")
    
    public: bool = Field(default=False, description="Public RAG?")
    allowed_users: List[str] = Field(default=[], description="Allowed users")
    require_api_key: bool = Field(default=False, description="Require API key?")


class RAGMonitoringSettings(BaseModel):
    """Per-RAG monitoring configuration."""
    model_config = ConfigDict(extra="allow")
    
    enable_metrics: bool = Field(default=True, description="Enable metrics?")
    enable_tracing: bool = Field(default=False, description="Enable tracing?")
    log_queries: bool = Field(default=True, description="Log queries?")
    log_responses: bool = Field(default=False, description="Log responses?")


class ExperimentalSettings(BaseModel):
    """Experimental features."""
    model_config = ConfigDict(extra="allow")
    
    enable_reranking: bool = Field(default=False, description="Enable reranking?")
    enable_hyde: bool = Field(default=False, description="Enable HyDE?")
    enable_fusion: bool = Field(default=False, description="Enable fusion?")


class RagConfig(BaseModel):
    """RAG-specific configuration."""
    model_config = ConfigDict(extra="allow")
    
    rag_id: str = Field(..., description="RAG identifier (alphanumeric + underscore)")
    display_name: str = Field(..., description="Display name")
    description: str = Field(default="", description="RAG description")
    
    collection: RAGCollection = Field(..., description="Collection settings")
    embeddings: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    prompting: PromptingSettings = Field(..., description="Prompting settings")
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    error_messages: ErrorMessagesSettings = Field(default_factory=ErrorMessagesSettings)
    cache: RAGCacheSettings = Field(default_factory=RAGCacheSettings)
    sessions: RAGSessionSettings = Field(default_factory=RAGSessionSettings)
    sources: SourcesSettings = Field(..., description="Sources settings")
    metadata: MetadataSettings = Field(default_factory=MetadataSettings)
    security: RAGSecuritySettings = Field(default_factory=RAGSecuritySettings)
    monitoring: RAGMonitoringSettings = Field(default_factory=RAGMonitoringSettings)
    experimental: ExperimentalSettings = Field(default_factory=ExperimentalSettings)

    @field_validator('rag_id')
    @classmethod
    def validate_rag_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("rag_id must be alphanumeric with underscores only")
        return v