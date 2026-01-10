"""
Endpoint principal de consulta RAG.
Integrado con retrieval (Qdrant) y LLM (OpenRouter).
Con instrumentación de métricas de observabilidad.
Con cache Redis para respuestas repetidas.
"""
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse, ContextChunk
from app.retrieval import retrieve_context
from app.prompting import load_template, build_messages
from app.llm import call_with_fallback, OpenRouterError
from app.observability import get_metrics, Timer
from app.cache import get_query_cache
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class SimpleQueryRequest(BaseModel):
    """Solicitud simplificada de consulta para interfaz web."""
    query: str
    rag_id: Optional[str] = "default"
    top_k: Optional[int] = 5
    score_threshold: Optional[float] = 0.0


class SimpleQueryResponse(BaseModel):
    """Respuesta simplificada para interfaz web."""
    answer: str
    sources: List[str] = []
    context_chunks: List[ContextChunk] = []
    latency_ms: int = 0


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Procesa una consulta RAG completa con parámetros estándar.
    
    Args:
        request: QueryRequest con rag_id, question, top_k, session_id
    
    Returns:
        QueryResponse con answer generado, context_chunks, latency_ms, etc.
    """
    metrics = get_metrics()
    metrics.inc_requests()
    
    with Timer() as timer:
        # Generar session_id si no se provee
        session_id = request.session_id or str(uuid.uuid4())
        
        try:
            # 1. Retrieval de contexto desde Qdrant
            top_k = request.top_k or 5
            chunks = await retrieve_context(
                rag_id=request.rag_id,
                question=request.question,
                top_k=top_k,
                score_threshold=request.score_threshold
            )
            
            # Convertir a modelo de respuesta
            context_chunks = [
                ContextChunk(
                    id=chunk["id"],
                    source=chunk["source"],
                    text=chunk["text"],
                    score=chunk["score"]
                )
                for chunk in chunks
            ]
            
            # Si no hay contexto, retornar mensaje genérico
            if not context_chunks:
                answer = "No se encontró contexto relevante para tu pregunta."
                latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
                return QueryResponse(
                    rag_id=request.rag_id,
                    answer=answer,
                    context_chunks=[],
                    latency_ms=latency_ms,
                    cache_hit=False,
                    session_id=session_id
                )
            
            # 2. Cargar templates de prompts (templates por defecto)
            try:
                system_template = load_template("prompts/system_default.txt")
                user_template = load_template("prompts/user_default.txt")
            except FileNotFoundError as e:
                metrics.inc_errors()
                raise HTTPException(
                    status_code=500,
                    detail=f"Template no encontrado: {str(e)}"
                )
            
            # 3. Build de mensajes para LLM
            messages = build_messages(
                system_template=system_template,
                user_template=user_template,
                question=request.question,
                context_chunks=[
                    {
                        "text": c.text,
                        "source": c.source,
                        "score": c.score
                    }
                    for c in context_chunks
                ],
                session_history=None  # Sin historial por ahora
            )
            
            # 4. Llamada a LLM con fallback
            try:
                llm_response = await call_with_fallback(
                    primary_model="openai/gpt-3.5-turbo",
                    fallback_model="anthropic/claude-instant-v1",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    timeout=30,
                    max_retries=2
                )
                answer = llm_response["content"]
            except OpenRouterError as e:
                metrics.inc_errors()
                # Si LLM falla, retornar mensaje de error
                answer = f"Error al generar respuesta: {e.message}"
            
            latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
            
            return QueryResponse(
                rag_id=request.rag_id,
                answer=answer,
                context_chunks=context_chunks,
                latency_ms=latency_ms,
                cache_hit=False,
                session_id=session_id
            )
            
        except HTTPException:
            raise
        except Exception as e:
            metrics.inc_errors()
            raise HTTPException(
                status_code=500,
                detail=f"Error en procesamiento de consulta: {str(e)}"
            )


@router.post("/query/simple", response_model=SimpleQueryResponse)
async def query_simple(request: SimpleQueryRequest):
    """
    Endpoint simplificado para interfaz web.
    Acepta un parámetro 'query' y retorna respuesta formateada para web.
    
    Con cache Redis: si la misma pregunta ya fue respondida,
    devuelve la respuesta cacheada en ~5ms en lugar de ~5 segundos.
    
    Args:
        request: SimpleQueryRequest con query, rag_id, top_k, score_threshold
    
    Returns:
        SimpleQueryResponse con answer, sources, context_chunks
    """
    metrics = get_metrics()
    metrics.inc_requests()
    cache = get_query_cache()
    
    with Timer() as timer:
        try:
            # 1. BUSCAR EN CACHE PRIMERO
            cached_response = await cache.get(query=request.query, rag_id=request.rag_id)
            if cached_response:
                # Cache HIT - devolver respuesta instantánea
                metrics.inc_cache_hits()
                latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
                return SimpleQueryResponse(
                    answer=cached_response.get("answer", ""),
                    sources=cached_response.get("sources", []),
                    context_chunks=[
                        ContextChunk(**c) for c in cached_response.get("context_chunks", [])
                    ],
                    latency_ms=latency_ms
                )
            
            # 2. CACHE MISS - procesar normalmente
            session_id = str(uuid.uuid4())
            
            # Retrieval de contexto desde Qdrant
            top_k = request.top_k or 5
            chunks = await retrieve_context(
                rag_id=request.rag_id,
                question=request.query,
                top_k=top_k,
                score_threshold=request.score_threshold or 0.0
            )
            
            # Convertir a modelo de respuesta
            context_chunks = [
                ContextChunk(
                    id=chunk["id"],
                    source=chunk["source"],
                    text=chunk["text"],
                    score=chunk["score"]
                )
                for chunk in chunks
            ]
            
            # Extraer sources
            sources = list(set([c.source for c in context_chunks]))
            
            # Si no hay contexto, retornar mensaje genérico
            if not context_chunks:
                latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
                return SimpleQueryResponse(
                    answer="No se encontró contexto relevante para tu pregunta.",
                    sources=[],
                    context_chunks=[],
                    latency_ms=latency_ms
                )
            
            # Cargar templates de prompts
            try:
                system_template = load_template("prompts/system_default.txt")
                user_template = load_template("prompts/user_default.txt")
            except FileNotFoundError as e:
                metrics.inc_errors()
                answer = f"Error: No se pudieron cargar los templates - {str(e)}"
                latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
                return SimpleQueryResponse(
                    answer=answer,
                    sources=sources,
                    context_chunks=context_chunks,
                    latency_ms=latency_ms
                )
            
            # Build de mensajes para LLM
            messages = build_messages(
                system_template=system_template,
                user_template=user_template,
                question=request.query,
                context_chunks=[
                    {
                        "text": c.text,
                        "source": c.source,
                        "score": c.score
                    }
                    for c in context_chunks
                ],
                session_history=None
            )
            
            # Llamada a LLM con fallback
            try:
                llm_response = await call_with_fallback(
                    primary_model="openai/gpt-3.5-turbo",
                    fallback_model="anthropic/claude-instant-v1",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    timeout=30,
                    max_retries=2
                )
                answer = llm_response["content"]
            except OpenRouterError as e:
                metrics.inc_errors()
                answer = f"Error al generar respuesta: {e.message}"
            except Exception as e:
                metrics.inc_errors()
                answer = f"Error: {str(e)}"
            
            latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
            
            # 3. GUARDAR EN CACHE para próximas consultas iguales
            response_to_cache = {
                "answer": answer,
                "sources": sources,
                "context_chunks": [
                    {"id": c.id, "source": c.source, "text": c.text, "score": c.score}
                    for c in context_chunks
                ]
            }
            await cache.set(query=request.query, rag_id=request.rag_id, response=response_to_cache)
            
            return SimpleQueryResponse(
                answer=answer,
                sources=sources,
                context_chunks=context_chunks,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            metrics.inc_errors()
            latency_ms = int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0
            return SimpleQueryResponse(
                answer=f"Error: {str(e)}",
                sources=[],
                context_chunks=[],
                latency_ms=latency_ms
            )