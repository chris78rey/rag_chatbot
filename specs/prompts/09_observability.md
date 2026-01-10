# 🔹 PROMPT EJECUTABLE 09 — Observabilidad Mínima

> **Archivo**: `specs/prompts/09_observability.md`  
> **Subproyecto**: 9 de 10  
> **Prerequisitos**: Subproyectos 1-8 completados

---

## ROL DEL MODELO

Actúa como **arquitecto SRE mínimo viable**:
- Implementar contadores/latencias en memoria del proceso
- Exponer métricas por `/metrics`
- Logs estructurados sin infraestructura extra
- No añadir Prometheus, Grafana ni servicios adicionales

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- Se requiere: logs + métricas internas (JSON endpoint)
- Métricas: latencia, errores, cache hit rate, rate limit triggers, ingest jobs
- Sin Prometheus/Grafana en MVP
- Las métricas son en memoria (se pierden al reiniciar, comportamiento esperado)

---

## OBJETIVO

Implementar contadores y mediciones simples expuestas en `/metrics` y logs estructurados.

**Éxito binario**: `/metrics` devuelve contadores reales que cambian al hacer consultas.

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/observability.py    (CREAR)
services/api/app/routes/metrics.py   (MODIFICAR)
docs/observability.md                (CREAR)
```

---

## CONTENIDO DE ARCHIVOS

### services/api/app/observability.py

```python
"""
Módulo de observabilidad: métricas y logging estructurado.

Implementa contadores en memoria para:
- requests_total
- errors_total
- cache_hits_total
- rate_limited_total
- latencias (para calcular avg y p95 aproximado)
"""
import time
import threading
from typing import Optional
from collections import deque


class Metrics:
    """
    Contenedor thread-safe de métricas en memoria.
    
    Nota: Las métricas se pierden al reiniciar el proceso.
    Esto es comportamiento esperado en MVP.
    """
    
    def __init__(self, latency_window: int = 1000):
        """
        Args:
            latency_window: Número de latencias a mantener para cálculo de p95
        """
        self._lock = threading.Lock()
        self._requests_total = 0
        self._errors_total = 0
        self._cache_hits_total = 0
        self._rate_limited_total = 0
        self._latencies_ms = deque(maxlen=latency_window)
    
    def inc_requests(self) -> None:
        """Incrementar contador de requests totales."""
        with self._lock:
            self._requests_total += 1
    
    def inc_errors(self) -> None:
        """Incrementar contador de errores."""
        with self._lock:
            self._errors_total += 1
    
    def inc_cache_hits(self) -> None:
        """Incrementar contador de cache hits."""
        with self._lock:
            self._cache_hits_total += 1
    
    def inc_rate_limited(self) -> None:
        """Incrementar contador de requests rate-limited (429)."""
        with self._lock:
            self._rate_limited_total += 1
    
    def record_latency(self, latency_ms: float) -> None:
        """Registrar latencia de un request."""
        with self._lock:
            self._latencies_ms.append(latency_ms)
    
    def get_avg_latency_ms(self) -> float:
        """Obtener latencia promedio."""
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            return sum(self._latencies_ms) / len(self._latencies_ms)
    
    def get_p95_latency_ms(self) -> float:
        """Obtener p95 aproximado de latencia."""
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            sorted_latencies = sorted(self._latencies_ms)
            idx = int(len(sorted_latencies) * 0.95)
            return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_snapshot(self) -> dict:
        """Obtener snapshot de todas las métricas."""
        with self._lock:
            avg_latency = 0.0
            p95_latency = 0.0
            if self._latencies_ms:
                avg_latency = sum(self._latencies_ms) / len(self._latencies_ms)
                sorted_latencies = sorted(self._latencies_ms)
                idx = int(len(sorted_latencies) * 0.95)
                p95_latency = sorted_latencies[min(idx, len(sorted_latencies) - 1)]
            
            return {
                "requests_total": self._requests_total,
                "errors_total": self._errors_total,
                "cache_hits_total": self._cache_hits_total,
                "rate_limited_total": self._rate_limited_total,
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "latency_samples": len(self._latencies_ms)
            }


