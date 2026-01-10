"""
Módulo de retrieval: genera embeddings y busca contexto relevante.

Usa sentence-transformers local (GRATIS, sin API key).
Modelo: all-MiniLM-L6-v2 (384 dimensiones, rápido y eficiente)

Funciones:
- get_embedding(): Genera embedding para texto usando sentence-transformers
- retrieve_context(): Busca chunks relevantes para una pregunta
"""
from typing import List, Dict, Any, Optional
import os

from app.qdrant_client import search

# Modelo de sentence-transformers (se carga una sola vez)
_model = None
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingüe, recomendado para español
EMBEDDING_DIM = 384  # Este modelo también tiene 384 dimensiones


def get_model():
    """
    Carga el modelo de sentence-transformers (singleton).
    Se carga una sola vez y se reutiliza.
    """
    global _model
    if _model is None:
        print(f"Cargando modelo de embeddings: {EMBEDDING_MODEL}...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"✓ Modelo cargado: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    return _model


async def get_embedding(text: str, model_name: str = None) -> List[float]:
    """
    Genera embedding para un texto usando sentence-transformers.
    
    Args:
        text: Texto a vectorizar
        model_name: Ignorado (usa modelo local)
    
    Returns:
        Vector de embeddings (384 dimensiones)
    """
    model = get_model()
    
    # Generar embedding
    embedding = model.encode(text, convert_to_numpy=True)
    
    # Convertir a lista de floats
    return embedding.tolist()


def get_embedding_sync(text: str) -> List[float]:
    """
    Versión síncrona de get_embedding (para scripts de ingesta).
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def get_embeddings_batch_sync(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings para múltiples textos (más eficiente).
    Útil para ingesta de documentos.
    
    Args:
        texts: Lista de textos a vectorizar
        
    Returns:
        Lista de vectores de embeddings
    """
    if not texts:
        return []
    
    model = get_model()
    
    # Generar embeddings en batch (más eficiente)
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    # Convertir a lista de listas de floats
    return [emb.tolist() for emb in embeddings]


async def retrieve_context(
    rag_id: str,
    question: str,
    top_k: int = 5,
    score_threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Recupera contexto relevante de Qdrant para una pregunta.
    
    Args:
        rag_id: ID del RAG (= nombre de colección)
        question: Pregunta del usuario
        top_k: Número de chunks a recuperar
        score_threshold: Score mínimo (opcional)
    
    Returns:
        Lista de chunks con {id, source, text, score}
    """
    # Generar embedding de la pregunta
    try:
        query_vector = await get_embedding(question)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []
    
    # Usar rag_id directamente como nombre de colección
    collection_name = rag_id
    
    results = search(
        collection_name=collection_name,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=score_threshold
    )
    
    return results


def get_embedding_dimension() -> int:
    """Retorna la dimensión de embeddings usada."""
    return EMBEDDING_DIM