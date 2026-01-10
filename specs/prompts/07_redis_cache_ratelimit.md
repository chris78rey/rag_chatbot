# 🔹 PROMPT EJECUTABLE 07 — Redis: Caché, Sesiones y Rate Limiting

> **Archivo**: `specs/prompts/07_redis_cache_ratelimit.md`  
> **Subproyecto**: 7 de 10  
> **Prerequisitos**: Subproyectos 1-6 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Implementar cache/sessions/rate-limit en FastAPI con Redis
- No rediseñar arquitectura
- No cambiar contrato de `/query`

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO DEL SISTEMA

- Redis ya se usa como broker para ingestión (cola de jobs)
- Caché: hash(query + rag_id + params) con TTL por RAG
- Sesiones: historial corto por session_id con TTL
- Rate limit: configurable por RAG (rps/burst) y aplicable en API (complementario a Nginx)

---

## OBJETIVO

Implementar utilidades Redis y middleware simple para:
- Cache hit/miss en `/query`
- Session store (historial de conversación)
- Rate limiting por RAG

**Éxito binario**: `/query` marca `cache_hit=true` al repetir la consulta y aplica 429 cuando excede límites.

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/redis_client.py    # CREAR
services/api/app/cache.py           # CREAR
services/api/app/sessions.py        # CREAR
services/api/app/rate_limit.py      # CREAR
services/api/app/routes/query.py    # MODIFICAR (integrar cache/rate-limit)
docs/redis.md                       # CREAR
```

---

## CONTENIDO DE ARCHIVOS

### 1. `services/api/app/redis_client.py`

```python
"""
Cliente Redis singleton para el API.

Responsabilidades:
- Conexión única a Redis
- Helpers para operaciones comunes
- Manejo de errores de conexión
"""
import os
from typing import Optional
import redis.asyncio as redis

# Singleton del cliente Redis
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Obtiene el cliente Redis (singleton).
    
    Returns:
        Cliente Redis async conectado
    """
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def close_redis():
    """Cierra la conexión Redis."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def redis_healthcheck() -> bool:
    """
    Verifica conexión a Redis.
    
    Returns:
        True si Redis responde, False si hay error
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False
```

### 2. `services/api/app/cache.py`

```python
"""
Sistema de caché de respuestas usando Redis.

Estrategia:
- Key: hash de (rag_id + question + top_k)
- Value: JSON con respuesta completa
- TTL: configurable por RAG
"""
import json
import hashlib
from typing import Optional, Any

from app.redis_client import get_redis

# Prefijo para keys de caché
CACHE_PREFIX = "rag:cache:"


def build_cache_key(rag_id: str, question: str, top_k: Optional[int] = None) -> str:
    """
    Construye la key de caché única para una consulta.
    
    Args:
        rag_id: ID del RAG
        question: Pregunta del usuario
        top_k: Parámetro top_k (afecta el resultado)
    
    Returns:
        Key de caché con hash
    """
    # Normalizar pregunta (lowercase, strip)
    normalized_q = question.lower().strip()
    
    # Crear string para hash
    cache_string = f"{rag_id}:{normalized_q}:{top_k or 'default'}"
    
    # Hash SHA256 truncado
    hash_value = hashlib.sha256(cache_string.encode()).hexdigest()[:32]
    
    return f"{CACHE_PREFIX}{rag_id}:{hash_value}"


async def get_cached_answer(
    rag_id: str, 
    question: str, 
    top_k: Optional[int] = None
) -> Optional[dict]:
    """
    Busca respuesta en caché.
    
    Args:
        rag_id: ID del RAG
        question: Pregunta del usuario
        top_k: Parámetro top_k
    
    Returns:
        Dict con respuesta cacheada o None si no existe
    """
    try:
        client = await get_redis()
        key = build_cache_key(rag_id, question, top_k)
        cached = await client.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    except Exception:
        # En caso de error, continuar sin caché
        return None


async def set_cached_answer(
    rag_id: str,
    question: str,
    response: dict,
    ttl_seconds: int = 300,
    top_k: Optional[int] = None
) -> bool:
    """
    Guarda respuesta en caché.
    
    Args:
        rag_id: ID del RAG
        question: Pregunta del usuario
        response: Respuesta completa a cachear
        ttl_seconds: Tiempo de vida del caché
        top_k: Parámetro top_k
    
    Returns:
        True si se guardó correctamente
    """
    try:
        client = await get_redis()
        key = build_cache_key(rag_id, question, top_k)
        await client.setex(key, ttl_seconds, json.dumps(response))
        return True
    except Exception:
        return False


async def invalidate_cache(rag_id: str) -> int:
    """
    Invalida todo el caché de un RAG específico.
    
    Args:
        rag_id: ID del RAG
    
    Returns:
        Número de keys eliminadas
    """
    try:
        client = await get_redis()
        pattern = f"{CACHE_PREFIX}{rag_id}:*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception:
        return 0
```

### 3. `services/api/app/sessions.py`

```python
"""
Gestión de sesiones de conversación con Redis.

