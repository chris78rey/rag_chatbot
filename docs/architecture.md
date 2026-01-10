# Arquitectura del Sistema RAF Chatbot

## 📋 Resumen

Sistema RAG (Retrieval-Augmented Generation) on-premise, diseñado para ~300 usuarios concurrentes con latencia baja mediante cache Redis.

## ✅ Estado Actual: Producción (MVP)

| Métrica | Valor Verificado |
|---------|------------------|
| Throughput con cache | ~112 req/s |
| Latencia con cache | ~85ms |
| Latencia sin cache | ~2.3s |
| Cache hit rate | ~88% |
| Usuarios concurrentes | ~300 |

---

## Stack Tecnológico

| Componente | Tecnología | Puerto | Función |
|------------|------------|--------|---------|
| API | FastAPI (async) | 8001 | Consultas en tiempo real |
| Proxy | Nginx | 8080 | Rate limiting, reverse proxy |
| Vector DB | Qdrant | interno | Almacenamiento de embeddings |
| Cache | Redis | interno | Cache de respuestas |
| LLM | OpenRouter | externo | Generación de respuestas |

---

## Diagrama de Arquitectura

```
                                    ┌─────────────────────────────────────────┐
                                    │            DOCKER COMPOSE               │
┌─────────────┐                     │                                         │
│   Cliente   │                     │  ┌─────────────┐     ┌─────────────┐   │
│  (Browser)  │────────────────────▶│  │    Nginx    │────▶│   FastAPI   │   │
│             │                     │  │   :8080     │     │    :8001    │   │
└─────────────┘                     │  │             │     │             │   │
                                    │  │ Rate Limit: │     │  - /query   │   │
                                    │  │ 10 req/s/IP │     │  - /health  │   │
                                    │  │ Burst: 20   │     │  - /metrics │   │
                                    │  └─────────────┘     └──────┬──────┘   │
                                    │                             │          │
                                    │         ┌───────────────────┼─────┐    │
                                    │         │                   │     │    │
                                    │         ▼                   ▼     │    │
                                    │  ┌─────────────┐     ┌──────────┐ │    │
                                    │  │   Qdrant    │     │  Redis   │ │    │
                                    │  │  (Vectores) │     │ (Cache)  │ │    │
                                    │  │             │     │          │ │    │
                                    │  │ Colecciones │     │ TTL: 1h  │ │    │
                                    │  │ por RAG     │     │          │ │    │
                                    │  └─────────────┘     └──────────┘ │    │
                                    │                                   │    │
                                    └───────────────────────────────────┼────┘
                                                                        │
                                                                        ▼
                                                               ┌─────────────┐
                                                               │ OpenRouter  │
                                                               │   (LLM)     │
                                                               │             │
                                                               │ Primary:    │
                                                               │ GPT-3.5     │
                                                               │             │
                                                               │ Fallback:   │
                                                               │ Claude      │
                                                               └─────────────┘
```

---

## Flujo de Consulta

```
┌──────────┐    ┌────────┐    ┌─────────┐    ┌───────┐    ┌────────┐    ┌─────┐
│ Request  │───▶│ Nginx  │───▶│ FastAPI │───▶│ Cache │───▶│ Qdrant │───▶│ LLM │
└──────────┘    └────────┘    └─────────┘    └───────┘    └────────┘    └─────┘
                    │              │              │             │           │
               Rate Limit     Métricas      Cache HIT?     Retrieval   Respuesta
               10 req/s/IP                      │          top_k=5         │
                                                │                          │
                                           ┌────┴────┐                     │
                                           │         │                     │
                                          HIT      MISS                    │
                                           │         │                     │
                                           ▼         └─────────────────────┘
                                      ~85ms                    │
                                                               ▼
                                                           ~2.3s
```

### Detalle del flujo:

1. **Nginx** recibe la petición y aplica rate limiting
2. **FastAPI** registra métricas (requests_total)
3. **Cache Redis** busca respuesta previa por hash(query + rag_id)
   - **HIT**: Retorna en ~85ms, incrementa cache_hits_total
   - **MISS**: Continúa al paso 4
