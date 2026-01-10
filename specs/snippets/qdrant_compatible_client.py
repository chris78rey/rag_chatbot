"""
Qdrant Compatible Client - Multi-version API Support

Cliente Qdrant compatible con múltiples versiones de la librería.
Maneja automáticamente las diferencias de API entre versiones.

Soporta:
- qdrant-client < 1.7.0 (método search)
- qdrant-client >= 1.7.0 (método query_points)

Uso:
    from snippets.qdrant_compatible_client import QdrantCompatibleClient
    
    client = QdrantCompatibleClient(url="http://localhost:6333")
    results = client.search("my_collection", query_vector, limit=5)

Autor: RAF Chatbot Team
Fecha: 2026-01-09
Lección Relacionada: LESSONS-LEARNED-07-QDRANT-CLIENT-API-COMPATIBILITY.md
"""

from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class QdrantCompatibleClient:
    """
    Wrapper compatible con múltiples versiones de qdrant-client.
    
    Detecta automáticamente qué versión de API usar basado
    en los métodos disponibles en el cliente.
    
    Attributes:
        _client: Cliente nativo de Qdrant
        _api_version: Versión de API detectada ("v1" o "v2")
    
    Example:
        >>> client = QdrantCompatibleClient(url="http://localhost:6333")
        >>> print(f"Using API: {client.api_version}")
        Using API: v2
        
        >>> results = client.search("my_collection", [0.1]*384, limit=5)
        >>> for r in results:
        ...     print(f"ID: {r['id']}, Score: {r['score']:.4f}")
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Inicializa el cliente compatible.
        
        Args:
            url: URL del servidor Qdrant (default: env QDRANT_URL o localhost:6333)
            api_key: API key opcional para autenticación
            timeout: Timeout para conexiones en segundos
        
        Raises:
            ImportError: Si qdrant-client no está instalado
            RuntimeError: Si la versión del cliente no es soportada
        """
        try:
            from qdrant_client import QdrantClient
        except ImportError:
            raise ImportError(
                "qdrant-client not installed. "
                "Install with: pip install qdrant-client"
            )
        
        # Resolver URL
        url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = api_key or os.getenv("QDRANT_API_KEY")
        
        # Crear cliente nativo
        self._client = QdrantClient(
            url=url,
            api_key=api_key if api_key else None,
            timeout=timeout
        )
        
        # Detectar versión de API
        self._api_version = self._detect_api_version()
        logger.info(
            f"QdrantCompatibleClient initialized: url={url}, api={self._api_version}"
        )
    
    def _detect_api_version(self) -> str:
        """
        Detecta la versión de API disponible.
        
        Returns:
            "v2" para qdrant-client >= 1.7.0 (query_points)
            "v1" para qdrant-client < 1.7.0 (search)
        
        Raises:
            RuntimeError: Si no se encuentra método de búsqueda compatible
        """
        if hasattr(self._client, 'query_points'):
            return "v2"
        elif hasattr(self._client, 'search'):
            return "v1"
        else:
            raise RuntimeError(
                "Unsupported qdrant-client version. "
                "Expected 'search' or 'query_points' method. "
                "Please upgrade: pip install --upgrade qdrant-client"
            )
    
    @property
    def api_version(self) -> str:
        """Versión de API detectada."""
        return self._api_version
    
    @property
    def native_client(self):
        """
        Acceso al cliente nativo para operaciones no cubiertas.
        
        Use esto para operaciones avanzadas que no están en el wrapper.
        
        Example:
            >>> native = client.native_client
            >>> native.create_collection(...)
        """
        return self._client
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca vectores similares (compatible con todas las versiones).
        
        Esta es la función principal del wrapper. Detecta automáticamente
        qué método usar (query_points o search) y normaliza los resultados.
        
        Args:
            collection_name: Nombre de la colección a buscar
            query_vector: Vector de consulta (embeddings)
            limit: Número máximo de resultados (default: 5)
            score_threshold: Score mínimo para filtrar resultados (opcional)
            with_payload: Incluir payload en resultados (default: True)
            with_vectors: Incluir vectores en resultados (default: False)
            filter_conditions: Filtros adicionales (formato Qdrant)
        
        Returns:
            Lista de resultados normalizados. Cada resultado es un dict con:
            - id: ID del punto (string)
            - score: Score de similitud (float)
            - payload: Datos asociados (dict, si with_payload=True)
            - vector: Vector (list, si with_vectors=True)
        
        Example:
            >>> results = client.search(
            ...     collection_name="documents",
            ...     query_vector=embeddings,
            ...     limit=10,
            ...     score_threshold=0.7
            ... )
            >>> for r in results:
            ...     print(f"{r['id']}: {r['score']:.3f} - {r['payload'].get('text', '')[:50]}")
        """
        try:
            if self._api_version == "v2":
                results = self._search_v2(
                    collection_name, query_vector, limit,
                    score_threshold, with_payload, with_vectors,
                    filter_conditions
                )
            else:
                results = self._search_v1(
                    collection_name, query_vector, limit,
                    score_threshold, with_payload, with_vectors,
                    filter_conditions
                )
            
            return self._normalize_results(results, with_payload, with_vectors)
            
        except Exception as e:
            logger.error(f"Search failed in collection '{collection_name}': {e}")
            return []
    
    def _search_v2(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        score_threshold: Optional[float],
        with_payload: bool,
        with_vectors: bool,
        filter_conditions: Optional[Dict]
    ):
        """
        Búsqueda usando API v2 (query_points).
        
        Disponible en qdrant-client >= 1.7.0
        """
        logger.debug(f"Using query_points (v2 API) on '{collection_name}'")
        
        kwargs = {
            "collection_name": collection_name,
            "query": query_vector,
            "limit": limit,
            "with_payload": with_payload,
            "with_vectors": with_vectors,
        }
        
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold
        
        if filter_conditions is not None:
            kwargs["query_filter"] = filter_conditions
        
        response = self._client.query_points(**kwargs)
        
        # query_points retorna QueryResponse con .points
        if hasattr(response, 'points'):
            return response.points
        return response
    
    def _search_v1(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        score_threshold: Optional[float],
        with_payload: bool,
        with_vectors: bool,
        filter_conditions: Optional[Dict]
    ):
        """
        Búsqueda usando API v1 (search).
        
        Disponible en qdrant-client < 1.7.0
        """
        logger.debug(f"Using search (v1 API) on '{collection_name}'")
        
        kwargs = {
            "collection_name": collection_name,
            "query_vector": query_vector,
            "limit": limit,
            "with_payload": with_payload,
            "with_vectors": with_vectors,
        }
        
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold
        
        if filter_conditions is not None:
            kwargs["query_filter"] = filter_conditions
        
        return self._client.search(**kwargs)
    
    def _normalize_results(
        self,
        results,
        with_payload: bool,
        with_vectors: bool
    ) -> List[Dict[str, Any]]:
        """
        Normaliza resultados a formato consistente.
        
        Independientemente de la versión de API, los resultados
        siempre tienen el mismo formato.
        """
        normalized = []
        
        for hit in results:
            try:
                item = {
                    "id": str(hit.id) if hasattr(hit, 'id') else "unknown",
                    "score": float(hit.score) if hasattr(hit, 'score') else 0.0,
                }
                
                if with_payload:
                    if hasattr(hit, 'payload') and hit.payload:
                        item["payload"] = dict(hit.payload)
                    else:
                        item["payload"] = {}
                
                if with_vectors:
                    if hasattr(hit, 'vector') and hit.vector:
                        item["vector"] = list(hit.vector)
                    else:
                        item["vector"] = []
                
                normalized.append(item)
                
            except Exception as e:
                logger.warning(f"Error normalizing search hit: {e}")
                continue
        
        logger.debug(f"Normalized {len(normalized)} results")
        return normalized
    
    # =========================================================================
    # COLLECTION OPERATIONS
    # =========================================================================
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Verifica si una colección existe.
        
        Args:
            collection_name: Nombre de la colección
        
        Returns:
            True si existe, False si no
        """
        try:
            collections = self._client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de una colección.
        
        Args:
            collection_name: Nombre de la colección
        
        Returns:
            Dict con información de la colección:
            - name: Nombre
            - points_count: Número de puntos
            - vectors_count: Número de vectores
            - status: Estado de la colección
            - error: Mensaje de error si falló
        """
        try:
            info = self._client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": getattr(info, 'vectors_count', info.points_count),
                "status": info.status.value if hasattr(info.status, 'value') else str(info.status),
                "error": None
            }
        except Exception as e:
            logger.error(f"Error getting collection info for '{collection_name}': {e}")
            return {
                "name": collection_name,
                "points_count": 0,
                "vectors_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def list_collections(self) -> List[str]:
        """
        Lista todas las colecciones disponibles.
        
        Returns:
            Lista de nombres de colecciones
        """
        try:
            collections = self._client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    # =========================================================================
    # HEALTH CHECK
    # =========================================================================
    
    def is_healthy(self) -> bool:
        """
        Verifica si el servidor Qdrant está accesible.
        
        Returns:
            True si el servidor responde, False si no
        """
        try:
            # Intentar listar colecciones como health check
            self._client.get_collections()
            return True
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check detallado del servidor.
        
        Returns:
            Dict con:
            - healthy: bool
            - collections_count: número de colecciones
            - api_version: versión de API detectada
            - error: mensaje de error si hay
        """
        try:
            collections = self._client.get_collections().collections
            return {
                "healthy": True,
                "collections_count": len(collections),
                "api_version": self._api_version,
                "error": None
            }
        except Exception as e:
            return {
                "healthy": False,
                "collections_count": 0,
                "api_version": self._api_version,
                "error": str(e)
            }
    
    def __repr__(self) -> str:
        """Representación string del cliente."""
        return f"QdrantCompatibleClient(api={self._api_version})"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def detect_qdrant_api_version() -> str:
    """
    Detecta la versión de API de qdrant-client instalado.
    
    No requiere conexión al servidor.
    
    Returns:
        "v2" para >= 1.7.0, "v1" para < 1.7.0, "unknown" si no se puede detectar
    """
    try:
        from qdrant_client import QdrantClient
        
        # Crear cliente en memoria para inspección
        try:
            client = QdrantClient(":memory:")
        except:
            # Si falla, crear objeto sin inicializar
            client = object.__new__(QdrantClient)
        
        if hasattr(client, 'query_points'):
            return "v2"
        elif hasattr(client, 'search'):
            return "v1"
        else:
            return "unknown"
    except ImportError:
        return "not_installed"


