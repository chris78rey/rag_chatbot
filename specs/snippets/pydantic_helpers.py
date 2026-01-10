# specs/snippets/pydantic_helpers.py
"""
Pydantic v2 Helper Functions and Patterns

Reusable utilities for working with Pydantic v2 models, validation,
and configuration management. Safe to copy into new projects.
"""

from typing import Type, TypeVar, Any, Optional, Dict, List
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pathlib import Path
import yaml

T = TypeVar('T', bound=BaseModel)


# ============================================================================
# 1. STRICT MODEL FACTORY
# ============================================================================

def create_strict_model(
    name: str,
    fields: Dict[str, tuple[type, Any]],
    extra: str = "forbid",
    description: str = ""
) -> Type[BaseModel]:
    """
    Factory function to create strict Pydantic v2 models dynamically.
    
    Useful for generating models from configuration or when you want
    to avoid boilerplate class definitions.
    
    Args:
        name: Model class name
        fields: Dict of field_name -> (type, default_value)
                Use ... (Ellipsis) for required fields
        extra: Extra fields handling ('forbid', 'allow', 'ignore')
        description: Optional model docstring
    
    Returns:
        Dynamically created BaseModel subclass
    
    Example:
        # Create a model for API response validation
        ResponseModel = create_strict_model(
            "APIResponse",
            {
                "status": (str, ...),  # Required
                "code": (int, 200),    # Optional, default=200
                "data": (dict, {}),    # Optional, default={}
            }
        )
        
        response = ResponseModel(status="ok")
        assert response.code == 200
    
    Example 2: Define with Field() for advanced validation
        from pydantic import Field
        
        UserModel = create_strict_model(
            "User",
            {
                "email": (str, Field(..., min_length=5)),
                "age": (int, Field(default=18, ge=0, le=150)),
            }
        )
    """
    from pydantic import Field as PydField
    
    # Build field annotations and defaults
    annotations = {}
    field_definitions = {}
    
    for fname, (ftype, default) in fields.items():
        annotations[fname] = ftype
        
        if default is ...:
            # Required field
            field_definitions[fname] = PydField(...)
        elif isinstance(default, PydField):
            # Already a Field object
            field_definitions[fname] = default
        else:
            # Simple default value
            field_definitions[fname] = default
    
    # Create model class
    model_dict = {
        '__annotations__': annotations,
        'model_config': ConfigDict(extra=extra),
        **field_definitions
    }
    
    if description:
        model_dict['__doc__'] = description
    
    return type(name, (BaseModel,), model_dict)


# ============================================================================
# 2. VALIDATION WITH FEEDBACK
# ============================================================================

def validate_model_with_feedback(
    model_class: Type[T],
    data: dict,
    context: str = "",
    raise_on_error: bool = True
) -> tuple[Optional[T], str]:
    """
    Validate data against model with detailed, user-friendly error messages.
    
    Returns a tuple of (validated_instance, error_message) where
    error_message is "OK" if validation succeeded.
    
    Args:
        model_class: Pydantic model to validate against
        data: Data dictionary to validate
        context: Optional context string for error messages (e.g., "Loading client.yaml")
        raise_on_error: If True, raises ValidationError. If False, returns error message.
    
    Returns:
        Tuple of (validated_instance or None, error_message)
    
    Example:
        config, error = validate_model_with_feedback(
            ClientConfig,
            yaml_data,
            context="Loading client.yaml"
        )
        
        if error != "OK":
            print(f"❌ {error}")
            sys.exit(1)
        
        print(f"✅ Configuration loaded successfully")
        use_config(config)
    
    Example 2: Programmatic error handling
        config, error = validate_model_with_feedback(
            RagConfig,
            raw_config,
            raise_on_error=False
        )
        
        if config is None:
            # Handle error gracefully
            logger.error(error)
            return None
        
        return config
    """
    try:
        instance = model_class(**data)
        return instance, "OK"
    
    except ValidationError as e:
        # Build detailed error message
        error_lines = []
        
        if context:
            error_lines.append(f"❌ Validation failed: {context}")
        else:
            error_lines.append(f"❌ Validation failed for {model_class.__name__}")
        
        # Add field-level errors
        for error in e.errors():
            field_path = ".".join(str(x) for x in error['loc'])
            error_type = error['type']
            msg = error['msg']
            input_val = error.get('input')
            
            # Format error message
            error_msg = f"   {field_path}: {msg}"
            if input_val is not None and len(str(input_val)) < 50:
                error_msg += f" (got: {input_val})"
            
            error_lines.append(error_msg)
        
        error_message = "\n".join(error_lines)
        
        if raise_on_error:
            raise ValidationError.from_exception_data(
                model_class.__name__,
                [error.dict() for error in e.errors()]
            )
        
        return None, error_message