Almacena historial corto de conversación por session_id.
"""
import json
from typing import List, Optional
from datetime import datetime

from app.redis_client import get_redis

# Prefijo para keys de sesión
SESSION_PREFIX = "rag:session:"


async def get_session_history(
    session_id: str,
    max_turns: int = 5
) -> List[dict]:
    """
    Obtiene el historial de una sesión.
    
    Args:
        session_id: ID de la sesión
        max_turns: Máximo de turnos a retornar
    
    Returns:
        Lista de turnos [{question, answer, timestamp}, ...]
    """
    try:
        client = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        
        # Obtener últimos N elementos de la lista
        history_raw = await client.lrange(key, -max_turns, -1)
        
        history = []
        for item in history_raw:
            history.append(json.loads(item))
        
        return history
    except Exception:
        return []


async def append_turn(
    session_id: str,
    question: str,
    answer: str,
    ttl_seconds: int = 1800
) -> bool:
    """
    Añade un turno de conversación a la sesión.
    
    Args:
        session_id: ID de la sesión
        question: Pregunta del usuario
        answer: Respuesta generada
        ttl_seconds: TTL de la sesión completa
    
    Returns:
        True si se guardó correctamente
    """
    try:
        client = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        
        turn = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Añadir al final de la lista
        await client.rpush(key, json.dumps(turn))
        
        # Renovar TTL
        await client.expire(key, ttl_seconds)
        
        return True
    except Exception:
        return False


async def clear_session(session_id: str) -> bool:
    """
    Elimina una sesión.
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        True si se eliminó
    """
    try:
        client = await get_redis()
        key = f"{SESSION_PREFIX}{session_id}"
        await client.delete(key)
        return True
    except Exception:
        return False
```

### 4. `services/api/app/rate_limit.py`

```python
"""
Rate limiting por RAG usando Token Bucket en Redis.

