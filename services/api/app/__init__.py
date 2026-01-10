"""
Módulo app: contiene la lógica de la API FastAPI.

Exports:
- qdrant_client: Cliente para operaciones vectoriales
- retrieval: Módulo de búsqueda de contexto
- models: Modelos Pydantic para requests/responses
- routes: Rutas/endpoints del API
"""

from app.qdrant_client import (
    get_client,
    ensure_collection,
    upsert_chunks,
    search,
    delete_collection,
)
from app.retrieval import get_embedding, retrieve_context
from app.models import QueryRequest, QueryResponse, ContextChunk

__all__ = [
    "get_client",
    "ensure_collection",
    "upsert_chunks",
    "search",
    "delete_collection",
    "get_embedding",
    "retrieve_context",
    "QueryRequest",
    "QueryResponse",
    "ContextChunk",
]