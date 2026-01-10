# 🔹 PROMPT EJECUTABLE 11 — Embeddings Reales (OpenAI/OpenRouter)

> **Archivo**: `specs/prompts/11_embeddings_reales.md`  
> **Subproyecto**: 11 de 13 (extensión)  
> **Prerequisitos**: Subproyectos 1-10 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Reemplazar embeddings dummy por llamadas reales a API
- Soportar OpenAI embeddings y alternativas vía OpenRouter
- Mantener compatibilidad con el código existente

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- Actualmente el sistema usa embeddings DUMMY (vectores pseudo-aleatorios)
- Esto hace que el retrieval NO funcione correctamente en producción
- Necesitamos embeddings reales para búsqueda semántica funcional
- OpenAI `text-embedding-ada-002` tiene dimensión 1536 (ya configurada)
- OpenAI `text-embedding-3-small` tiene dimensión 1536 también
- Se puede usar OpenRouter como proxy para embeddings

---

## OBJETIVO

Implementar generación de embeddings reales usando:
1. OpenAI API directamente (opción principal)
2. Modelo local con sentence-transformers (opción fallback/offline)

**Éxito binario**: El retrieval devuelve chunks semánticamente relevantes a la pregunta.

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/embeddings/
├── __init__.py
├── base.py
├── openai_embeddings.py
└── local_embeddings.py

services/api/app/retrieval.py          # MODIFICAR
services/ingest/worker.py              # MODIFICAR
services/api/requirements.txt          # MODIFICAR
```

---

## CONTENIDO DE ARCHIVOS

### services/api/app/embeddings/__init__.py

```python
"""
Módulo de embeddings - genera vectores semánticos para texto.
"""
from .base import EmbeddingProvider, get_embedding_provider
from .openai_embeddings import OpenAIEmbeddings
from .local_embeddings import LocalEmbeddings

__all__ = [
    "EmbeddingProvider",
    "get_embedding_provider", 
    "OpenAIEmbeddings",
    "LocalEmbeddings"
]
```

### services/api/app/embeddings/base.py

```python
"""
Clase base abstracta para proveedores de embeddings.
"""
import os
from abc import ABC, abstractmethod
from typing import List, Optional

class EmbeddingProvider(ABC):
    """Interfaz base para proveedores de embeddings."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión de los vectores generados."""
        pass


# Singleton del provider
_embedding_provider: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """
    Obtiene el provider de embeddings configurado.
    
    Prioridad:
    1. OpenAI si OPENAI_API_KEY está configurado
    2. Local (sentence-transformers) como fallback
    """
    global _embedding_provider
    
    if _embedding_provider is not None:
        return _embedding_provider
    
    # Intentar OpenAI primero
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        from .openai_embeddings import OpenAIEmbeddings
        _embedding_provider = OpenAIEmbeddings(api_key=openai_key)
        print("[Embeddings] Usando OpenAI embeddings")
        return _embedding_provider
    
    # Fallback a local
    print("[Embeddings] OPENAI_API_KEY no encontrado, usando embeddings locales")
    from .local_embeddings import LocalEmbeddings
    _embedding_provider = LocalEmbeddings()
    return _embedding_provider


def set_embedding_provider(provider: EmbeddingProvider):
    """Permite configurar un provider específico (útil para testing)."""
    global _embedding_provider
    _embedding_provider = provider
```

### services/api/app/embeddings/openai_embeddings.py

```python
"""
Proveedor de embeddings usando OpenAI API.
"""
import httpx
from typing import List, Optional
from .base import EmbeddingProvider

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"


class OpenAIEmbeddings(EmbeddingProvider):
    """
    Genera embeddings usando la API de OpenAI.
    
    Modelos soportados:
    - text-embedding-ada-002 (1536 dims, más barato)
    - text-embedding-3-small (1536 dims, más nuevo)
    - text-embedding-3-large (3072 dims, mejor calidad)
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "text-embedding-ada-002",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._dimension = self._get_dimension_for_model(model)
    
    def _get_dimension_for_model(self, model: str) -> int:
        """Retorna la dimensión según el modelo."""
        dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        return dimensions.get(model, 1536)
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        embeddings = await self.embed_batch([text])
        return embeddings[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos.
        
        OpenAI soporta hasta 2048 textos por request.
        """
        if not texts:
            return []
        
        # Limpiar textos (remover newlines excesivos, limitar longitud)
        cleaned_texts = [self._clean_text(t) for t in texts]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": cleaned_texts
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                OPENAI_EMBEDDINGS_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                error_msg = f"OpenAI Embeddings error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                raise Exception(error_msg)
            
            data = response.json()
            
            # Ordenar por índice (OpenAI puede retornarlos desordenados)
            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            
            return [item["embedding"] for item in embeddings_data]
    
    def _clean_text(self, text: str, max_tokens: int = 8000) -> str:
        """
        Limpia y trunca texto para embeddings.
        
        text-embedding-ada-002 soporta hasta 8191 tokens.
        Estimamos ~4 chars por token como aproximación.
        """
        # Remover newlines múltiples
        text = " ".join(text.split())
        
        # Truncar si es muy largo (estimación conservadora)
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        
        return text