Implementación simple:
- Cada RAG tiene su propio bucket
- Configurable: rps (requests per second) y burst
- Devuelve 429 si se excede el límite
"""
import time
from typing import Tuple
from fastapi import HTTPException

from app.redis_client import get_redis

# Prefijo para keys de rate limit
RATE_LIMIT_PREFIX = "rag:ratelimit:"


async def check_rate_limit(
    rag_id: str,
    client_ip: str,
    rps: int = 10,
    burst: int = 20,
    error_message: str = "Demasiadas solicitudes. Intenta de nuevo en unos segundos."
) -> Tuple[bool, int]:
    """
    Verifica y aplica rate limiting.
    
    Usa algoritmo Token Bucket simplificado:
    - Los tokens se regeneran a razón de 'rps' por segundo
    - Máximo 'burst' tokens acumulados
    - Cada request consume 1 token
    
    Args:
        rag_id: ID del RAG
        client_ip: IP del cliente
        rps: Requests por segundo permitidos
        burst: Máximo de requests en ráfaga
        error_message: Mensaje para el error 429
    
    Returns:
        Tuple (allowed: bool, remaining: int)
    
    Raises:
        HTTPException 429 si se excede el límite
    """
    try:
        client = await get_redis()
        
        # Key única por RAG + IP
        key = f"{RATE_LIMIT_PREFIX}{rag_id}:{client_ip}"
        now = time.time()
        
        # Obtener estado actual
        pipe = client.pipeline()
        pipe.hgetall(key)
        results = await pipe.execute()
        
        bucket_data = results[0]
        
        if not bucket_data:
            # Primer request, crear bucket lleno
            tokens = burst - 1  # Consumir 1 token
            last_update = now
        else:
            # Calcular tokens regenerados
            last_update = float(bucket_data.get("last_update", now))
            tokens = float(bucket_data.get("tokens", burst))
            
            # Regenerar tokens basado en tiempo transcurrido
            elapsed = now - last_update
            tokens = min(burst, tokens + (elapsed * rps))
            
            # Consumir 1 token
            tokens -= 1
        
        # Verificar si hay tokens disponibles
        if tokens < 0:
            # Rate limit excedido
            raise HTTPException(
                status_code=429,
                detail=error_message
            )
        
        # Guardar nuevo estado
        await client.hset(key, mapping={
            "tokens": tokens,
            "last_update": now
        })
        await client.expire(key, 60)  # Limpiar después de 1 minuto de inactividad
        
        return True, int(tokens)
        
    except HTTPException:
        raise
    except Exception:
        # En caso de error de Redis, permitir el request
        return True, -1


async def get_rate_limit_status(rag_id: str, client_ip: str) -> dict:
    """
    Obtiene el estado actual del rate limit.
    
    Args:
        rag_id: ID del RAG
        client_ip: IP del cliente
    
    Returns:
        Dict con tokens restantes y tiempo de reset
    """
    try:
        client = await get_redis()
        key = f"{RATE_LIMIT_PREFIX}{rag_id}:{client_ip}"
        data = await client.hgetall(key)
        
        if data:
            return {
                "tokens_remaining": int(float(data.get("tokens", 0))),
                "last_update": float(data.get("last_update", 0))
            }
        return {"tokens_remaining": -1, "last_update": 0}
    except Exception:
        return {"tokens_remaining": -1, "last_update": 0}
```

### 5. Modificaciones a `services/api/app/routes/query.py`

```python
"""
Endpoint principal de consulta RAG.
Integrado con cache, sessions y rate limiting.
"""
import time
import uuid
from fastapi import APIRouter, Request
from app.models import QueryRequest, QueryResponse, ContextChunk

# Importar utilidades Redis
from app.cache import get_cached_answer, set_cached_answer
from app.sessions import get_session_history, append_turn
from app.rate_limit import check_rate_limit

router = APIRouter()

# Configuración por defecto (en producción viene del YAML)
DEFAULT_CACHE_TTL = 300
DEFAULT_SESSION_TTL = 1800
DEFAULT_RPS = 10
DEFAULT_BURST = 20


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, req: Request):
    """
    Procesa una consulta RAG con cache, sessions y rate limiting.
    """
    start_time = time.time()
    
    # Obtener IP del cliente
    client_ip = req.client.host if req.client else "unknown"
    
    # 1. Aplicar rate limiting
    await check_rate_limit(
        rag_id=request.rag_id,
        client_ip=client_ip,
        rps=DEFAULT_RPS,
        burst=DEFAULT_BURST
    )
    
    # 2. Generar/usar session_id
    session_id = request.session_id or str(uuid.uuid4())
    
    # 3. Buscar en caché
    cached = await get_cached_answer(
        rag_id=request.rag_id,
        question=request.question,
        top_k=request.top_k
    )
    
    if cached:
        # Cache hit
        cached["cache_hit"] = True
        cached["latency_ms"] = int((time.time() - start_time) * 1000)
        cached["session_id"] = session_id
        return QueryResponse(**cached)
    
    # 4. Cache miss - procesar consulta
    # TODO: Aquí va la lógica real de retrieval + LLM (Subproyectos 6 y 8)
    
    # Obtener historial de sesión (para contexto futuro)
    session_history = await get_session_history(session_id)
    
    # Respuesta dummy por ahora
    answer = "NOT_IMPLEMENTED"
    context_chunks = []
    
    # 5. Construir respuesta
    response_data = {
        "rag_id": request.rag_id,
        "answer": answer,
        "context_chunks": context_chunks,
        "latency_ms": int((time.time() - start_time) * 1000),
        "cache_hit": False,
        "session_id": session_id
    }
    
    # 6. Guardar en caché
    await set_cached_answer(
        rag_id=request.rag_id,
        question=request.question,
        response=response_data,
        ttl_seconds=DEFAULT_CACHE_TTL,
        top_k=request.top_k
    )
    
    # 7. Guardar turno en sesión
    await append_turn(
        session_id=session_id,
        question=request.question,
        answer=answer,
        ttl_seconds=DEFAULT_SESSION_TTL
    )
    
    return QueryResponse(**response_data)
```

### 6. `docs/redis.md`

```markdown
# Uso de Redis en el Sistema RAG

## Funciones de Redis

Redis cumple múltiples roles en el sistema:

| Función | Prefijo de Keys | Descripción |
|---------|-----------------|-------------|
| Cola de ingestión | `rag:ingest:*` | Jobs de procesamiento de documentos |
| Caché de respuestas | `rag:cache:*` | Respuestas pre-calculadas |
| Sesiones | `rag:session:*` | Historial de conversaciones |
| Rate limiting | `rag:ratelimit:*` | Control de tráfico por RAG/IP |

## Prefijos de Keys

### Caché (`rag:cache:`)
- Pattern: `rag:cache:{rag_id}:{hash}`
- TTL: Configurable por RAG (default 300s)
- Contenido: JSON con respuesta completa

### Sesiones (`rag:session:`)
- Pattern: `rag:session:{session_id}`
- Tipo: LIST (turnos de conversación)
- TTL: Configurable (default 1800s)

### Rate Limit (`rag:ratelimit:`)
- Pattern: `rag:ratelimit:{rag_id}:{client_ip}`
- Tipo: HASH (tokens, last_update)
- TTL: 60s de inactividad

## Algoritmo de Rate Limiting

Se usa **Token Bucket**:
1. Cada bucket tiene capacidad `burst`
2. Se regeneran `rps` tokens por segundo
3. Cada request consume 1 token
4. Si tokens < 0, se rechaza con 429

## Configuración Recomendada

### Redis para Producción
```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### TTLs Sugeridos
| Tipo | TTL | Razón |
|------|-----|-------|
| Caché | 5-10 min | Balance frescura/performance |
| Sesiones | 30 min | Conversación típica |
| Rate limit | 1 min | Auto-limpieza |

## Monitoreo

### Comandos útiles
```bash
# Ver todas las keys de caché
redis-cli KEYS "rag:cache:*"

# Ver estado de una sesión
redis-cli LRANGE "rag:session:{session_id}" 0 -1

# Ver tokens de rate limit
redis-cli HGETALL "rag:ratelimit:{rag_id}:{ip}"

# Estadísticas de memoria
redis-cli INFO memory
```

## Invalidación de Caché

Para invalidar caché de un RAG específico:
```python
from app.cache import invalidate_cache
await invalidate_cache("mi_rag_id")
```
```

---

## VALIDACIÓN (humano ejecuta)

### Test de Caché

```bash
# 1. Primera consulta (cache miss)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "test", "question": "¿Qué es Python?"}'
# Verificar: cache_hit = false

# 2. Segunda consulta idéntica (cache hit)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "test", "question": "¿Qué es Python?"}'
# Verificar: cache_hit = true
```

### Test de Rate Limiting

```bash
# Disparar muchas consultas rápidas
for i in {1..30}; do
  curl -s -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"rag_id": "test", "question": "test"}' &
done
wait

# Debería ver algunas respuestas 429
```

### Verificar Keys en Redis

```bash
# Conectar a Redis
docker compose exec redis redis-cli

# Ver keys de caché
KEYS rag:cache:*

# Ver keys de sesión
KEYS rag:session:*

# Ver keys de rate limit
KEYS rag:ratelimit:*
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `cache_hit` cambia a `true` al repetir consulta
- [ ] Se recibe error 429 al exceder rate limit
- [ ] Las keys existen en Redis con prefijos correctos
- [ ] Los TTLs se aplican correctamente

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| Cache nunca hit | Key diferente cada vez | Verificar normalización de pregunta |
| 429 siempre o nunca | Config rps/burst incorrecta | Ajustar valores en config |
| Redis connection error | URL incorrecta o servicio caído | Verificar REDIS_URL y `docker compose ps` |
| Session history vacío | TTL muy corto | Aumentar ttl_seconds |

---

## LO QUE SE CONGELA

✅ Prefijos de keys Redis: `rag:cache:`, `rag:session:`, `rag:ratelimit:`  
✅ Algoritmo de rate limiting: Token Bucket  
✅ Estructura de caché: hash de (rag_id + question + top_k)  

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 8**: Integración OpenRouter (LLM) + fallback + prompts por RAG