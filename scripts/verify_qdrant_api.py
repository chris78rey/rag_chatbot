#!/usr/bin/env python3
"""
Verifica la compatibilidad del cliente Qdrant.

Uso:
    python scripts/verify_qdrant_api.py
    python scripts/verify_qdrant_api.py --test-connection
    python scripts/verify_qdrant_api.py --test-connection http://localhost:6333

Este script detecta qué versión de API está disponible
y verifica que el wrapper funcione correctamente.

Autor: RAF Chatbot Team
Fecha: 2026-01-09
Lección Relacionada: LESSONS-LEARNED-07-QDRANT-CLIENT-API-COMPATIBILITY.md
"""

import sys
import os
import argparse

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_qdrant_client_installed() -> bool:
    """Verifica si qdrant-client está instalado."""
    try:
        import qdrant_client
        return True
    except ImportError:
        return False


def check_qdrant_client_version() -> str:
    """Verifica la versión instalada de qdrant-client."""
    try:
        import qdrant_client
        version = getattr(qdrant_client, '__version__', 'unknown')
        print(f"✓ qdrant-client version: {version}")
        return version
    except ImportError:
        print("✗ qdrant-client not installed")
        print("  Install with: pip install qdrant-client")
        return None


def check_available_methods() -> dict:
    """Verifica qué métodos de búsqueda están disponibles."""
    from qdrant_client import QdrantClient
    
    # Crear cliente en memoria para inspección (no requiere servidor)
    try:
        client = QdrantClient(":memory:")
    except Exception:
        # Si falla, crear objeto sin inicializar para inspección
        client = object.__new__(QdrantClient)
    
    methods = {
        'query_points': hasattr(client, 'query_points'),
        'search': hasattr(client, 'search'),
        'search_batch': hasattr(client, 'search_batch'),
        'query': hasattr(client, 'query'),
        'scroll': hasattr(client, 'scroll'),
        'retrieve': hasattr(client, 'retrieve'),
    }
    
    print("\nMétodos disponibles:")
    for method, available in methods.items():
        status = "✓" if available else "✗"
        print(f"  {status} {method}")
    
    return methods


def determine_api_version(methods: dict) -> str:
    """Determina qué versión de API usar."""
    print("\nAnálisis de compatibilidad:")
    
    if methods.get('query_points'):
        print("  → Detectado: API v2 (qdrant-client >= 1.7.0)")
        print("  → Usar: client.query_points(collection_name=..., query=vector, limit=k)")
        return "v2"
    elif methods.get('search'):
        print("  → Detectado: API v1 (qdrant-client < 1.7.0)")
        print("  → Usar: client.search(collection_name=..., query_vector=vector, limit=k)")
        return "v1"
    else:
        print("  ✗ No se encontró método de búsqueda compatible")
        print("  → Actualizar qdrant-client: pip install --upgrade qdrant-client")
        return None


def test_connection(url: str = None) -> bool:
    """Prueba conexión al servidor Qdrant."""
    url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
    
    print(f"\n{'='*60}")
    print(f"Probando conexión a: {url}")
    print('='*60)
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=url, timeout=5)
        
        # Intentar obtener colecciones
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        print(f"✓ Conexión exitosa")
        print(f"  Colecciones encontradas: {len(collection_names)}")
        
        if collection_names:
            print(f"  Nombres: {collection_names}")
            
            # Mostrar info de cada colección
            for name in collection_names[:3]:  # Limitar a 3
                try:
                    info = client.get_collection(name)
                    print(f"\n  Colección '{name}':")
                    print(f"    - Puntos: {info.points_count}")
                    print(f"    - Estado: {info.status}")
                except Exception as e:
                    print(f"    - Error obteniendo info: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        print("\n  Posibles soluciones:")
        print("  1. Verificar que Qdrant esté corriendo")
        print("  2. Verificar URL y puerto")
        print("  3. Si usa Docker: docker-compose up -d qdrant")
        return False


def test_search_functionality(url: str = None) -> bool:
    """Prueba la funcionalidad de búsqueda."""
    url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
    
    print(f"\n{'='*60}")
    print("Probando funcionalidad de búsqueda")
    print('='*60)
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=url, timeout=5)
        
        # Obtener primera colección disponible
        collections = client.get_collections().collections
        if not collections:
            print("⚠ No hay colecciones para probar búsqueda")
            return True  # No es un error, solo no hay datos
        
        collection_name = collections[0].name
        print(f"  Usando colección: {collection_name}")
        
        # Obtener dimensión del vector
        info = client.get_collection(collection_name)
        try:
            # Intentar obtener dimensión de diferentes formas
            if hasattr(info.config.params, 'vectors'):
                if hasattr(info.config.params.vectors, 'size'):
                    vector_size = info.config.params.vectors.size
                else:
                    vector_size = 384  # Default
            else:
                vector_size = 384
        except Exception:
            vector_size = 384
        
        print(f"  Dimensión de vectores: {vector_size}")
        
        # Crear vector de prueba
        dummy_vector = [0.1] * vector_size
        
        # Probar búsqueda con el método disponible
        if hasattr(client, 'query_points'):
            print("  Método: query_points (v2)")
            response = client.query_points(
                collection_name=collection_name,
                query=dummy_vector,
                limit=3
            )
            results = response.points if hasattr(response, 'points') else response
        elif hasattr(client, 'search'):
            print("  Método: search (v1)")
            results = client.search(
                collection_name=collection_name,
                query_vector=dummy_vector,
                limit=3
            )
        else:
            print("✗ No se encontró método de búsqueda")
            return False
        
        print(f"✓ Búsqueda exitosa")
        print(f"  Resultados encontrados: {len(results)}")
        
        for i, hit in enumerate(results[:3]):
            score = hit.score if hasattr(hit, 'score') else 0
            print(f"    {i+1}. ID: {hit.id}, Score: {score:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en búsqueda: {e}")
        return False