class OpenRouterEmbeddings(EmbeddingProvider):
    """
    Genera embeddings usando OpenRouter como proxy.
    Útil si ya tienes cuenta en OpenRouter.
    
    Nota: OpenRouter tiene soporte limitado para embeddings.
    Usar OpenAI directo es preferible.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-ada-002",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._dimension = 1536  # Default para ada-002
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed_text(self, text: str) -> List[float]:
        embeddings = await self.embed_batch([text])
        return embeddings[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        OpenRouter usa el mismo formato que OpenAI para embeddings.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "rag-onpremise"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter Embeddings error: {response.status_code}")
            
            data = response.json()
            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings_data]
```

### services/api/app/embeddings/local_embeddings.py

```python
"""
Proveedor de embeddings usando modelos locales (sentence-transformers).

Ventajas:
- Sin costo por API call
- Funciona offline
- Sin límites de rate

Desventajas:
- Requiere más RAM/CPU
- Calidad puede ser menor que OpenAI
- Primera carga es lenta (descarga modelo)
"""
from typing import List, Optional
from .base import EmbeddingProvider

# Flag para verificar si sentence-transformers está disponible
_sentence_transformers_available = False
_model = None

try:
    from sentence_transformers import SentenceTransformer
    _sentence_transformers_available = True
except ImportError:
    pass


class LocalEmbeddings(EmbeddingProvider):
    """
    Genera embeddings usando sentence-transformers localmente.
    
    Modelos recomendados:
    - all-MiniLM-L6-v2: Rápido, 384 dims (default)
    - all-mpnet-base-v2: Mejor calidad, 768 dims
    - paraphrase-multilingual-MiniLM-L12-v2: Multilingüe, 384 dims
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """
        Args:
            model_name: Nombre del modelo de HuggingFace
            device: 'cpu' o 'cuda' para GPU
        """
        if not _sentence_transformers_available:
            raise ImportError(
                "sentence-transformers no está instalado. "
                "Instalar con: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dimension = self._get_dimension_for_model(model_name)
    
    def _get_dimension_for_model(self, model_name: str) -> int:
        """Retorna la dimensión según el modelo."""
        dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-multilingual-MiniLM-L12-v2": 384,
            "all-MiniLM-L12-v2": 384,
        }
        return dimensions.get(model_name, 384)
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _get_model(self):
        """Carga lazy del modelo."""
        if self._model is None:
            print(f"[LocalEmbeddings] Cargando modelo {self.model_name}...")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            print(f"[LocalEmbeddings] Modelo cargado")
        return self._model
    
    async def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos."""
        if not texts:
            return []
        
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()


class DummyEmbeddings(EmbeddingProvider):
    """
    Embeddings dummy para testing.
    NO usar en producción.
    """
    
    def __init__(self, dimension: int = 1536):
        self._dimension = dimension
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed_text(self, text: str) -> List[float]:
        import hashlib
        import random
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        random.seed(hash_val)
        return [random.uniform(-1, 1) for _ in range(self._dimension)]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]
```

---

### MODIFICAR: services/api/app/retrieval.py

```python
"""
Módulo de retrieval: genera embeddings y busca contexto relevante.
MODIFICADO: Usa embeddings reales en lugar de dummy.
"""
from typing import List, Dict, Any, Optional

from app.qdrant_client import search
from app.embeddings import get_embedding_provider


async def get_embedding(text: str) -> List[float]:
    """
    Genera embedding para un texto usando el provider configurado.
    
    Args:
        text: Texto a vectorizar
    
    Returns:
        Vector de embeddings
    """
    provider = get_embedding_provider()
    return await provider.embed_text(text)


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings para múltiples textos (más eficiente).
    
    Args:
        texts: Lista de textos a vectorizar
    
    Returns:
        Lista de vectores
    """
    provider = get_embedding_provider()
    return await provider.embed_batch(texts)


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

### MODIFICAR: services/ingest/worker.py (función generate_embeddings)

Reemplazar la función `generate_embeddings_dummy` por:

