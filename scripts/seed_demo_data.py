"""
Script para poblar datos de demostración en Qdrant.
Útil para validar que el sistema funciona end-to-end.

Uso:
    python scripts/seed_demo_data.py
"""
import os
import sys
import uuid
import random
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.http import models


def seed_demo_data():
    """Inserta datos de demostración en Qdrant."""
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    
    rag_id = "demo"
    collection_name = f"{rag_id}_collection"
    vector_dim = 1536
    
    # Crear colección
    print(f"Creando colección: {collection_name}")
    try:
        client.delete_collection(collection_name)
        print(f"Colección anterior eliminada")
    except Exception as e:
        print(f"No había colección anterior: {e}")
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_dim,
            distance=models.Distance.COSINE
        )
    )
    print(f"✅ Colección creada: {collection_name}")
    
    # Datos de ejemplo
    demo_chunks = [
        {
            "text": "FastAPI es un framework web moderno y rápido para construir APIs con Python.",
            "source": "docs/fastapi.txt"
        },
        {
            "text": "Qdrant es una base de datos vectorial diseñada para búsqueda de similitud.",
            "source": "docs/qdrant.txt"
        },
        {
            "text": "Redis es un almacén de estructuras de datos en memoria, usado como base de datos, caché y broker de mensajes.",
            "source": "docs/redis.txt"
        },
        {
            "text": "Los embeddings son representaciones numéricas de texto que capturan su significado semántico.",
            "source": "docs/embeddings.txt"
        },
        {
            "text": "RAG (Retrieval Augmented Generation) combina búsqueda de información con generación de lenguaje.",
            "source": "docs/rag.txt"
        },
        {
            "text": "Docker es una plataforma para containerizar aplicaciones y simplificar el deployment.",
            "source": "docs/docker.txt"
        },
        {
            "text": "Python es un lenguaje de programación versátil usado en ciencia de datos, web y machine learning.",
            "source": "docs/python.txt"
        }
    ]
    
    # Generar vectores dummy (en producción serían embeddings reales)
    points = []
    for i, chunk in enumerate(demo_chunks):
        random.seed(hash(chunk["text"]))
        vector = [random.uniform(-1, 1) for _ in range(vector_dim)]
        
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk["text"],
                "source_path": chunk["source"],
                "page": 0,
                "chunk_index": i
            }
        ))
    
    # Insertar
    client.upsert(collection_name=collection_name, points=points)
    print(f"✅ Insertados {len(points)} puntos de demostración")
    
    # Verificar
    info = client.get_collection(collection_name)
    print(f"✅ Colección {collection_name}: {info.points_count} puntos")
    print(f"✅ Vector size: {info.config.params.vectors.size} dimensions")


if __name__ == "__main__":
    try:
        seed_demo_data()
        print("\n✅ Datos de demostración insertados correctamente")
    except Exception as e:
        print(f"\n❌ Error al insertar datos: {e}")
        sys.exit(1)