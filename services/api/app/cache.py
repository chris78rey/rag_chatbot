"""
Módulo de Cache con Redis para RAF Chatbot.

Cachea respuestas de queries para evitar llamadas repetidas al LLM.

Funcionamiento:
1. Query llega → se crea un hash único de (query + rag_id)
2. Buscar en Redis si existe ese hash
3. Si existe → devolver respuesta cacheada (rápido, ~5ms)
4. Si no existe → procesar normalmente → guardar en Redis → devolver

Ejemplo:
    from app.cache import QueryCache
    
    cache = QueryCache()
    
    # Buscar en cache
    cached = await cache.get(query="What is lean startup?", rag_id="default")
    if cached:
        return cached  # Hit! Respuesta instantánea
    
    # Si no está en cache, procesar y guardar
    response = await process_query(...)
    await cache.set(query="What is lean startup?", rag_id="default", response=response)

Autor: RAF Chatbot Team
Fecha: 2026-01-09
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Cliente Redis global
_redis_client = None


def get_redis_client():
    """
    Obtiene o crea conexión a Redis.
    
    Returns:
        Cliente Redis o None si no está disponible
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test de conexión
        _redis_client.ping()
        logger.info(f"✓ Redis conectado: {redis_url}")
        
        return _redis_client
        
    except ImportError:
        logger.warning("⚠ redis package no instalado, cache deshabilitado")
        return None
    except Exception as e:
        logger.warning(f"⚠ No se pudo conectar a Redis: {e}")
        return None


class QueryCache:
    """
    Cache de queries usando Redis.
    
    Características:
    - TTL configurable (default: 1 hora)
    - Hash único por (query + rag_id)
    - Serialización JSON automática
    - Graceful degradation si Redis no disponible
    """
    
    # Prefijo para las keys en Redis
    KEY_PREFIX = "raf:cache:query:"
    
    # Tiempo de vida del cache (segundos)
    DEFAULT_TTL = 3600  # 1 hora
    
    def __init__(self, ttl_seconds: int = None):
        """
        Inicializa el cache.
        
        Args:
            ttl_seconds: Tiempo de vida en segundos (default: 3600 = 1 hora)
        """
        self.ttl = ttl_seconds or self.DEFAULT_TTL
        self._client = None
    
    @property
    def client(self):
        """Lazy loading del cliente Redis."""
        if self._client is None:
            self._client = get_redis_client()
        return self._client
    
    def _make_key(self, query: str, rag_id: str) -> str:
        """
        Genera key única para una query.
        
        Combina query + rag_id y crea hash MD5.
        
        Args:
            query: Pregunta del usuario
            rag_id: ID del RAG
            
        Returns:
            Key para Redis: "raf:cache:query:<hash>"
        """
        # Normalizar query (lowercase, strip)
        normalized = f"{rag_id}:{query.lower().strip()}"
        
        # Crear hash
        hash_value = hashlib.md5(normalized.encode()).hexdigest()
        
        return f"{self.KEY_PREFIX}{hash_value}"
    
    async def get(self, query: str, rag_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca respuesta en cache.
        
        Args:
            query: Pregunta del usuario
            rag_id: ID del RAG
            
        Returns:
            Dict con respuesta cacheada o None si no existe
        """
        if not self.client:
            return None
        
        try:
            key = self._make_key(query, rag_id)
            data = self.client.get(key)
            
            if data:
                logger.debug(f"Cache HIT: {key[:50]}...")
                return json.loads(data)
            else:
                logger.debug(f"Cache MISS: {key[:50]}...")
                return None
                
        except Exception as e:
            logger.warning(f"Error leyendo cache: {e}")
            return None
    
    async def set(
        self,
        query: str,
        rag_id: str,
        response: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """
        Guarda respuesta en cache.
        
        Args:
            query: Pregunta del usuario
            rag_id: ID del RAG
            response: Respuesta a cachear (dict serializable)
            ttl: Tiempo de vida en segundos (opcional)
            
        Returns:
            True si se guardó correctamente
        """
        if not self.client:
            return False
        
        try:
            key = self._make_key(query, rag_id)
            data = json.dumps(response, ensure_ascii=False)
            ttl = ttl or self.ttl
            
            self.client.setex(key, ttl, data)
            logger.debug(f"Cache SET: {key[:50]}... (TTL={ttl}s)")
            
            return True
            
        except Exception as e:
            logger.warning(f"Error guardando en cache: {e}")
            return False
    
    async def delete(self, query: str, rag_id: str) -> bool:
        """
        Elimina una entrada del cache.
        
        Args:
            query: Pregunta del usuario
            rag_id: ID del RAG
            
        Returns:
            True si se eliminó
        """
        if not self.client:
            return False
        
        try:
            key = self._make_key(query, rag_id)
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error eliminando cache: {e}")
            return False
    
    async def clear_all(self, rag_id: str = None) -> int:
        """
        Limpia todo el cache o solo de un RAG específico.
        
        Args:
            rag_id: Si se especifica, solo limpia ese RAG
            
        Returns:
            Número de keys eliminadas
        """
        if not self.client:
            return 0
        
        try:
            pattern = f"{self.KEY_PREFIX}*"
            keys = self.client.keys(pattern)
            
            if keys:
                return self.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.warning(f"Error limpiando cache: {e}")
            return 0
    
    async def stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Dict con estadísticas
        """
        if not self.client:
            return {"available": False}
        
        try:
            pattern = f"{self.KEY_PREFIX}*"
            keys = self.client.keys(pattern)
            
            return {
                "available": True,
                "total_cached_queries": len(keys),
                "ttl_seconds": self.ttl,
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# Instancia global del cache
_query_cache = None


def get_query_cache() -> QueryCache:
    """
    Obtiene instancia singleton del cache.
    
    Returns:
        QueryCache instance
    """
    global _query_cache
    
    if _query_cache is None:
        _query_cache = QueryCache()
    
    return _query_cache