```python
import asyncio
import sys
import os

# Añadir path para imports del API
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from app.embeddings import get_embedding_provider


def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """
    Genera embeddings reales para los chunks.
    
    Usa el provider configurado (OpenAI o local).
    """
    provider = get_embedding_provider()
    
    # Ejecutar async en sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        embeddings = loop.run_until_complete(provider.embed_batch(chunks))
    finally:
        loop.close()
    
    return embeddings


# DEPRECATED: Mantener para compatibilidad/testing
def generate_embeddings_dummy(chunks: List[str]) -> List[List[float]]:
    """
    DEPRECATED: Genera embeddings dummy.
    Solo usar para testing sin API key.
    """
    import hashlib
    import random
    
    vectors = []
    for chunk in chunks:
        hash_val = int(hashlib.md5(chunk.encode()).hexdigest(), 16)
        random.seed(hash_val)
        vectors.append([random.uniform(-1, 1) for _ in range(1536)])
    return vectors
```

---

### MODIFICAR: services/api/requirements.txt

Añadir estas dependencias:

```
# Embeddings
httpx==0.26.0

# Embeddings locales (opcional, descomentar si se usa)
# sentence-transformers==2.2.2
# torch==2.1.0
```

---

## CONFIGURACIÓN

### Variables de entorno (.env)

```bash
# Para embeddings OpenAI (recomendado)
OPENAI_API_KEY=sk-xxx

# Modelo de embeddings (opcional, default: text-embedding-ada-002)
EMBEDDING_MODEL=text-embedding-ada-002

# Alternativa: usar OpenRouter para embeddings
# OPENROUTER_API_KEY=sk-or-xxx
# EMBEDDING_PROVIDER=openrouter
```

### Configuración en client.yaml (futuro)

```yaml
embeddings:
  provider: "openai"  # openai, openrouter, local
  model: "text-embedding-ada-002"
  # Para local:
  # provider: "local"
  # model: "all-MiniLM-L6-v2"
```

---

## VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# 1. Verificar que OPENAI_API_KEY está configurado
echo $OPENAI_API_KEY

# 2. Rebuild del servicio API
docker compose -f deploy/compose/docker-compose.yml build api

# 3. Reiniciar
docker compose -f deploy/compose/docker-compose.yml up -d

# 4. Reiniciar worker de ingestión
docker compose -f deploy/compose/docker-compose.yml restart ingest-worker

# 5. Reingestar un documento de prueba
# (Colocar un .txt en data/sources/<rag_id>/incoming/)
python -m services.ingest.cli submit --rag test

# 6. Probar retrieval
curl -X POST http://localhost/api/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "test", "question": "tema del documento"}'

# 7. Verificar que context_chunks contiene texto RELEVANTE a la pregunta
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] Los embeddings se generan sin error (revisar logs del worker)
- [ ] `/query` devuelve chunks semánticamente relevantes (no aleatorios)
- [ ] El score de los chunks varía según la relevancia de la pregunta

---

## TEST DE RELEVANCIA

Para verificar que embeddings funcionan correctamente:

```bash
# 1. Crear documento de prueba
echo "Python es un lenguaje de programación interpretado" > data/sources/test/incoming/python.txt
echo "FastAPI es un framework web moderno para Python" >> data/sources/test/incoming/python.txt

# 2. Ingestar
python -m services.ingest.cli submit --rag test

# 3. Consulta relevante (debería tener score alto)
curl -X POST http://localhost/api/query \
  -d '{"rag_id":"test","question":"¿Qué es FastAPI?"}'

# 4. Consulta no relevante (debería tener score bajo o no resultados)
curl -X POST http://localhost/api/query \
  -d '{"rag_id":"test","question":"¿Cuál es la capital de Francia?"}'
```

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| OPENAI_API_KEY not set | Variable no configurada | Añadir al .env |
| 401 Unauthorized | API key inválida | Verificar key en OpenAI dashboard |
| Dimension mismatch | Modelo embeddings cambió | Recrear colección en Qdrant |
| Rate limit exceeded | Muchos requests a OpenAI | Añadir rate limiting o usar batch |
| sentence-transformers not found | No instalado | pip install sentence-transformers |

---

## COSTOS ESTIMADOS (OpenAI)

| Modelo | Precio | Tokens por consulta | Costo aprox |
|--------|--------|---------------------|-------------|
| text-embedding-ada-002 | $0.0001/1K tokens | ~100-500 | $0.00001-0.00005 |
| text-embedding-3-small | $0.00002/1K tokens | ~100-500 | $0.000002-0.00001 |

Para 10,000 consultas/día: ~$0.10-0.50/día con ada-002

---

## LO QUE SE CONGELA

✅ Interfaz `EmbeddingProvider` con `embed_text` y `embed_batch`  
✅ Función `get_embedding_provider()` para obtener provider  
✅ Compatibilidad con dimensión 1536 (OpenAI default)

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 12**: Cargador de configuración YAML + procesador PDF