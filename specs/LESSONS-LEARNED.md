# RAF Chatbot — Lessons Learned Documentation

**Document Version**: 1.0  
**Date**: 2025-01-09  
**Scope**: Subprojects 1-6 (Foundation through Embedding Service)

---

## 📚 Table of Contents

1. [Lesson 1: Pydantic Version Compatibility](#lesson-1-pydantic-version-compatibility)
2. [Lesson 2: Docker Networking in Development](#lesson-2-docker-networking-in-development)
3. [Lesson 3: Configuration Validation Strategy](#lesson-3-configuration-validation-strategy)
4. [Lesson 4: API Key Management Pattern](#lesson-4-api-key-management-pattern)
5. [Lesson 5: Testing Without External Dependencies](#lesson-5-testing-without-external-dependencies)
6. [Prevention Checklist](#prevention-checklist)

---

## Lesson 1: Pydantic Version Compatibility

### 🔴 Problem
Existing Pydantic v1 code (`@validator`, `@root_validator`, `class Config`) failed with Pydantic v2 due to breaking API changes.

**Error Encountered**:
```
pydantic.errors.PydanticUserError: If you use `@root_validator` with pre=False 
(the default) you MUST specify `skip_on_failure=True`.
```

### 🔍 Root Cause
- Pydantic v2 is **not backward compatible** with v1 syntax
- Migration guide not followed during implementation
- No version pinning in requirements (let pip choose latest)
- Assumptions about decorator behavior changed

### ✅ Solution Implemented

**Before (Pydantic v1)**:
```python
from pydantic import BaseModel, validator, root_validator

class Model(BaseModel):
    value: int
    
    @validator('value')
    def check_value(cls, v):
        return v
    
    @root_validator()
    def check_model(cls, values):
        return values
    
    class Config:
        extra = "forbid"
```

**After (Pydantic v2)**:
```python
from pydantic import BaseModel, field_validator, model_validator, ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    value: int
    
    @field_validator('value')
    @classmethod
    def check_value(cls, v):
        return v
    
    @model_validator(mode='after')
    def check_model(self):
        return self
```

### 🎯 Key Changes

| Pydantic v1 | Pydantic v2 | Notes |
|-----------|-----------|-------|
| `@validator()` | `@field_validator()` + `@classmethod` | Field-level validation |
| `@root_validator()` | `@model_validator(mode='after')` | Model-level validation |
| `class Config:` | `model_config = ConfigDict()` | Configuration |
| `extra = "forbid"` | `ConfigDict(extra="forbid")` | Extra fields handling |

### 📋 Preventive Principle

**"Always pin exact versions for framework dependencies, especially Pydantic"**

### 🚨 Activation Signal

- Installation fails with `PydanticUserError`
- Syntax like `@root_validator()` appears in codebase
- `class Config:` inside model definitions
- Error mentions "deprecated" and "pydantic v2"

### 💾 Reusable Snippet

```python
# utility/pydantic_helpers.py
"""Helper utilities for Pydantic v2 models."""

from typing import Type, TypeVar, Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

T = TypeVar('T', bound=BaseModel)

def create_strict_model(
    name: str,
    fields: dict[str, tuple[type, Any]],
    extra: str = "forbid"
) -> Type[BaseModel]:
    """
    Factory function to create strict Pydantic v2 models.
    
    Args:
        name: Model class name
        fields: Dict of field_name -> (type, default_value)
        extra: Extra fields handling ('forbid', 'allow', 'ignore')
    
    Returns:
        Dynamically created BaseModel subclass
    
    Example:
        StrictModel = create_strict_model(
            "StrictModel",
            {
                "url": (str, ...),
                "timeout": (int, 30),
            },
            extra="forbid"
        )
        
        m = StrictModel(url="http://example.com")
    """
    field_definitions = {}
    for fname, (ftype, default) in fields.items():
        from pydantic import Field
        if default is ...:
            field_definitions[fname] = (ftype, Field(...))
        else:
            field_definitions[fname] = (ftype, Field(default=default))
    
    return type(name, (BaseModel,), {
        '__annotations__': {k: v[0] for k, v in fields.items()},
        **{k: v[1] for k, v in field_definitions.items()},
        'model_config': ConfigDict(extra=extra)
    })


def validate_model_with_feedback(
    model_class: Type[T],
    data: dict,
    context: str = ""
) -> tuple[T | None, str]:
    """
    Validate data against model with detailed error messages.
    
    Args:
        model_class: Pydantic model to validate against
        data: Data dictionary to validate
        context: Optional context string for error messages
    
    Returns:
        Tuple of (validated_instance or None, error_message or "OK")
    
    Example:
        config, error = validate_model_with_feedback(
            ClientConfig,
            yaml_data,
            context="Loading client.yaml"
        )
        if error != "OK":
            print(f"Validation failed: {error}")
    """
    try:
        instance = model_class(**data)
        return instance, "OK"
    except Exception as e:
        msg = f"Validation error"
        if context:
            msg += f" ({context})"
        msg += f": {str(e)}"
        return None, msg
```

### 📖 Migration Checklist

- [ ] Check current Pydantic version: `pip show pydantic`
- [ ] If v2+, look for `class Config:` blocks and convert to `model_config = ConfigDict()`
- [ ] Look for `@validator` decorators and convert to `@field_validator`
- [ ] Look for `@root_validator` and convert to `@model_validator(mode='after')`
- [ ] Add `@classmethod` decorator to field validators
- [ ] Update import statements
- [ ] Run tests: `pytest -v`
- [ ] Pin version in requirements.txt: `pydantic==2.10.0`

---

## Lesson 2: Docker Networking in Development

### 🔴 Problem
Tests failed when trying to connect to Docker services (Qdrant, Redis) using hostnames like `http://qdrant:6333` and `redis://localhost:6379` from the host machine.

**Error Encountered**:
```
Cannot reach Qdrant at localhost:6333
Error 11001 connecting to redis:6379. getaddrinfo failed
```

### 🔍 Root Cause
- **Container hostnames** (`qdrant`, `redis`) only resolve **inside the Docker network**
- **Host machine** cannot resolve container service names directly
- Ports must be **explicitly exposed** in docker-compose with `ports:` mapping
- Mismatch between **internal Docker DNS** and **host DNS resolution**

### ✅ Solution Implemented

**Before (Failed)**:
```yaml
# docker-compose.yml (broken)
services:
  qdrant:
    image: qdrant/qdrant:latest
    # No ports mapping - not exposed to host!
  
  redis:
    image: redis:7-alpine
    # No ports mapping!
```

**After (Working)**:
```yaml
# docker-compose.yml (fixed)
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"    # HOST:CONTAINER
      - "6334:6334"
    networks:
      - app_network    # Internal network for container-to-container

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

### 🎯 Key Insight

There are **two different connection strings** to use:

| Context | URL | Use Case |
|---------|-----|----------|
| **Inside Docker** | `http://qdrant:6333` | Container-to-container communication |
| **From Host** | `http://localhost:6333` | Local machine testing |
| **From Outside** | `http://<machine-ip>:6333` | Remote machine (production) |

### 📋 Preventive Principle

**"Always expose Docker ports for services you need to test locally, and maintain dual configuration (Docker DNS + localhost)"**

### 🚨 Activation Signal

- Connection timeouts to service hostnames
- Error: `getaddrinfo failed` for service names
- Services work inside containers but not from host
- Config has hardcoded `http://service-name:port`

### 💾 Reusable Snippet

```python
# config/connection.py
"""Smart connection string resolver for Docker/local environments."""

import os
from enum import Enum

class Environment(Enum):
    DOCKER = "docker"      # Inside Docker container
    LOCAL = "local"        # Host machine (development)
    PRODUCTION = "prod"    # Remote deployment

class ServiceLocator:
    """Resolve service URLs based on environment."""
    
    # Service definitions: (docker_host, local_host, default_port)
    SERVICES = {
        "qdrant": ("qdrant", "localhost", 6333),
        "redis": ("redis", "localhost", 6379),
        "api": ("api", "localhost", 8000),
    }
    
    def __init__(self, env: Environment | None = None):
        """Initialize with auto-detection if env not provided."""
        self.env = env or self._detect_environment()
    
    @staticmethod
    def _detect_environment() -> Environment:
        """Auto-detect environment from Docker container state."""
        # If DOCKER_HOST is set, we're likely in Docker
        if os.environ.get('DOCKER_HOST'):
            return Environment.DOCKER
        
        # If /.dockerenv exists, we're in a container
        if os.path.exists('/.dockerenv'):
            return Environment.DOCKER
        
        return Environment.LOCAL
    
    def get_url(
        self,
        service: str,
        protocol: str = "http",
        path: str = ""
    ) -> str:
        """
        Get service URL for current environment.
        
        Args:
            service: Service name ('qdrant', 'redis', etc.)
            protocol: Protocol prefix ('http', 'redis', 'postgresql')
            path: Optional path suffix
        
        Returns:
            Full service URL
        
        Example:
            locator = ServiceLocator()
            qdrant_url = locator.get_url("qdrant", "http")
            # Returns "http://localhost:6333" on local
            # Returns "http://qdrant:6333" in Docker
        """
        if service not in self.SERVICES:
            raise ValueError(f"Unknown service: {service}")
        
        docker_host, local_host, port = self.SERVICES[service]
        host = docker_host if self.env == Environment.DOCKER else local_host
        
        # Handle protocol-specific defaults
        if service == "redis" and protocol == "redis":
            url = f"{protocol}://{host}:{port}/0"
        else:
            url = f"{protocol}://{host}:{port}"
        
        if path:
            url += path
        
        return url
    
    @classmethod
    def get_qdrant_url(cls) -> str:
        """Convenience method for Qdrant URL."""
        return cls().get_url("qdrant", "http")
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Convenience method for Redis URL."""
        return cls().get_url("redis", "redis")


# Usage example:
# locator = ServiceLocator()
# qdrant_url = locator.get_url("qdrant")
# redis_url = locator.get_url("redis", "redis")
```

### ✅ Docker Compose Template

```yaml
# deploy/compose/docker-compose.yml (best practices)
version: "3.8"

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: raf_qdrant
    ports:
      - "6333:6333"    # Host:Container - essential for local testing
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - app_network
    environment:
      - QDRANT_API_KEY=${QDRANT_API_KEY:-}  # Empty = no auth in dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 5s
      timeout: 3s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: raf_redis
    ports:
      - "6379:6379"    # Host:Container - essential for local testing
    volumes:
      - redis_storage:/data
    networks:
      - app_network
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

volumes:
  qdrant_storage:
  redis_storage:

networks:
  app_network:
    driver: bridge
```

---

## Lesson 3: Configuration Validation Strategy

### 🔴 Problem
Configuration errors discovered at runtime (missing fields, wrong types, invalid values) rather than at startup. Hard to debug due to silent failures or cryptic error messages.

### 🔍 Root Cause
- No schema validation for YAML configs
- Type hints only in code, not enforced
- Error messages from missing fields were generic
- No separation between defaults and required fields

### ✅ Solution Implemented

**Strategy: Pydantic-based strict validation with helpful error messages**

```python
# services/api/config/models.py (excerpt)

from pydantic import BaseModel, Field, field_validator, ConfigDict

class QdrantSettings(BaseModel):
    """Qdrant configuration with validation."""
    model_config = ConfigDict(extra="allow")  # Allow future fields
    
    url: str = Field(
        ...,  # Required field
        description="Qdrant connection URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Optional API key for auth"
    )
    timeout_s: int = Field(
        default=30,
        ge=1,      # Greater than or equal
        le=300,    # Less than or equal
        description="Timeout in seconds (1-300)"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Ensure URL starts with http:// or https://."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(
                "URL must start with http:// or https:// "
                f"(got: {v})"
            )
        return v
```

**Benefits**:
- ✅ Type safety (int, str, List, etc.)
- ✅ Range validation (ge, le, min_length)
- ✅ Format validation (regex, URL, email)
- ✅ Custom validation (business logic)
- ✅ Clear error messages
- ✅ IDE autocomplete support

### 📋 Preventive Principle

**"Validate configuration at load time with clear schemas, not at runtime with guesses"**

### 🚨 Activation Signal

- Config errors discovered late (production)
- Vague error messages: "KeyError: 'qdrant_url'"
- Type mismatches: treating strings as integers
- Missing required fields not caught early

### 💾 Reusable Pattern

```python
# config/validation.py
"""Reusable configuration validation pattern."""

from typing import TypeVar, Type, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

class ConfigValidator:
    """Validates configuration files with helpful error messages."""
    
    @staticmethod
    def load_yaml(path: Path | str) -> dict:
        """Load YAML file with error handling."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {path.absolute()}\n"
                f"Expected one of:\n"
                f"  - {path.resolve()}\n"
                f"  - {Path.cwd() / path}"
            )
        
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ValueError(f"Config file is empty: {path}")
            
            return data
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML syntax in {path}:\n{e}"
            ) from e
    
    @staticmethod
    def validate(
        model: Type[T],
        data: dict,
        context: str = ""
    ) -> T:
        """
        Validate data against model with detailed feedback.
        
        Args:
            model: Pydantic model class
            data: Data dictionary to validate
            context: Context for error messages
        
        Returns:
            Validated model instance
        
        Raises:
            ValidationError with detailed field-level errors
        
        Example:
            config = ConfigValidator.validate(
                ClientConfig,
                yaml_data,
                context="Loading client.yaml"
            )
        """
        try:
            return model(**data)
        except ValidationError as e:
            error_lines = [f"\n❌ Config validation failed"]
            if context:
                error_lines.append(f"   Context: {context}")
            
            for error in e.errors():
                field_path = ".".join(str(x) for x in error['loc'])
                msg = error['msg']
                error_lines.append(f"   - {field_path}: {msg}")
            
            raise ValidationError("\n".join(error_lines)) from e
    
    @classmethod
    def load_and_validate(
        cls,
        model: Type[T],
        path: Path | str,
        context: str = ""
    ) -> T:
        """
        Load YAML file and validate against model in one step.
        
        Example:
            config = ConfigValidator.load_and_validate(
                RagConfig,
                "configs/rags/my_rag.yaml"
            )
        """
        data = cls.load_yaml(path)
        return cls.validate(model, data, context or f"Loading {Path(path).name}")
```

### ✅ Test Pattern

```python
# tests/test_config_validation.py (excerpt)

import pytest
from pydantic import ValidationError
from config.models import QdrantSettings

class TestQdrantConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config(self):
        """Happy path: valid configuration."""
        config = QdrantSettings(
            url="http://qdrant:6333",
            timeout_s=30
        )
        assert config.url == "http://qdrant:6333"
        assert config.timeout_s == 30
    
    def test_invalid_url_protocol(self):
        """Sad path: invalid URL protocol."""
        with pytest.raises(ValidationError) as exc:
            QdrantSettings(url="ftp://qdrant:6333")
        
        assert "http://" in str(exc.value)
    
    def test_timeout_out_of_range(self):
        """Sad path: timeout exceeds maximum."""
        with pytest.raises(ValidationError) as exc:
            QdrantSettings(
                url="http://qdrant:6333",
                timeout_s=999  # Exceeds le=300
            )
        
        assert "less than or equal to 300" in str(exc.value)
    
    def test_missing_required_field(self):
        """Sad path: missing required field."""
        with pytest.raises(ValidationError) as exc:
            QdrantSettings()  # Missing url
        
        assert "Field required" in str(exc.value)
```

---

## Lesson 4: API Key Management Pattern

### 🔴 Problem
API keys scattered across:
- Hardcoded in config files (security risk)
- Different formats in different projects
- No consistent pattern for optional vs. required
- Environment variables not documented

### 🔍 Root Cause
- No explicit strategy for secret management
- Treating API keys same as regular config
- No distinction between dev/staging/prod secrets
- Git could accidentally commit sensitive data

### ✅ Solution Implemented

**Strategy: Environment variables + defaults for development**

```yaml
# configs/client/client.yaml.example (safe to commit)

llm:
  provider: "openrouter"
  api_key_env_var: "OPENROUTER_API_KEY"  # ← Where to look for secret
  default_model: "meta-llama/llama-2-70b-chat"
  timeout_s: 60

qdrant:
  url: "http://qdrant:6333"
  api_key: null  # Development: no auth. Use env var in production
  timeout_s: 30

redis:
  url: "redis://redis:6379/0"
  password: null  # Development: no password. Use env var in production
```

**Implementation**:
```python
# services/config/secrets.py
"""Secure API key and secret management."""

import os
from typing import Optional
from pydantic import SecretStr, Field

class SecretSettings(BaseModel):
    """Settings that contain secrets (API keys, passwords)."""
    model_config = ConfigDict(extra="forbid")
    
    # API Keys - loaded from environment
    openrouter_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenRouter API key (env: OPENROUTER_API_KEY)"
    )
    
    qdrant_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Qdrant API key (env: QDRANT_API_KEY)"
    )
    
    @classmethod
    def from_environment(cls) -> "SecretSettings":
        """Load secrets from environment variables."""
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        )
    
    def get_key(self, name: str) -> Optional[str]:
        """Get secret by name, returns None if not set."""
        key = getattr(self, name, None)
        return key.get_secret_value() if key else None
```

### 📋 Preventive Principle

**"API keys and passwords NEVER in config files. Always use environment variables with .env files (git-ignored)"**

### 🚨 Activation Signal

- Sensitive data in YAML files
- Hardcoded `api_key: "sk-1234..."`
- No environment variable usage
- `.env` file accidentally committed to git

### 💾 Reusable Pattern

```python
# utils/secrets.py
"""Secure secret management utilities."""

from pathlib import Path
from typing import Optional
import os

class SecretManager:
    """Manage API keys and passwords securely."""
    
    def __init__(self, env_file: Path | str | None = None):
        """Initialize with optional .env file."""
        self.env_file = Path(env_file) if env_file else Path.cwd() / ".env"
        self._loaded = False
    
    def load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            return  # Silently skip if not found
        
        with open(self.env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
        
        self._loaded = True
    
    def get(
        self,
        key: str,
        default: Optional[str] = None,
        required: bool = False
    ) -> Optional[str]:
        """
        Get secret by key with validation.
        
        Args:
            key: Environment variable name
            default: Default if not found
            required: Raise error if missing
        
        Returns:
            Secret value or default
        
        Raises:
            ValueError if required and not found
        """
        if not self._loaded:
            self.load_env_file()
        
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(
                f"Required secret not found: {key}\n"
                f"Set it in environment or in {self.env_file}"
            )
        
        return value
    
    def validate_required_keys(self, *keys: str) -> None:
        """Validate that all required keys are set."""
        missing = []
        
        for key in keys:
            if not self.get(key):
                missing.append(key)
        
        if missing:
            raise ValueError(
                f"Missing required secrets: {', '.join(missing)}\n"
                f"Set them in environment or in {self.env_file}"
            )


# Usage:
# secrets = SecretManager()
# api_key = secrets.get("OPENROUTER_API_KEY", required=True)
```

### ✅ .env Template (git-ignored)

```bash
# .env (DO NOT COMMIT - add to .gitignore)
# Copy from .env.example and fill in your secrets

# LLM Provider
OPENROUTER_API_KEY=sk_openrouter_xxxxx

# Qdrant (production)
QDRANT_API_KEY=your_qdrant_key

# Redis (production)
REDIS_PASSWORD=your_redis_password

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### ✅ .env.example (safe to commit)

```bash
# .env.example
# Copy this file to .env and fill in your actual secrets

# LLM Provider (required for SP8)
OPENROUTER_API_KEY=your_api_key_here

# Qdrant (optional, null in development)
QDRANT_API_KEY=

# Redis (optional, null in development)
REDIS_PASSWORD=

# Database (optional)
DATABASE_URL=
```

---

## Lesson 5: Testing Without External Dependencies

### 🔴 Problem
Tests needed to validate Subprojects 1-6 but required:
- Running Docker services
- External API keys
- Network connectivity
- Complex setup

### 🔍 Root Cause
- No distinction between unit tests (fast, local) and integration tests (slow, external)
- Tests coupled to external service implementation
- No mocking/stubbing strategy
- Test data scattered across multiple locations

### ✅ Solution Implemented

**Strategy: Layered testing approach**

```
Unit Tests (Fast, no dependencies)
  ↓
Integration Tests (Docker, realistic)
  ↓
End-to-End Tests (Full stack, slow)
```

**Implementation**:
```python
# tests/conftest.py (pytest configuration and fixtures)
"""Shared test configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import yaml

@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    config_data = {
        "qdrant": {"url": "http://localhost:6333"},
        "redis": {"url": "redis://localhost:6379"},
    }
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False
    ) as f:
        yaml.dump(config_data, f)
        yield Path(f.name)
        Path(f.name).unlink()  # Cleanup


@pytest.fixture
def mock_embedding_service(monkeypatch):
    """Mock embedding service that doesn't need real models."""
    
    class MockEmbedder:
        def embed(self, text: str) -> list[float]:
            # Return deterministic dummy vector
            return [0.1] * 384  # 384-dimensional vector
        
        def embed_batch(self, texts: list[str]) -> list[list[float]]:
            return [self.embed(t) for t in texts]
    
    mock = MockEmbedder()
    monkeypatch.setattr(
        "services.embed.service.EmbeddingGenerator.embed",
        mock.embed
    )
    return mock


class TestConfigValidationUnit:
    """Unit tests for configuration - no external dependencies."""
    
    def test_valid_qdrant_config(self):
        """Test Qdrant config validation in isolation."""
        from services.api.config.models import QdrantSettings
        
        config = QdrantSettings(
            url="http://qdrant:6333",
            timeout_s=30
        )
        
        assert config.url == "http://qdrant:6333"
        assert config.timeout_s == 30
        assert config.api_key is None
    
    def test_qdrant_config_url_validation(self):
        """Test URL format validation without network."""
        from services.api.config.models import QdrantSettings
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            QdrantSettings(url="invalid-url")  # No protocol


class TestEmbeddingServiceUnit:
    """Unit tests for embedding service - mocked dependencies."""
    
    def test_embedding_generator_with_mock(self, mock_embedding_service):
        """Test embedding generation with mocked model."""
        from services.embed import EmbeddingGenerator
        
        # Uses mocked embedder that returns dummy vectors
        generator = EmbeddingGenerator()
        result = generator.embed_documents(
            documents=[
                Document(doc_id="d1", chunk_id="d1:0", content="test"),
            ],
            rag_config=mock_config
        )
        
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0].vector) == 384


# tests/test_integration.py
class TestIntegrationWithDocker:
    """Integration tests that require Docker services."""
    
    @pytest.mark.requires_docker
    def test_qdrant_connection_real(self):
        """Test real Qdrant connection (requires docker-compose up)."""
        from services.embed import QdrantVectorStore
        
        store = QdrantVectorStore("http://localhost:6333")
        
        # This will fail if Docker not running - that's expected
        # Mark test with @pytest.mark.requires_docker to skip if needed
        info = store.health_check()
        assert info is not None
```

### 📋 Preventive Principle

**"Test in isolation when possible, mock external services, keep integration tests separate"**

### 🚨 Activation Signal

- All tests require Docker running
- Tests fail with network errors in CI/CD
- Test setup takes > 30 seconds
- Can't run tests on airplane or offline

### 💾 Reusable Testing Utilities

```python
# tests/fixtures.py
"""Reusable test fixtures and utilities."""

import pytest
from dataclasses import dataclass
from typing import Optional

@dataclass
class MockConfig:
    """Mock configuration for testing."""
    rag_id: str = "test_rag"
    chunk_size: int = 512
    chunk_overlap: int = 128
    batch_size: int = 32
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimension: int = 384


class MockEmbeddings:
    """Deterministic mock embeddings (same input = same output)."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed(self, text: str) -> list[float]:
        """Generate deterministic vector from text hash."""
        import hashlib
        
        # Create seed from text hash
        hash_val = int(
            hashlib.md5(text.encode()).hexdigest(),
            16
        )
        
        # Generate deterministic vector
        vector = []
        for i in range(self.dimension):
            # Pseudo-random but deterministic values
            val = ((hash_val + i) % 10000) / 10000.0 - 0.5
            vector.append(val)
        
        return vector
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        return [self.embed(t) for t in texts]


@pytest.fixture
def mock_embeddings():
    """Provide mock embeddings for testing."""
    return MockEmbeddings()


@pytest.fixture
def mock_config():
    """Provide mock configuration for testing."""
    return MockConfig()


# Usage in tests:
# def test_something(mock_embeddings, mock_config):
#     result = process(mock_embeddings, mock_config)
#     assert result is not None
```

---

## Prevention Checklist

Use this checklist to avoid repeating these lessons:

### 🔧 Setup Phase

- [ ] **Dependencies**: Pin exact versions of critical packages (Pydantic, FastAPI, etc.)
  ```
  pydantic==2.10.0
  fastapi==0.104.0
  ```

- [ ] **Docker**: Expose all ports needed for local testing
  ```yaml
  ports:
    - "6333:6333"  # Host:Container
  ```

- [ ] **Configuration**: Create schema with Pydantic models, not manual validation
  ```python
  model_config = ConfigDict(extra="allow")
  ```

- [ ] **Secrets**: Never store API keys in YAML, always use environment variables
  ```bash
  OPENROUTER_API_KEY=sk_...  # In .env, not in code
  ```

### 🧪 Testing Phase

- [ ] **Unit Tests**: Can run without Docker (`pytest tests/unit`)
- [ ] **Integration Tests**: Marked with `@pytest.mark.requires_docker`
- [ ] **Mocks**: Use mock objects for external services
- [ ] **Fixtures**: Create reusable test data in conftest.py

### 📦 Deployment Phase

- [ ] **Requirements.txt**: Pinned versions with min/max range
  ```
  pydantic>=2.10.0,<3.0.0
  ```

- [ ] **Environment**: `.env.example` committed, `.env` in .gitignore
- [ ] **Health Checks**: Validate all external dependencies at startup
- [ ] **Error Messages**: Include context and fixes, not just stack traces

### 📝 Code Review Checklist

- [ ] No hardcoded API keys or passwords
- [ ] All external service calls have timeouts
- [ ] Config validation errors are helpful (not just `ValueError`)
- [ ] Tests don't require external services (unless marked `@requires_docker`)
- [ ] Version constraints documented for critical dependencies

---

## 📚 Quick Reference: Before/After Patterns

### Pattern 1: Configuration Validation

**❌ Before (Bad)**:
```python
def load_config(path):
    import json
    with open(path) as f:
        config = json.load(f)
    
    # Hope these keys exist!
    url = config['qdrant_url']
    timeout = config.get('timeout', 30)  # Silent default
    
    return config
```

**✅ After (Good)**:
```python
from pydantic import BaseModel, Field

class QdrantSettings(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str = Field(..., description="Connection URL")
    timeout: int = Field(default=30, ge=1, le=300)

def load_config(path):
    data = yaml.safe_load(Path(path).read_text())
    return QdrantSettings(**data['qdrant'])
```

### Pattern 2: Service Connections

**❌ Before (Bad)**:
```python
# Hardcoded hostnames that only work in Docker
QDRANT_URL = "http://qdrant:6333"
REDIS_URL = "redis://redis:6379"
```

**✅ After (Good)**:
```python
class ServiceLocator:
    SERVICES = {
        "qdrant": ("qdrant", "localhost", 6333),
        "redis": ("redis", "localhost", 6379),
    }
    
    def get_url(self, service: str) -> str:
        docker_host, local_host, port = self.SERVICES[service]
        host = docker_host if self._in_docker() else local_host
        return f"http://{host}:{port}"
```

### Pattern 3: Secret Management

**❌ Before (Bad)**:
```yaml
llm:
  api_key: "sk-1234567890..."  # EXPOSED!
```

**✅ After (Good)**:
```yaml
# configs/client/client.yaml (safe to commit)
llm:
  api_key_env_var: "OPENROUTER_API_KEY"  # Points to env var
```

```python
# Code that reads it
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("Set OPENROUTER_API_KEY environment variable")
```

### Pattern 4: Testing

**❌ Before (Bad)**:
```python
# Tests require Docker to be running
def test_qdrant():
    from services.embed import QdrantVectorStore
    store = QdrantVectorStore("http://localhost:6333")
    store.health_check()  # FAILS if Docker down!
```

**✅ After (Good)**:
```python
# Unit test - no external dependencies
def test_qdrant_config():
    from services.api.config.models import QdrantSettings
    config = QdrantSettings(url="http://localhost:6333")
    assert config.url == "http://localhost:6333"

# Integration test - explicitly marked
@pytest.mark.requires_docker
def test_qdrant_real_connection():
    store = QdrantVectorStore("http://localhost:6333")
    assert store.health_check()
```

---

## 📊 Impact Summary

| Lesson | Impact | Priority | Effort |
|--------|--------|----------|--------|
| Pydantic v2 Migration | Blocker for testing | 🔴 Critical | 2 hours |
| Docker Networking | Can't test locally | 🔴 Critical | 1 hour |
| Config Validation | Errors at startup | 🟠 High | 3 hours |
| Secret Management | Security risk | 🟠 High | 1 hour |
| Testing Strategy | CI/CD fails | 🟡 Medium | 2 hours |

---

## 🔗 Related Documents

- [SUBPROJECT-5-PROOF.md](../SUBPROJECT-5-PROOF.md) - Configuration validation details
- [SUBPROJECT-6-PROOF.md](../SUBPROJECT-6-PROOF.md) - Embedding service implementation
- [docker-compose.yml](../../deploy/compose/docker-compose.yml) - Docker configuration template
- [.env.example](../../.env.example) - Secret management template

---

**Document Status**: Complete  
**Last Updated**: 2025-01-09  
**Next Review**: After Subproject 7 completion