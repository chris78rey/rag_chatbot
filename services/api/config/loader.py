"""
RAF Chatbot — Configuration Loader

Loads and validates YAML configuration files using Pydantic models.
Provides helpful error messages for validation failures.
"""

import yaml
from pathlib import Path
from typing import Union, Optional
from pydantic import ValidationError

from .models import ClientConfig, RagConfig


class ConfigLoader:
    """Loads and validates configuration files."""

    @staticmethod
    def load_client_config(config_path: Union[str, Path]) -> ClientConfig:
        """
        Load and validate client configuration from YAML file.

        Args:
            config_path: Path to client.yaml file

        Returns:
            ClientConfig: Validated configuration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If YAML is invalid
            ValidationError: If configuration doesn't match schema
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_path}: {e}")

        if not config_dict:
            raise ValueError(f"Config file is empty: {config_path}")

        try:
            return ClientConfig(**config_dict)
        except ValidationError as e:
            raise ValidationError(
                f"Configuration validation failed:\n{e.json()}"
            ) from e

    @staticmethod
    def load_rag_config(config_path: Union[str, Path]) -> RagConfig:
        """
        Load and validate RAG configuration from YAML file.

        Args:
            config_path: Path to <rag_id>.yaml file

        Returns:
            RagConfig: Validated configuration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If YAML is invalid
            ValidationError: If configuration doesn't match schema
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_path}: {e}")

        if not config_dict:
            raise ValueError(f"Config file is empty: {config_path}")

        try:
            return RagConfig(**config_dict)
        except ValidationError as e:
            raise ValidationError(
                f"RAG configuration validation failed:\n{e.json()}"
            ) from e

    @staticmethod
    def load_all_rag_configs(rags_dir: Union[str, Path]) -> dict:
        """
        Load and validate all RAG configurations from a directory.

        Args:
            rags_dir: Directory containing <rag_id>.yaml files

        Returns:
            dict: Dictionary mapping rag_id -> RagConfig

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        rags_dir = Path(rags_dir)

        if not rags_dir.exists():
            raise FileNotFoundError(f"RAGs directory not found: {rags_dir}")

        rags = {}
        for config_file in rags_dir.glob("*.yaml"):
            # Skip .example files
            if config_file.name.endswith(".example"):
                continue

            try:
                rag_config = ConfigLoader.load_rag_config(config_file)
                rags[rag_config.rag_id] = rag_config
            except (ValueError, ValidationError) as e:
                # Log error but continue loading other configs
                print(f"Warning: Failed to load {config_file}: {e}")

        return rags