"""
Modelos Pydantic para requests y responses del API.

Incluye:
- QueryRequest: Solicitud de consulta RAG
- ContextChunk: Chunk recuperado de Qdrant
- QueryResponse: Respuesta a una consulta
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ContextChunk(BaseModel):
    """Representa un chunk de contexto recuperado de Qdrant."""
    id: str = Field(..., description="ID único del punto en Qdrant")
    source: str = Field(..., description="Ruta del archivo fuente")
    text: str = Field(..., description="Contenido textual del chunk")
    score: float = Field(..., description="Score de similitud (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "source": "docs/policy.pdf",
                "text": "Política de vacaciones...",
                "score": 0.89
            }
        }


class QueryRequest(BaseModel):
    """Solicitud de consulta RAG."""
    rag_id: str = Field(..., description="ID del RAG (corresponde a nombre de colección)")
    question: str = Field(..., description="Pregunta del usuario")
    top_k: Optional[int] = Field(5, description="Número de chunks a recuperar")
    session_id: Optional[str] = Field(None, description="ID de sesión (generado si no se provee)")
    score_threshold: Optional[float] = Field(None, description="Score mínimo para incluir resultado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rag_id": "policies",
                "question": "¿Cuántos días de vacaciones me corresponden?",
                "top_k": 5,
                "session_id": "sess_abc123"
            }
        }


class QueryResponse(BaseModel):
    """Respuesta a una consulta RAG."""
    rag_id: str = Field(..., description="ID del RAG consultado")
    answer: str = Field(..., description="Respuesta generada (o NOT_IMPLEMENTED si LLM aún no integrado)")
    context_chunks: List[ContextChunk] = Field(..., description="Chunks de contexto recuperados")
    latency_ms: int = Field(..., description="Latencia de procesamiento en milisegundos")
    cache_hit: bool = Field(False, description="Si la respuesta vino de caché")
    session_id: str = Field(..., description="ID de sesión para tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la respuesta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rag_id": "policies",
                "answer": "NOT_IMPLEMENTED - Contexto recuperado, falta integración LLM",
                "context_chunks": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "source": "docs/policy.pdf",
                        "text": "Política de vacaciones...",
                        "score": 0.89
                    }
                ],
                "latency_ms": 245,
                "cache_hit": False,
                "session_id": "sess_abc123",
                "timestamp": "2025-01-10T15:30:00"
            }
        }