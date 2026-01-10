# 🔹 PROMPT EJECUTABLE 06 — Integración Qdrant + Embeddings + Retrieval

> **Archivo**: `specs/prompts/06_qdrant_retrieval.md`  
> **Subproyecto**: 6 de 10  
> **Prerequisitos**: Subproyectos 1-5 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Implementar integración mínima con Qdrant respetando contratos existentes
- No cambiar schemas de `/query` definidos en Subproyecto 5
- No rediseñar arquitectura

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO DEL SISTEMA

- Qdrant es vector DB en contenedor (ya levantado en docker-compose)
- Multi-RAG: una colección por RAG
- Embeddings: modelo configurable por YAML (definido en Subproyecto 3)
- Ingestión: worker consume cola y hace upsert
- Consulta: API hace search top_k y arma contexto

---

## OBJETIVO

Implementar:
- Cliente Qdrant
- Creación/validación de colección por RAG
- Upsert de puntos con payload mínimo
- Búsqueda top_k para `/query`

**Éxito binario**: `/query` devuelve `context_chunks` reales desde Qdrant (con datos de prueba).

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/qdrant_client.py    (CREAR)
services/api/app/retrieval.py        (CREAR)
services/api/app/routes/query.py     (MODIFICAR)
services/ingest/worker.py            (MODIFICAR - añadir lógica real)
scripts/seed_demo_data.py            (CREAR - opcional para testing)
docs/qdrant.md                       (CREAR)
```

---

## CONTENIDO DE ARCHIVOS

### services/api/app/qdrant_client.py

```python
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

_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    """Obtiene o crea instancia singleton del cliente Qdrant."""
    global _client
    if _client is None:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY", None)
        _client = QdrantClient(url=url, api_key=api_key if api_key else None)
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
    
    return True


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
    
    return len(points)


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
    
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold
    )
    
    return [
        {
            "id": str(hit.id),
            "source": hit.payload.get("source_path", ""),
            "text": hit.payload.get("text", ""),
            "score": hit.score
        }
        for hit in results
    ]


def delete_collection(collection_name: str) -> bool:
    """Elimina una colección (usado para reindex)."""
    client = get_client()
    client.delete_collection(collection_name=collection_name)
    return True
```

---

### services/api/app/retrieval.py

```python
"""
Módulo de retrieval: genera embeddings y busca contexto relevante.

Funciones:
- get_embedding(): Genera embedding para texto
- retrieve_context(): Busca chunks relevantes para una pregunta
"""
from typing import List, Dict, Any, Optional
import os
import httpx

from app.qdrant_client import search


async def get_embedding(text: str, model_name: str = None) -> List[float]:
    """
    Genera embedding para un texto usando OpenRouter o modelo configurado.
    
    Args:
        text: Texto a vectorizar
        model_name: Modelo de embeddings (default: text-embedding-ada-002)
    
    Returns:
        Vector de embeddings
    """
    # TODO: Implementar llamada real a API de embeddings
    # Por ahora, placeholder que retorna vector dummy para testing
    
    model = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Placeholder: retornar vector de dimensión 1536 (OpenAI ada-002)
    # En producción, llamar a la API real
    import hashlib
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    
    # Generar vector pseudo-aleatorio pero determinístico
    import random
    random.seed(hash_val)
    return [random.uniform(-1, 1) for _ in range(1536)]


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
    query_vector = await get_embedding(question)
    
    # Buscar en Qdrant
    # Por convención, collection_name = rag_id + "_collection"
    collection_name = f"{rag_id}_collection"
    
    results = search(
        collection_name=collection_name,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=score_threshold
    )
    
    return results
```

---

### services/api/app/routes/query.py (MODIFICAR)

```python
"""
Endpoint principal de consulta RAG.
MODIFICADO: Ahora llama a retrieval real en lugar de dummy.
"""
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse, ContextChunk
from app.retrieval import retrieve_context

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Procesa una consulta RAG.
    
    Flujo:
    1. Generar embedding de la pregunta
    2. Buscar chunks relevantes en Qdrant
    3. (Futuro) Llamar a LLM con contexto
    4. Retornar respuesta
    """
    start_time = time.time()
    
    # Generar session_id si no se provee
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Recuperar contexto de Qdrant
        top_k = request.top_k or 5
        chunks = await retrieve_context(
            rag_id=request.rag_id,
            question=request.question,
            top_k=top_k
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
        
        # Respuesta (LLM aún no implementado)
        answer = "NOT_IMPLEMENTED - Contexto recuperado, falta integración LLM"
        if not context_chunks:
            answer = "No se encontró contexto relevante para tu pregunta."
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            rag_id=request.rag_id,
            answer=answer,
            context_chunks=context_chunks,
            latency_ms=latency_ms,
            cache_hit=False,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en retrieval: {str(e)}"
        )
```

---

### services/ingest/worker.py (MODIFICAR)

```python
"""
Worker de ingestión que consume jobs de la cola Redis.
MODIFICADO: Añadida lógica real de procesamiento.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Añadir path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import redis

