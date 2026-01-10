# 🔹 PROMPT EJECUTABLE 05 — Contrato de API (consulta RAG) + esqueleto FastAPI

> **Archivo**: `specs/prompts/05_api_fastapi.md`  
> **Subproyecto**: 5 de 10  
> **Prerequisitos**: Subproyectos 1-4 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Crear esqueleto FastAPI con endpoints y respuestas dummy
- No integrar Qdrant ni LLM real todavía
- No cambiar nombres ni estructuras definidas

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- Consultas: FastAPI async en tiempo real
- Multi-RAG: el cliente elige `rag_id`
- Sesión ligera: historial corto (temporal)
- Caché de respuestas: Redis por hash (rag_id + query + parámetros)
- Sin autenticación en MVP; pero detrás de Nginx con rate limiting

---

## OBJETIVO

Definir endpoints y crear esqueleto de proyecto FastAPI sin lógica de retrieval.

**Éxito binario**: existen rutas FastAPI con modelos Pydantic y documentación OpenAPI visible al levantar.

---

## ARCHIVOS A CREAR

```
services/api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       ├── query.py
│       └── metrics.py
├── README.md
├── Dockerfile
└── requirements.txt
```

---

## CONTRATO DE ENDPOINTS

### 1) GET /health

**Response**:
```json
{
  "status": "ok"
}
```

### 2) POST /query

**Request Body**:
```json
{
  "rag_id": "string (requerido)",
  "question": "string (requerido)",
  "session_id": "string (opcional)",
  "top_k": "int (opcional, override)"
}
```

**Response**:
```json
{
  "rag_id": "string",
  "answer": "string",
  "context_chunks": [
    {
      "id": "string",
      "source": "string",
      "text": "string",
      "score": 0.95
    }
  ],
  "latency_ms": 123,
  "cache_hit": false,
  "session_id": "string"
}
```

### 3) GET /metrics

**Response**:
```json
{
  "requests_total": 0,
  "errors_total": 0,
  "cache_hits_total": 0,
  "avg_latency_ms": 0
}
```

---

## CONTENIDO DE ARCHIVOS

### services/api/app/__init__.py

```python
# API package init
```

### services/api/app/main.py

```python
"""
FastAPI main application.
Registra routers y habilita documentación OpenAPI.
"""
from fastapi import FastAPI
from app.routes import health, query, metrics

app = FastAPI(
    title="RAG On-Premise API",
    description="API de consultas RAG multi-tenant",
    version="0.1.0"
)

app.include_router(health.router, tags=["Health"])
app.include_router(query.router, tags=["Query"])
app.include_router(metrics.router, tags=["Metrics"])


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar."""
    pass
```

### services/api/app/models.py

```python
"""
Modelos Pydantic para request/response de la API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request para consulta RAG."""
    rag_id: str = Field(..., description="ID del RAG a consultar")
    question: str = Field(..., description="Pregunta del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión para historial")
    top_k: Optional[int] = Field(None, description="Override de top_k para retrieval")


class ContextChunk(BaseModel):
    """Chunk de contexto recuperado."""
    id: str
    source: str
    text: str
    score: float


class QueryResponse(BaseModel):
    """Response de consulta RAG."""
    rag_id: str
    answer: str
    context_chunks: List[ContextChunk]
    latency_ms: int
    cache_hit: bool
    session_id: Optional[str]


class HealthResponse(BaseModel):
    """Response de health check."""
    status: str


class MetricsResponse(BaseModel):
    """Response de métricas."""
    requests_total: int
    errors_total: int
    cache_hits_total: int
    avg_latency_ms: float
```

### services/api/app/routes/__init__.py

```python
# Routes package init
```

### services/api/app/routes/health.py

```python
"""
Endpoint de health check.
"""
from fastapi import APIRouter
from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica que el servicio está activo."""
    return HealthResponse(status="ok")
```

### services/api/app/routes/query.py

```python
"""
Endpoint principal de consulta RAG.
"""
import time
import uuid
from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse, ContextChunk

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Procesa una consulta RAG.
    
    NOTA: Esta es una implementación DUMMY.
    La integración real con Qdrant y LLM se hará en subproyectos posteriores.
    """
    start_time = time.time()
    
    # Generar session_id si no se provee
    session_id = request.session_id or str(uuid.uuid4())
    
    # Respuesta dummy
    response = QueryResponse(
        rag_id=request.rag_id,
        answer="NOT_IMPLEMENTED",
        context_chunks=[],
        latency_ms=int((time.time() - start_time) * 1000),
        cache_hit=False,
        session_id=session_id
    )
    
    return response
```

### services/api/app/routes/metrics.py

```python
"""
Endpoint de métricas internas.
"""
from fastapi import APIRouter
from app.models import MetricsResponse

router = APIRouter()

# Contadores dummy (se implementarán en Subproyecto 9)
_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "cache_hits_total": 0,
    "avg_latency_ms": 0.0
}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Devuelve métricas internas del servicio."""
    return MetricsResponse(**_metrics)
```

### services/api/Dockerfile

```dockerfile
# Dockerfile para servicio API FastAPI
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/

# Puerto expuesto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### services/api/requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
python-dotenv==1.0.0
```

### services/api/README.md

```markdown
# API FastAPI - RAG On-Premise

Servicio principal de consultas RAG.

## Estructura

```
services/api/
├── app/
│   ├── main.py          # Aplicación FastAPI
│   ├── models.py        # Modelos Pydantic
│   └── routes/          # Endpoints
│       ├── health.py    # Health check
│       ├── query.py     # Consulta RAG
│       └── metrics.py   # Métricas internas
├── Dockerfile
└── requirements.txt
```

## Endpoints

| Método | Ruta      | Descripción              |
|--------|-----------|--------------------------|
| GET    | /health   | Health check             |
| POST   | /query    | Consulta RAG             |
| GET    | /metrics  | Métricas internas        |
| GET    | /docs     | Documentación OpenAPI    |

## Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# Build
docker build -t rag-api .

# Run
docker run -p 8000:8000 rag-api
```

## Notas

- Esta es una implementación esqueleto (dummy)
- La integración con Qdrant se hará en Subproyecto 6
- La integración con Redis cache/rate-limit en Subproyecto 7
- La integración con LLM en Subproyecto 8
```

---

## COMANDOS DE VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# 1. Build del servicio API
docker compose -f deploy/compose/docker-compose.yml build api

# 2. Levantar solo el API (y dependencias)
docker compose -f deploy/compose/docker-compose.yml up -d api

# 3. Verificar que está corriendo
docker compose -f deploy/compose/docker-compose.yml ps

# 4. Probar health check
curl http://localhost:8000/health

# 5. Probar endpoint query (dummy)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "test", "question": "¿Hola?"}'

# 6. Ver documentación OpenAPI
# Abrir en navegador: http://localhost:8000/docs

# Si hay Nginx configurado:
# Abrir: http://localhost/api/docs
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `/health` responde `{"status": "ok"}`
- [ ] `/docs` muestra documentación OpenAPI
- [ ] `/query` responde con schema correcto (aunque dummy)
- [ ] `/metrics` responde con contadores (aunque en 0)

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| 404 en /api/* | Nginx mal configurado | Verificar proxy_pass en nginx.conf |
| Import error | Estructura de carpetas incorrecta | Verificar __init__.py en cada directorio |
| Connection refused | Contenedor no levantado | docker compose up -d |

---

## LO QUE SE CONGELA

✅ Contrato request/response de `/query`  
✅ Estructura de carpetas `services/api/app/`  
✅ Modelos Pydantic definidos

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 6**: Integración Qdrant + embeddings + retrieval real