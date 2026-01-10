"""
Cliente Qdrant para operaciones vectoriales.

Funciones:
- get_client(): Obtener instancia del cliente
- ensure_collection(): Crear/verificar colección existe
- upsert_chunks(): Insertar/actualizar vectores con payload
- search(): Buscar vectores similares
"""
from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    """Obtiene o crea instancia singleton del cliente Qdrant."""
    global _client
    if _client is None:
        url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        api_key = os.getenv("QDRANT_API_KEY", None)
        try:
            _client = QdrantClient(url=url, api_key=api_key if api_key else None)
            logger.info(f"✓ Qdrant client connected to {url}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Qdrant: {e}")
            raise
    return _client


def ensure_collection(collection_name: str, vector_dim: int) -> bool:
    """
    Crea colección si no existe.
    
    Args:
        collection_name: Nombre de la colección (rag_id)
        vector_dim: Dimensión de los vectores de embeddings
    
    Returns:
        True si la colección existe o fue creada
    """
    client = get_client()
    
    try:
        # Verificar si existe
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dim,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"✓ Created collection: {collection_name}")
        else:
            logger.info(f"✓ Collection exists: {collection_name}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error ensuring collection {collection_name}: {e}")
        raise


def upsert_chunks(
    collection_name: str,
    chunks: List[Dict[str, Any]],
    vectors: List[List[float]]
) -> int:
    """
    Inserta o actualiza chunks en Qdrant.
    
    Args:
        collection_name: Nombre de la colección
        chunks: Lista de dicts con {id, source_path, page, chunk_index, text}
        vectors: Lista de vectores correspondientes
    
    Returns:
        Número de puntos insertados
    """
    client = get_client()
    
    try:
        points = [
            models.PointStruct(
                id=chunk.get("id", i),
                vector=vectors[i],
                payload={
                    "source_path": chunk.get("source_path", ""),
                    "page": chunk.get("page", 0),
                    "chunk_index": chunk.get("chunk_index", i),
                    "text": chunk.get("text", "")
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"✓ Upserted {len(points)} chunks to {collection_name}")
        
        return len(points)
    except Exception as e:
        logger.error(f"✗ Error upserting chunks: {e}")
        raise


def search(
    collection_name: str,
    query_vector: List[float],
    top_k: int = 5,
    score_threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Busca vectores similares en la colección.
    
    Args:
        collection_name: Nombre de la colección
        query_vector: Vector de la consulta
        top_k: Número de resultados a retornar
        score_threshold: Score mínimo (opcional)
    
    Returns:
        Lista de resultados con {id, source, text, score}
    """
    client = get_client()
    
    try:
        # Verificar que la colección existe
        try:
            collection_info = client.get_collection(collection_name)
            logger.info(f"✓ Searching in collection: {collection_name} (points: {collection_info.points_count})")
        except Exception as e:
            logger.warning(f"⚠ Collection {collection_name} not found: {e}")
            return []
        
        # Realizar búsqueda - usar query_points (método actual en qdrant-client >= 1.7)
        results = None
        
        # Intentar query_points primero (versiones nuevas >= 1.7)
        if hasattr(client, 'query_points'):
            try:
                logger.info("Using query_points method")
                response = client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold
                )
                # query_points devuelve QueryResponse con .points
                results = response.points if hasattr(response, 'points') else response
                logger.info(f"✓ query_points returned {len(results) if results else 0} results")
            except Exception as e:
                logger.warning(f"query_points failed: {e}, trying fallback")
                results = None
        
        # Fallback a search (versiones intermedias)
        if results is None and hasattr(client, 'search'):
            try:
                logger.info("Using search method (fallback 1)")
                results = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold
                )
                logger.info(f"✓ search returned {len(results) if results else 0} results")
            except Exception as e:
                logger.warning(f"search failed: {e}, trying next fallback")
                results = None
        
        # Fallback a scroll si no hay otros métodos (muy raro)
        if results is None:
            logger.warning("No search method available, returning empty results")
            return []
        
        # Formatear resultados
        formatted_results = []
        for hit in results:
            try:
                # Manejar diferentes estructuras de respuesta
                hit_id = str(hit.id) if hasattr(hit, 'id') else "unknown"
                hit_score = float(hit.score) if hasattr(hit, 'score') else 0.0
                hit_payload = hit.payload if hasattr(hit, 'payload') else {}
                
                formatted_results.append({
                    "id": hit_id,
                    "source": hit_payload.get("source", hit_payload.get("source_path", "unknown")),
                    "text": hit_payload.get("text", ""),
                    "score": hit_score
                })
            except Exception as e:
                logger.warning(f"Error formatting hit: {e}")
                continue
        
        logger.info(f"✓ Found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"✗ Error searching Qdrant: {e}")
        # Retornar lista vacía en caso de error en lugar de fallar
        return []


def delete_collection(collection_name: str) -> bool:
    """Elimina una colección (usado para reindex)."""
    client = get_client()
    try:
        client.delete_collection(collection_name=collection_name)
        logger.info(f"✓ Deleted collection: {collection_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Error deleting collection: {e}")
        raise