# Import del cliente Qdrant (relativo al proyecto)
# En producción, ajustar según estructura de imports


def get_redis_client():
    """Obtiene cliente Redis."""
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url)


def update_job_status(redis_client, job_id: str, status: str, meta: dict = None):
    """Actualiza estado de un job en Redis."""
    redis_client.set(f"rag:job:{job_id}:status", status)
    if meta:
        redis_client.set(f"rag:job:{job_id}:meta", json.dumps(meta))


def read_source(path: str, source_type: str) -> str:
    """Lee contenido de un archivo fuente."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def chunk_text_simple(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Divide texto en chunks (implementación simple).
    En producción, usar LangChain splitters según config.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def generate_embeddings_dummy(chunks: List[str]) -> List[List[float]]:
    """
    Genera embeddings dummy (determinísticos por contenido).
    En producción, llamar a API de embeddings real.
    """
    import hashlib
    import random
    
    vectors = []
    for chunk in chunks:
        hash_val = int(hashlib.md5(chunk.encode()).hexdigest(), 16)
        random.seed(hash_val)
        vectors.append([random.uniform(-1, 1) for _ in range(1536)])
    return vectors


def process_job(job: dict) -> bool:
    """
    Procesa un job de ingestión.
    
    1. Leer archivo
    2. Dividir en chunks
    3. Generar embeddings
    4. Upsert a Qdrant
    5. Mover archivo a processed/failed
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    
    job_id = job["job_id"]
    rag_id = job["rag_id"]
    source_path = job["source_path"]
    source_type = job.get("source_type", "txt")
    
    redis_client = get_redis_client()
    update_job_status(redis_client, job_id, "processing")
    
    try:
        # 1. Leer archivo
        print(f"[Worker] Leyendo {source_path}")
        
        if source_type == "pdf":
            # TODO: Implementar lectura PDF con PyPDF o similar
            text = f"[PDF no implementado] {source_path}"
        else:
            text = read_source(source_path, source_type)
        
        # 2. Chunking
        print(f"[Worker] Chunking texto ({len(text)} chars)")
        chunks = chunk_text_simple(text)
        print(f"[Worker] {len(chunks)} chunks generados")
        
        # 3. Generar embeddings
        print(f"[Worker] Generando embeddings")
        vectors = generate_embeddings_dummy(chunks)
        
        # 4. Upsert a Qdrant
        print(f"[Worker] Upserting a Qdrant")
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)
        
        collection_name = f"{rag_id}_collection"
        
        # Asegurar que la colección existe
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE
                )
            )
        
        # Preparar puntos
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload={
                    "source_path": source_path,
                    "page": 0,
                    "chunk_index": i,
                    "text": chunk
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        client.upsert(collection_name=collection_name, points=points)
        print(f"[Worker] {len(points)} puntos insertados en {collection_name}")
        
        # 5. Mover archivo a processed
        source = Path(source_path)
        processed_dir = source.parent.parent / "processed"
        processed_dir.mkdir(exist_ok=True)
        dest = processed_dir / source.name
        source.rename(dest)
        print(f"[Worker] Archivo movido a {dest}")
        
        update_job_status(redis_client, job_id, "done", {
            "chunks": len(chunks),
            "collection": collection_name
        })
        
        return True
        
    except Exception as e:
        print(f"[Worker] Error procesando job: {e}")
        update_job_status(redis_client, job_id, "failed", {
            "error": str(e)
        })
        
        # Mover a failed
        try:
            source = Path(source_path)
            failed_dir = source.parent.parent / "failed"
            failed_dir.mkdir(exist_ok=True)
            source.rename(failed_dir / source.name)
        except:
            pass
        
        return False


def run_worker():
    """Loop principal del worker."""
    print("[Worker] Iniciando worker de ingestión...")
    redis_client = get_redis_client()
    queue_key = "rag:ingest:queue"
    
    while True:
        try:
            # Esperar job de la cola (blocking)
            result = redis_client.brpop(queue_key, timeout=5)
            
            if result:
                _, job_data = result
                job = json.loads(job_data)
                print(f"[Worker] Job recibido: {job['job_id']}")
                process_job(job)
            
        except KeyboardInterrupt:
            print("[Worker] Detenido por usuario")
            break
        except Exception as e:
            print(f"[Worker] Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
```

---

### scripts/seed_demo_data.py

```python
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

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.http import models


def seed_demo_data():
    """Inserta datos de demostración."""
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    
    rag_id = "demo"
    collection_name = f"{rag_id}_collection"
    vector_dim = 1536
    
    # Crear colección
    print(f"Creando colección: {collection_name}")
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_dim,
            distance=models.Distance.COSINE
        )
    )
    
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
    print(f"Insertados {len(points)} puntos de demostración")
    
    # Verificar
    info = client.get_collection(collection_name)
    print(f"Colección {collection_name}: {info.points_count} puntos")