def get_qdrant_client_version() -> Optional[str]:
    """
    Obtiene la versión instalada de qdrant-client.
    
    Returns:
        String de versión (e.g., "1.16.2") o None si no está instalado
    """
    try:
        import qdrant_client
        return getattr(qdrant_client, '__version__', 'unknown')
    except ImportError:
        return None


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("Qdrant Compatible Client - Demo")
    print("=" * 70)
    
    # Mostrar información de la librería
    version = get_qdrant_client_version()
    api = detect_qdrant_api_version()
    print(f"\nqdrant-client version: {version}")
    print(f"API version detected: {api}")
    
    # Intentar crear cliente y conectar
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    print(f"\nAttempting connection to: {url}")
    
    try:
        client = QdrantCompatibleClient(url=url)
        print(f"✅ Connected successfully")
        print(f"   Client: {client}")
        
        # Health check
        health = client.health_check()
        print(f"\nHealth check:")
        print(f"   Healthy: {health['healthy']}")
        print(f"   Collections: {health['collections_count']}")
        print(f"   API: {health['api_version']}")
        
        # Listar colecciones
        collections = client.list_collections()
        print(f"\nCollections available: {collections}")
        
        # Si hay colecciones, mostrar info de la primera
        if collections:
            info = client.get_collection_info(collections[0])
            print(f"\nFirst collection info:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            # Intentar una búsqueda dummy
            print(f"\nTesting search in '{collections[0]}'...")
            
            # Determinar dimensión del vector
            try:
                full_info = client.native_client.get_collection(collections[0])
                vector_size = full_info.config.params.vectors.size
            except:
                vector_size = 384  # Default
            
            dummy_vector = [0.1] * vector_size
            results = client.search(
                collection_name=collections[0],
                query_vector=dummy_vector,
                limit=3
            )
            
            print(f"   Found {len(results)} results")
            for r in results[:3]:
                print(f"   - ID: {r['id']}, Score: {r['score']:.4f}")
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nMake sure Qdrant is running:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)