# Instancia global de métricas
metrics = Metrics()


class Timer:
    """Context manager para medir latencia de operaciones."""
    
    def __init__(self, record_func: Optional[callable] = None):
        self.record_func = record_func or metrics.record_latency
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.record_func(self.elapsed_ms)
        return False


def get_metrics() -> Metrics:
    """Obtener instancia global de métricas."""
    return metrics
```

---

### services/api/app/routes/metrics.py (MODIFICAR)

```python
"""
Endpoint de métricas internas.
Expone contadores y latencias en formato JSON.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.observability import get_metrics


router = APIRouter()


class MetricsResponse(BaseModel):
    """Response de métricas del sistema."""
    requests_total: int
    errors_total: int
    cache_hits_total: int
    rate_limited_total: int
    avg_latency_ms: float
    p95_latency_ms: float
    latency_samples: int


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint():
    """
    Devuelve métricas internas del servicio.
    
    Las métricas son en memoria y se reinician con el proceso.
    """
    snapshot = get_metrics().get_snapshot()
    return MetricsResponse(**snapshot)
```

---

### Modificaciones a services/api/app/routes/query.py

Agregar medición de métricas en el endpoint `/query`:

```python
"""
Endpoint principal de consulta RAG.
Con medición de métricas.
"""
import time
import uuid
from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse, ContextChunk
from app.observability import get_metrics, Timer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Procesa una consulta RAG.
    Incluye medición de latencia y contadores.
    """
    metrics = get_metrics()
    metrics.inc_requests()
    
    with Timer() as timer:
        try:
            # Generar session_id si no se provee
            session_id = request.session_id or str(uuid.uuid4())
            
            # TODO: Verificar cache (implementado en subproyecto 7)
            cache_hit = False
            # if cached_response := await get_cached_answer(...):
            #     metrics.inc_cache_hits()
            #     cache_hit = True
            #     return cached_response
            
            # TODO: Retrieval real (implementado en subproyecto 6)
            context_chunks = []
            
            # TODO: LLM call (implementado en subproyecto 8)
            answer = "NOT_IMPLEMENTED"
            
            response = QueryResponse(
                rag_id=request.rag_id,
                answer=answer,
                context_chunks=context_chunks,
                latency_ms=int(timer.elapsed_ms) if hasattr(timer, 'elapsed_ms') else 0,
                cache_hit=cache_hit,
                session_id=session_id
            )
            
            return response
            
        except Exception as e:
            metrics.inc_errors()
            raise
    
    # Actualizar latency en response después del timer
    response.latency_ms = int(timer.elapsed_ms)
    return response
```

---

### docs/observability.md

```markdown
# Observabilidad del Sistema RAG

## Visión General

El sistema implementa observabilidad mínima viable:
- Métricas en memoria expuestas por JSON endpoint
- Logs estructurados a stdout/stderr
- Sin dependencias de Prometheus/Grafana en MVP

## Métricas Disponibles

### Endpoint: GET /metrics

Devuelve un JSON con las siguientes métricas:

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `requests_total` | counter | Total de requests procesados |
| `errors_total` | counter | Total de errores |
| `cache_hits_total` | counter | Total de cache hits |
| `rate_limited_total` | counter | Total de requests rechazados por rate limit |
| `avg_latency_ms` | gauge | Latencia promedio en ms |
| `p95_latency_ms` | gauge | Percentil 95 de latencia en ms |
| `latency_samples` | gauge | Número de muestras de latencia en memoria |

### Ejemplo de Response

```json
{
  "requests_total": 1250,
  "errors_total": 3,
  "cache_hits_total": 450,
  "rate_limited_total": 12,
  "avg_latency_ms": 234.5,
  "p95_latency_ms": 512.3,
  "latency_samples": 1000
}
```

## Comportamiento

### Persistencia

- Las métricas se almacenan **en memoria**
- Se **reinician** cuando el contenedor se reinicia
- Esto es comportamiento esperado en MVP

### Thread Safety

- Los contadores usan locks para acceso concurrente seguro
- El cálculo de p95 mantiene las últimas 1000 latencias

### Ventana de Latencias