if __name__ == "__main__":
    seed_demo_data()
    print("✅ Datos de demostración insertados")
```

---

### docs/qdrant.md

```markdown
# Integración con Qdrant

## Descripción

Qdrant es la base de datos vectorial usada para almacenar y buscar embeddings de los chunks de documentos.

## Arquitectura

- **Una colección por RAG**: Cada `rag_id` tiene su propia colección llamada `{rag_id}_collection`
- **Distancia**: Coseno (COSINE)
- **Dimensión**: Configurable por RAG (default: 1536 para OpenAI ada-002)

## Payload por Chunk

Cada punto en Qdrant contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `source_path` | string | Ruta del archivo fuente |
| `page` | int | Número de página (para PDFs) |
| `chunk_index` | int | Índice del chunk en el documento |
| `text` | string | Contenido textual del chunk |

## Operaciones Disponibles

### Cliente (`qdrant_client.py`)

- `get_client()`: Obtener instancia singleton
- `ensure_collection(name, dim)`: Crear colección si no existe
- `upsert_chunks(collection, chunks, vectors)`: Insertar/actualizar
- `search(collection, vector, top_k)`: Buscar similares
- `delete_collection(name)`: Eliminar colección (para reindex)

### Retrieval (`retrieval.py`)

- `get_embedding(text)`: Generar embedding (placeholder)
- `retrieve_context(rag_id, question, top_k)`: Buscar contexto relevante

## Configuración

Variables de entorno:
- `QDRANT_URL`: URL del servidor (default: `http://localhost:6333`)
- `QDRANT_API_KEY`: API key opcional

## Testing

```bash
# Poblar datos de demo
python scripts/seed_demo_data.py

# Verificar colección
curl http://localhost:6333/collections

# Probar búsqueda via API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "demo", "question": "¿Qué es FastAPI?"}'
```

## Notas

- Los embeddings actuales son DUMMY (pseudo-aleatorios)
- En producción, implementar llamada real a API de embeddings
- El worker de ingestión crea la colección automáticamente si no existe
```

---

## COMANDOS DE VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# 1. Rebuild de servicios
docker compose -f deploy/compose/docker-compose.yml build api ingest-worker

# 2. Levantar stack completo
docker compose -f deploy/compose/docker-compose.yml up -d

# 3. Ver logs del worker
docker compose -f deploy/compose/docker-compose.yml logs -f ingest-worker

# 4. Poblar datos de demo (desde host o dentro del contenedor)
python scripts/seed_demo_data.py

# 5. Verificar colección en Qdrant
curl http://localhost:6333/collections

# 6. Probar endpoint /query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "demo", "question": "¿Qué es RAG?"}'
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] La colección existe en Qdrant (`curl http://localhost:6333/collections`)
- [ ] `/query` devuelve `context_chunks` con datos reales (no vacío)
- [ ] El score es numérico y entre 0 y 1
- [ ] El texto en los chunks corresponde a los datos insertados

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| Collection not found | Colección no creada | Ejecutar seed_demo_data.py o submit via CLI |
| Dimension mismatch | Vector de distinta dimensión | Verificar que embeddings tienen dim=1536 |
| Empty context_chunks | Colección vacía o rag_id incorrecto | Verificar nombre de colección |
| Connection refused | Qdrant no levantado | docker compose up -d qdrant |

---

## LO QUE SE CONGELA

✅ Estructura de payload por chunk: `source_path`, `page`, `chunk_index`, `text`  
✅ Convención de nombre de colección: `{rag_id}_collection`  
✅ Interfaz del cliente Qdrant  

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 7**: Redis - caché de respuestas, sesiones, rate limiting por RAG