def generate_code_recommendation(api_version: str) -> None:
    """Genera recomendación de código basada en la versión de API."""
    print(f"\n{'='*60}")
    print("Código recomendado para tu versión")
    print('='*60)
    
    if api_version == "v2":
        print("""
# Para qdrant-client >= 1.7.0 (tu versión)

from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Búsqueda
response = client.query_points(
    collection_name="my_collection",
    query=query_vector,        # Nota: 'query', no 'query_vector'
    limit=5,
    score_threshold=0.7        # Opcional
)

# Extraer resultados
results = response.points

# Formatear
for hit in results:
    print(f"ID: {hit.id}, Score: {hit.score}")
    print(f"Payload: {hit.payload}")
""")
    elif api_version == "v1":
        print("""
# Para qdrant-client < 1.7.0 (tu versión)

from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Búsqueda
results = client.search(
    collection_name="my_collection",
    query_vector=query_vector,  # Nota: 'query_vector', no 'query'
    limit=5,
    score_threshold=0.7         # Opcional
)

# Formatear (results ya es una lista)
for hit in results:
    print(f"ID: {hit.id}, Score: {hit.score}")
    print(f"Payload: {hit.payload}")
""")
    else:
        print("""
# No se pudo determinar la versión de API.
# Instala o actualiza qdrant-client:

pip install --upgrade qdrant-client
""")


def main():
    """Ejecuta todas las verificaciones."""
    parser = argparse.ArgumentParser(
        description="Verifica compatibilidad de qdrant-client"
    )
    parser.add_argument(
        '--test-connection', '-t',
        action='store_true',
        help='Probar conexión al servidor Qdrant'
    )
    parser.add_argument(
        '--test-search', '-s',
        action='store_true',
        help='Probar funcionalidad de búsqueda'
    )
    parser.add_argument(
        '--url', '-u',
        type=str,
        default=None,
        help='URL del servidor Qdrant (default: QDRANT_URL env o localhost:6333)'
    )
    parser.add_argument(
        '--show-code', '-c',
        action='store_true',
        help='Mostrar código de ejemplo para tu versión'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Verificación de Compatibilidad Qdrant Client")
    print("=" * 60)
    
    # Verificar instalación
    if not check_qdrant_client_installed():
        print("\n✗ qdrant-client no está instalado")
        print("  Instalar con: pip install qdrant-client")
        sys.exit(1)
    
    # Verificar versión
    version = check_qdrant_client_version()
    if not version:
        sys.exit(1)
    
    # Verificar métodos disponibles
    methods = check_available_methods()
    
    # Determinar versión de API
    api_version = determine_api_version(methods)
    if not api_version:
        sys.exit(1)
    
    # Mostrar código de ejemplo
    if args.show_code:
        generate_code_recommendation(api_version)
    
    # Probar conexión si se solicita
    if args.test_connection:
        if not test_connection(args.url):
            print("\n⚠ La conexión falló, pero la librería está correctamente instalada")
    
    # Probar búsqueda si se solicita
    if args.test_search:
        if not test_search_functionality(args.url):
            print("\n⚠ La búsqueda falló")
    
    print("\n" + "=" * 60)
    print("Verificación completada")
    print("=" * 60)
    
    # Resumen final
    print(f"\nResumen:")
    print(f"  - qdrant-client: {version}")
    print(f"  - API detectada: {api_version}")
    print(f"  - Método recomendado: {'query_points' if api_version == 'v2' else 'search'}")
    
    if not args.show_code:
        print(f"\n  Tip: Usa --show-code para ver ejemplo de código")
    if not args.test_connection:
        print(f"  Tip: Usa --test-connection para probar conexión al servidor")


if __name__ == "__main__":
    main()