# ============================================================================
# 3. CONFIGURATION LOADER
# ============================================================================

class ConfigLoader:
    """
    Load and validate configuration files (YAML/JSON) with helpful error messages.
    
    Features:
    - Load YAML/JSON files with validation
    - Clear error messages with file paths
    - Support for missing files and malformed data
    - Type-safe configuration objects
    """
    
    @staticmethod
    def load_yaml(path: Path | str) -> dict:
        """
        Load YAML file with comprehensive error handling.
        
        Args:
            path: Path to YAML file
        
        Returns:
            Parsed YAML as dictionary
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or file is empty
        
        Example:
            data = ConfigLoader.load_yaml("configs/client/client.yaml")
        """
        path = Path(path)
        
        # Check existence
        if not path.exists():
            abs_path = path.resolve()
            cwd_path = Path.cwd() / path
            raise FileNotFoundError(
                f"Configuration file not found: {path}\n"
                f"Searched:\n"
                f"  - {abs_path}\n"
                f"  - {cwd_path}"
            )
        
        # Load and parse YAML
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ValueError(f"Configuration file is empty: {path}")
            
            return data
        
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML syntax in {path}:\n{e}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Error reading {path}: {e}"
            ) from e
    
    @staticmethod
    def load_json(path: Path | str) -> dict:
        """Load JSON file with error handling."""
        import json
        
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e
    
    @classmethod
    def load_and_validate(
        cls,
        model: Type[T],
        path: Path | str,
        file_format: str = "yaml"
    ) -> T:
        """
        Load configuration file and validate against model in one step.
        
        Args:
            model: Pydantic model class to validate against
            path: Path to configuration file
            file_format: 'yaml' or 'json'
        
        Returns:
            Validated model instance
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
            ValidationError: If validation fails
        
        Example:
            config = ConfigLoader.load_and_validate(
                ClientConfig,
                "configs/client/client.yaml"
            )
        """
        # Load file
        if file_format.lower() == "yaml":
            data = cls.load_yaml(path)
        elif file_format.lower() == "json":
            data = cls.load_json(path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
        
        # Validate
        context = f"Loading {Path(path).name}"
        instance, error = validate_model_with_feedback(
            model,
            data,
            context=context
        )
        
        if instance is None:
            raise ValueError(error)
        
        return instance


# ============================================================================
# 4. ENVIRONMENT VARIABLE HELPERS
# ============================================================================

def get_env_or_raise(key: str, description: str = "") -> str:
    """
    Get environment variable or raise helpful error.
    
    Args:
        key: Environment variable name
        description: Optional description for error message
    
    Returns:
        Environment variable value
    
    Raises:
        ValueError: If variable not set
    
    Example:
        api_key = get_env_or_raise(
            "OPENROUTER_API_KEY",
            description="Required for LLM integration"
        )
    """
    import os
    
    value = os.getenv(key)
    
    if not value:
        msg = f"Required environment variable not set: {key}"
        if description:
            msg += f"\n  {description}"
        raise ValueError(msg)
    
    return value


def get_env_or_default(key: str, default: str) -> str:
    """
    Get environment variable with fallback to default.
    
    Args:
        key: Environment variable name
        default: Default value if not set
    
    Returns:
        Environment variable value or default
    
    Example:
        debug = get_env_or_default("DEBUG", "false").lower() == "true"
    """
    import os
    return os.getenv(key, default)


# ============================================================================
# 5. SCHEMA VERSIONING PATTERN
# ============================================================================

class VersionedConfig(BaseModel):
    """
    Base class for versioned configurations.
    
    Handles automatic migration from older config versions.
    
    Example:
        class MyConfig(VersionedConfig):
            _version: str = "2.0"
            
            name: str
            
            @model_validator(mode='before')
            @classmethod
            def migrate_v1_to_v2(cls, data):
                if data.get('_version') == '1.0':
                    # Apply migrations
                    data['new_field'] = data.pop('old_field')
                    data['_version'] = '2.0'
                return data
    """
    
    model_config = ConfigDict(extra="allow")
    
    _version: str = Field(default="1.0")
    
    @classmethod
    def from_dict(cls, data: dict, auto_migrate: bool = True) -> 'VersionedConfig':
        """Load config with automatic version migration."""
        if auto_migrate:
            # Validators will handle migration
            pass
        return cls(**data)


# ============================================================================
# 6. VALIDATION HELPERS
# ============================================================================

def validate_no_extra_fields(data: dict, allowed_keys: set[str]) -> None:
    """
    Validate that data doesn't contain extra fields.
    
    Useful for strict config validation before passing to Pydantic.
    
    Args:
        data: Dictionary to validate
        allowed_keys: Set of allowed keys
    
    Raises:
        ValueError: If extra fields found
    
    Example:
        validate_no_extra_fields(
            config_data,
            allowed_keys={'qdrant', 'redis', 'llm', 'app'}
        )
    """
    extra_keys = set(data.keys()) - allowed_keys
    
    if extra_keys:
        raise ValueError(
            f"Unexpected configuration keys: {', '.join(extra_keys)}\n"
            f"Allowed keys: {', '.join(sorted(allowed_keys))}"
        )


def validate_no_hardcoded_secrets(data: dict, depth: int = 0) -> None:
    """
    Detect and prevent hardcoded secrets in configuration.
    
    Scans for common patterns that look like API keys, passwords, tokens.
    
    Args:
        data: Dictionary to scan
        depth: Internal recursion depth
    
    Raises:
        ValueError: If suspicious secret patterns found
    
    Example:
        validate_no_hardcoded_secrets(config_data)
    """
    SUSPICIOUS_KEYS = {'api_key', 'password', 'secret', 'token', 'credential'}
    SUSPICIOUS_PATTERNS = ['sk-', 'Bearer ', 'ey']
    
    def check_nested(obj, path=""):
        if not isinstance(obj, (dict, list)):
            return
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                
                # Check key name
                if any(sus in k.lower() for sus in SUSPICIOUS_KEYS):
                    if isinstance(v, str) and len(v) > 20:
                        # Check if looks like a real secret
                        if not v.startswith(('$', '{', 'null', 'None')):
                            if any(pat in v for pat in SUSPICIOUS_PATTERNS):
                                raise ValueError(
                                    f"⚠️  Possible hardcoded secret at '{new_path}'\n"
                                    f"   Use environment variables instead: "
                                    f"os.getenv('{k.upper()}')"
                                )
                
                # Recurse
                check_nested(v, new_path)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_nested(item, f"{path}[{i}]")
    
    check_nested(data)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Create model dynamically
    MyModel = create_strict_model(
        "Settings",
        {
            "host": (str, "localhost"),
            "port": (int, 8000),
            "debug": (bool, False),
        }
    )
    
    instance = MyModel(port=9000)
    print(f"✅ Created model: {instance}")
    
    # Example 2: Validate with feedback
    config_data = {"host": "example.com", "port": "invalid"}
    instance, error = validate_model_with_feedback(MyModel, config_data)
    print(f"Validation result: {error}")
    
    # Example 3: Load and validate config
    try:
        # config = ConfigLoader.load_and_validate(MyModel, "config.yaml")
        print("✅ ConfigLoader available for YAML/JSON loading")
    except FileNotFoundError:
        print("⚠️  No config file found (expected for snippet demo)")