- Se mantienen las últimas 1000 mediciones de latencia
- El p95 se calcula sobre esta ventana deslizante

## Logs Estructurados

### Formato Recomendado

Los logs deben seguir formato JSON para facilitar parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Query processed",
  "rag_id": "example_rag",
  "latency_ms": 234,
  "cache_hit": false
}
```

### Niveles de Log

| Nivel | Uso |
|-------|-----|
| DEBUG | Información detallada para debugging |
| INFO | Operaciones normales |
| WARNING | Situaciones inusuales pero no errores |
| ERROR | Errores que afectan el request |

### Datos Sensibles

**NO logear:**
- API keys
- Contenido completo de respuestas LLM
- Datos personales de usuarios

**SÍ logear:**
- IDs de request/session
- Latencias
- Códigos de error
- RAG IDs

## Uso para Diagnóstico

### Verificar Salud del Sistema

```bash
# Obtener métricas
curl http://localhost:8000/metrics

# Calcular tasa de errores
# error_rate = errors_total / requests_total
```

### Identificar Problemas

| Síntoma | Métrica | Acción |
|---------|---------|--------|
| Respuestas lentas | `p95_latency_ms` alto | Revisar Qdrant/LLM |
| Muchos errores | `errors_total` crece rápido | Revisar logs |
| Cache inefectivo | `cache_hits_total` bajo | Ajustar TTL |
| Rate limiting excesivo | `rate_limited_total` alto | Ajustar límites |

## Monitoreo Externo (Futuro)

Para producción, considerar:

1. **Prometheus**: Scrape del endpoint /metrics (requiere formato diferente)
2. **Grafana**: Dashboards sobre métricas de Prometheus
3. **ELK Stack**: Agregación de logs

Estos NO están implementados en MVP.

## Scripts de Verificación

### Test básico de métricas

```bash
# 1. Obtener métricas iniciales
curl -s http://localhost:8000/metrics | jq .

# 2. Hacer algunas consultas
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"rag_id":"test","question":"prueba"}' > /dev/null
done

# 3. Verificar que métricas cambiaron
curl -s http://localhost:8000/metrics | jq .
# requests_total debería ser >= 5
```
```

---

## TAREAS A REALIZAR

1. **Crear** `services/api/app/observability.py` con la clase `Metrics` y helpers
2. **Modificar** `services/api/app/routes/metrics.py` para usar las métricas reales
3. **Modificar** `services/api/app/routes/query.py` para instrumentar con métricas
4. **Crear** `docs/observability.md` con documentación

---

## VALIDACIÓN (humano ejecuta)

```bash
# 1. Rebuild y restart del API
docker compose -f deploy/compose/docker-compose.yml build api
docker compose -f deploy/compose/docker-compose.yml up -d api

# 2. Obtener métricas iniciales
curl http://localhost:8000/metrics
# Debería mostrar todos los contadores en 0

# 3. Hacer 5 consultas
for i in {1..5}; do
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"rag_id":"test","question":"hola"}'
done

# 4. Verificar que métricas cambiaron
curl http://localhost:8000/metrics
# requests_total debería ser 5
# avg_latency_ms debería tener un valor > 0
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `/metrics` responde con el nuevo schema (incluye p95_latency_ms)
- [ ] `requests_total` incrementa con cada consulta
- [ ] `avg_latency_ms` muestra valores reales (no 0)
- [ ] Las métricas cambian al hacer múltiples requests

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| Métricas siempre en 0 | No se llama a `metrics.inc_*()` | Verificar instrumentación en query.py |
| Import error | Ruta incorrecta | Verificar que observability.py está en app/ |
| Race conditions | Acceso sin lock | Usar los métodos de la clase Metrics |
| Latency siempre 0 | Timer no se usa correctamente | Verificar context manager |

---

## LO QUE SE CONGELA

✅ Nombres de métricas expuestas:
- `requests_total`
- `errors_total`
- `cache_hits_total`
- `rate_limited_total`
- `avg_latency_ms`
- `p95_latency_ms`

✅ Endpoint `/metrics` con schema definido

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 10**: Gestión de estado (verificación de estructura e invariantes)