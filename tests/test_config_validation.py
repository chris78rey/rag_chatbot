"""
Configuration Validation Tests

Tests for ClientConfig and RagConfig Pydantic models.
Tests both valid and invalid configurations.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from pydantic import ValidationError
from services.api.config.models import ClientConfig, RagConfig
from services.api.config.loader import ConfigLoader


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_client_config_dict():
    """Valid client configuration dictionary."""
    return {
        "app": {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "INFO",
            "environment": "development",
            "name": "Test Chatbot",
        },
        "qdrant": {
            "url": "http://qdrant:6333",
            "api_key": None,
            "timeout_s": 30,
            "max_retries": 3,
        },
        "redis": {
            "url": "redis://redis:6379/0",
            "password": None,
            "db": 0,
            "timeout_s": 10,
            "max_pool_size": 20,
        },
        "llm": {
            "provider": "openrouter",
            "api_key_env_var": "OPENROUTER_API_KEY",
            "default_model": "meta-llama/llama-2-70b-chat",
            "fallback_model": "gpt-3.5-turbo",
            "timeout_s": 60,
            "max_retries": 2,
            "max_tokens_default": 1024,
        },
        "paths": {
            "sources_root": "/app/data/sources",
            "rags_config_dir": "/app/configs/rags",
            "logs_dir": "/app/logs",
            "templates_dir": "/app/configs/templates",
        },
        "concurrency": {
            "global_max_inflight_requests": 100,
            "global_rate_limit": 1000,
            "request_timeout_s": 120,
        },
        "security": {
            "behind_nginx": True,
            "trusted_proxies": ["127.0.0.1", "nginx"],
            "cors_origins": ["http://localhost:3000"],
            "require_api_key": False,
            "api_key_header": "X-API-Key",
        },
        "cache": {
            "enabled": True,
            "ttl_seconds": 3600,
            "backend": "redis",
        },
        "sessions": {
            "enabled": True,
            "ttl_seconds": 86400,
            "max_history_turns": 10,
        },
        "monitoring": {
            "enable_metrics": True,
            "enable_tracing": False,
            "trace_sample_rate": 0.1,
        },
        "error_handling": {
            "return_stack_traces": False,
            "log_full_errors": True,
            "default_error_message": "An error occurred.",
        },
    }


@pytest.fixture
def valid_rag_config_dict():
    """Valid RAG configuration dictionary."""
    return {
        "rag_id": "test_rag",
        "display_name": "Test RAG",
        "description": "Test RAG for unit tests",
        "collection": {
            "name": "test_rag_docs",
            "recreation_policy": "skip",
            "shard_number": 1,
        },
        "embeddings": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "batch_size": 32,
            "normalize": True,
        },
        "chunking": {
            "splitter": "recursive_character",
            "chunk_size": 512,
            "chunk_overlap": 128,
            "separator": "\n\n",
            "secondary_separators": ["\n", " ", ""],
        },
        "retrieval": {
            "top_k": 5,
            "score_threshold": 0.5,
            "max_context_chunks": 10,
            "rerank": False,
            "filter_duplicates": True,
        },
        "prompting": {
            "system_template_path": "/app/configs/templates/system_prompt.txt",
            "user_template_path": "/app/configs/templates/user_prompt.txt",
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        "rate_limit": {
            "requests_per_second": 10,
            "burst_size": 20,
            "per_user": False,
        },
        "errors": {
            "no_context_message": "No information found.",
            "provider_error_message": "LLM service unavailable.",
            "timeout_message": "Request timed out.",
            "rate_limit_message": "Too many requests.",
        },
        "cache": {
            "enabled": True,
            "ttl_seconds": 3600,
            "key_prefix": "test_rag",
        },
        "sessions": {
            "enabled": True,
            "history_turns": 5,
            "ttl_seconds": 3600,
            "deduplicate_history": True,
        },
        "sources": {
            "directory": "test_rag_sources",
            "allowed_extensions": [".pdf", ".txt", ".md"],
            "max_file_size_mb": 50,
            "auto_reload": True,
        },
        "metadata": {
            "extract_title": True,
            "extract_date": True,
            "custom_fields": [],
        },
        "security": {
            "public": True,
            "allowed_users": [],
            "require_consent": False,
        },
        "monitoring": {
            "log_queries": True,
            "log_responses": False,
            "collect_metrics": True,
            "alert_on_error": True,
        },
        "experimental": {
            "enable_reranking": False,
            "enable_hyde": False,
            "enable_query_expansion": False,
        },
    }


# ============================================================================
# CLIENT CONFIG TESTS
# ============================================================================

class TestClientConfigValid:
    """Tests for valid client configurations."""
    
    def test_valid_client_config(self, valid_client_config_dict):
        """Test loading a valid client configuration."""
        config = ClientConfig(**valid_client_config_dict)
        assert config.app.host == "0.0.0.0"
        assert config.app.port == 8000
        assert config.qdrant.url == "http://qdrant:6333"
        assert config.redis.url == "redis://redis:6379/0"
    
    def test_client_config_defaults(self):
        """Test client config with minimal fields."""
        config_dict = {
            "qdrant": {
                "url": "http://qdrant:6333",
            },
            "redis": {
                "url": "redis://redis:6379/0",
            },
            "llm": {
                "default_model": "test-model",
            },
        }
        config = ClientConfig(**config_dict)
        assert config.app.port == 8000  # Default
        assert config.cache.enabled is True  # Default


class TestClientConfigInvalid:
    """Tests for invalid client configurations."""
    
    def test_missing_required_fields(self, valid_client_config_dict):
        """Test that missing required fields fail validation."""
        del valid_client_config_dict["qdrant"]
        with pytest.raises(ValidationError):
            ClientConfig(**valid_client_config_dict)
    
    def test_invalid_url(self, valid_client_config_dict):
        """Test that invalid URLs fail validation."""
        valid_client_config_dict["qdrant"]["url"] = "invalid-url"
        with pytest.raises(ValidationError):
            ClientConfig(**valid_client_config_dict)
    
    def test_invalid_log_level(self, valid_client_config_dict):
        """Test that invalid log level fails validation."""
        valid_client_config_dict["app"]["log_level"] = "INVALID"
        with pytest.raises(ValidationError):
            ClientConfig(**valid_client_config_dict)
    
    def test_invalid_port(self, valid_client_config_dict):
        """Test that invalid port fails validation."""
        valid_client_config_dict["app"]["port"] = 99999  # Out of range
        with pytest.raises(ValidationError):
            ClientConfig(**valid_client_config_dict)
    
    def test_extra_fields_not_allowed(self, valid_client_config_dict):
        """Test that extra fields are rejected."""
        valid_client_config_dict["invalid_field"] = "value"
        with pytest.raises(ValidationError):
            ClientConfig(**valid_client_config_dict)


# ============================================================================
# RAG CONFIG TESTS
# ============================================================================

class TestRagConfigValid:
    """Tests for valid RAG configurations."""
    
    def test_valid_rag_config(self, valid_rag_config_dict):
        """Test loading a valid RAG configuration."""
        config = RagConfig(**valid_rag_config_dict)
        assert config.rag_id == "test_rag"
        assert config.display_name == "Test RAG"
        assert config.collection.name == "test_rag_docs"
    
    def test_rag_id_alphanumeric(self, valid_rag_config_dict):
        """Test that rag_id accepts alphanumeric and underscores."""
        valid_rag_config_dict["rag_id"] = "valid_rag_123"
        config = RagConfig(**valid_rag_config_dict)
        assert config.rag_id == "valid_rag_123"


class TestRagConfigInvalid:
    """Tests for invalid RAG configurations."""
    
    def test_missing_rag_id(self, valid_rag_config_dict):
        """Test that missing rag_id fails validation."""
        del valid_rag_config_dict["rag_id"]
        with pytest.raises(ValidationError):
            RagConfig(**valid_rag_config_dict)
    
    def test_invalid_rag_id(self, valid_rag_config_dict):
        """Test that invalid rag_id (with special chars) fails."""
        valid_rag_config_dict["rag_id"] = "invalid-rag-id"  # Hyphens not allowed
        with pytest.raises(ValidationError):
            RagConfig(**valid_rag_config_dict)
    
    def test_chunk_overlap_exceeds_chunk_size(self, valid_rag_config_dict):
        """Test that chunk_overlap >= chunk_size fails."""
        valid_rag_config_dict["chunking"]["chunk_overlap"] = 600
        valid_rag_config_dict["chunking"]["chunk_size"] = 512
        with pytest.raises(ValidationError):
            RagConfig(**valid_rag_config_dict)
    
    def test_invalid_extension_format(self, valid_rag_config_dict):
        """Test that extensions must start with a dot."""
        valid_rag_config_dict["sources"]["allowed_extensions"] = ["pdf"]  # Missing dot
        with pytest.raises(ValidationError):
            RagConfig(**valid_rag_config_dict)
    
    def test_invalid_temperature(self, valid_rag_config_dict):
        """Test that temperature must be in valid range."""
        valid_rag_config_dict["prompting"]["temperature"] = 3.0  # > 2.0
        with pytest.raises(ValidationError):
            RagConfig(**valid_rag_config_dict)


# ============================================================================
# CONFIG LOADER TESTS
# ============================================================================

class TestConfigLoader:
    """Tests for ConfigLoader utility."""
    
    def test_load_client_config_from_file(self, valid_client_config_dict):
        """Test loading client config from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_client_config_dict, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_client_config(temp_path)
            assert config.app.port == 8000
        finally:
            Path(temp_path).unlink()
    
    def test_load_rag_config_from_file(self, valid_rag_config_dict):
        """Test loading RAG config from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_rag_config_dict, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_rag_config(temp_path)
            assert config.rag_id == "test_rag"
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_client_config("/nonexistent/path/config.yaml")
    
    def test_load_invalid_yaml(self):
        """Test that invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: {")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ConfigLoader.load_client_config(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_file(self):
        """Test that empty YAML file raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ConfigLoader.load_client_config(temp_path)
        finally:
            Path(temp_path).unlink()