4. **Qdrant** busca los top_k chunks más relevantes
5. **OpenRouter** genera respuesta con contexto
6. **Cache Redis** almacena respuesta (TTL: 1 hora)
7. **FastAPI** retorna respuesta, registra latencia

---

## Flujo de Ingesta

```
┌──────────┐    ┌─────────────────┐    ┌─────────────┐    ┌────────┐
│   PDF    │───▶│ ingest_pdf.py   │───▶│  Chunking   │───▶│ Qdrant │
└──────────┘    └─────────────────┘    └─────────────┘    └────────┘
                        │                     │                │
                   Extracción            500 chars         Upsert
                   de texto              50 overlap        puntos
```

### Comando de ingesta:

```bash
docker cp documento.pdf api:/workspace/data/
docker exec api python scripts/ingest_pdf.py /workspace/data/documento.pdf --rag-id default
```

---

## Servicios Docker

| Servicio | Imagen | Puerto | Volumen |
|----------|--------|--------|---------|
| `nginx` | nginx:alpine | 8080:80 | nginx.conf (ro) |
| `api` | build local | 8001:8000 | configs, scripts, data |
| `qdrant` | qdrant/qdrant:latest | interno | qdrant_data |
| `redis` | redis:7-alpine | interno | redis_data |
| `ingest-worker` | build local | - | sources_data |

---

## Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/query/simple` | POST | Consulta simplificada (UI) |
| `/query` | POST | Consulta completa |
| `/metrics` | GET | Métricas del sistema |
| `/docs` | GET | Documentación OpenAPI |

### Modelo de Request (query/simple):

```json
{
  "query": "¿Pregunta del usuario?",
  "rag_id": "default",
  "top_k": 5,
  "score_threshold": 0.0
}
```

### Modelo de Response:

```json
{
  "answer": "Respuesta generada por LLM",
  "sources": ["documento.pdf"],
  "context_chunks": [
    {
      "id": "chunk_123",
      "source": "documento.pdf",
      "text": "Texto del chunk...",
      "score": 0.85
    }
  ],
  "latency_ms": 85
}
```

---

## Configuración

### Variables de Entorno (.env)

```env
OPENROUTER_API_KEY=sk-or-...   # Requerido
QDRANT_URL=http://qdrant:6333  # Default
REDIS_URL=redis://redis:6379/0 # Default
```

### Rate Limiting (Nginx)

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=20 nodelay;
```

### Cache (Redis)

- **Key format**: `rag:cache:{rag_id}:{hash(query)}`
- **TTL**: 3600 segundos (1 hora)
- **Degradación**: Si Redis falla, continúa sin cache

---

## Métricas Disponibles

```json
{
  "requests_total": 150,
  "errors_total": 2,
  "cache_hits_total": 120,
  "rate_limited_total": 0,
  "avg_latency_ms": 85.5,
  "p95_latency_ms": 250.0,
  "latency_samples": 150
}
```

---

## Características de Producción

| Feature | Estado | Descripción |
|---------|--------|-------------|
| Cache Redis | ✅ | TTL 1h, ~88% hit rate |
| Rate Limiting | ✅ | 10 req/s por IP (Nginx) |
| LLM Fallback | ✅ | Claude si GPT-3.5 falla |
| Métricas | ✅ | Contadores + latencias |
| Multi-RAG | ✅ | Colección por rag_id |
| Logs | ✅ | Estructurados |

---

## Decisiones de Diseño

### Por qué FastAPI async
- Manejo eficiente de I/O (Qdrant, Redis, OpenRouter)
- Alto throughput con bajo uso de recursos
- Documentación OpenAPI automática

### Por qué Qdrant
- Vector database optimizada para similaridad
- API simple y bien documentada
- Persistencia en volumen Docker

### Por qué Redis para cache
- Latencia ultra-baja (~1ms)
- TTL nativo
- Degradación graceful si no está disponible

### Por qué Nginx
- Rate limiting probado en producción
- Bajo overhead
- Configuración simple

---

## Escalabilidad

### Actual (MVP)
- Single instance de cada servicio
- ~300 usuarios concurrentes verificados

### Futuro (si se necesita)
- Múltiples replicas de API detrás de load balancer
- Qdrant en modo cluster
- Redis en modo cluster o Sentinel