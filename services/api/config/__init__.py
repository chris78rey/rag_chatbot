"""
RAF Chatbot — Configuration Module

Provides configuration loading and validation for:
- Client global configuration (client.yaml)
- RAG-specific configurations (<rag_id>.yaml)

Usage:
    from services.api.config import ConfigLoader, ClientConfig, RagConfig
    
    # Load client config
    client_cfg = ConfigLoader.load_client_config("configs/client/client.yaml")
    
    # Load single RAG config
    rag_cfg = ConfigLoader.load_rag_config("configs/rags/my_rag.yaml")
    
    # Load all RAG configs from directory
    all_rags = ConfigLoader.load_all_rag_configs("configs/rags")
"""

from .models import ClientConfig, RagConfig
from .loader import ConfigLoader

__all__ = [
    "ConfigLoader",
    "ClientConfig",
    "RagConfig",
]