# RAF Chatbot - Sistema RAG On-Premise

## 🎯 Descripción

Sistema RAG (Retrieval-Augmented Generation) comercializable, 100% local, replicable por cliente mediante Docker Compose aislado.

## ✅ Estado Actual: PRODUCCIÓN (MVP)

El sistema está **funcional y listo para producción** con las siguientes capacidades verificadas:

| Métrica | Valor |
|---------|-------|
| Usuarios concurrentes | ~300 (objetivo cumplido) |
| Throughput con cache | ~112 req/s |
| Latencia con cache | ~85ms |
| Latencia sin cache | ~2.3s (llamada LLM) |
| Cache hit rate | ~88% |

## 🏗️ Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Cliente   │────▶│    Nginx    │────▶│   FastAPI   │
│  (Browser)  │     │   :8080     │     │    :8001    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
             ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
             │   Qdrant    │           │    Redis    │           │  OpenRouter │
             │  (Vectores) │           │   (Cache)   │           │    (LLM)    │
             └─────────────┘           └─────────────┘           └─────────────┘
```

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Función |
|------------|------------|---------|
| API | FastAPI (async) | Consultas en tiempo real |
| Vector DB | Qdrant | Almacenamiento de embeddings |
| Cache | Redis | Cache de respuestas (TTL 1h) |
| Proxy | Nginx | Rate limiting (10 req/s por IP) |
| LLM | OpenRouter | Generación de respuestas |
| Contenedores | Docker Compose | Orquestación local |

## 📦 Servicios Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `nginx` | 8080:80 | Reverse proxy con rate limiting |
| `api` | 8001:8000 | API FastAPI |
| `qdrant` | interno | Vector database |
| `redis` | interno | Cache y estado |
| `ingest-worker` | - | Worker de ingestión (placeholder) |

## 🚀 Inicio Rápido

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env y añadir OPENROUTER_API_KEY
```

### 2. Levantar servicios

```bash
cd deploy/compose
docker compose up -d
```

### 3. Verificar estado

```bash
docker ps
# Todos los servicios deben estar "Up"
```

### 4. Probar el sistema

```bash
# Health check
curl http://localhost:8080/health

# Consulta de prueba
curl -X POST http://localhost:8080/api/query/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es este sistema?", "rag_id": "default"}'
```

## 📁 Estructura del Repositorio

```
raf_chatbot/
├── configs/                 # Configuración por cliente y RAG
│   ├── client/             # Config global del cliente
│   └── rags/               # Config por RAG + prompts
├── data/                   # Datos y fuentes
│   ├── sources/            # Documentos a ingestar
│   └── backups/            # Backups
├── deploy/                 # Configuración de despliegue
│   ├── compose/            # docker-compose.yml
│   └── nginx/              # Configuración Nginx
├── docs/                   # Documentación
├── scripts/                # Scripts operativos
│   ├── ingest_pdf.py       # Ingesta de PDFs
│   ├── load_test.py        # Pruebas de carga
│   └── verify_qdrant_api.py # Verificación Qdrant
├── services/               # Servicios
│   ├── api/                # FastAPI
│   └── ingest/             # Worker de ingestión
├── specs/                  # Especificaciones y lecciones aprendidas
└── tests/                  # Tests
```

## 🔧 Operaciones Comunes

### Ingestar un PDF

```bash
# Copiar PDF al contenedor
docker cp "mi_documento.pdf" api:/workspace/data/

# Ejecutar ingesta
docker exec api python scripts/ingest_pdf.py /workspace/data/mi_documento.pdf --rag-id default
```

### Ver métricas

```bash
curl http://localhost:8080/api/metrics
```

### Ver logs

```bash
docker compose -f deploy/compose/docker-compose.yml logs -f api
```

### Reiniciar servicios

```bash
cd deploy/compose
docker compose restart
```

## 🌐 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/query/simple` | POST | Consulta simplificada (UI web) |
| `/api/query` | POST | Consulta completa |
| `/api/metrics` | GET | Métricas del sistema |
| `/api/docs` | GET | Documentación OpenAPI |

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
OPENROUTER_API_KEY=sk-or-...    # Requerido para LLM
QDRANT_URL=http://qdrant:6333   # URL interna de Qdrant
REDIS_URL=redis://redis:6379/0  # URL interna de Redis
```

### Rate Limiting (Nginx)

- **Límite**: 10 requests/segundo por IP
- **Burst**: 20 requests
- **Configuración**: `deploy/nginx/nginx.conf`

## 📊 Características de Producción

- ✅ **Cache Redis**: Respuestas cacheadas por 1 hora
- ✅ **Rate Limiting**: Protección contra abuso (Nginx)
- ✅ **Fallback LLM**: Modelo secundario si falla el principal
- ✅ **Métricas**: Contadores y latencias en /metrics
- ✅ **Multi-RAG**: Soporte para múltiples colecciones
- ✅ **Logs estructurados**: Para diagnóstico

## 📚 Documentación Adicional

- [Operaciones](docs/operations.md)
- [Arquitectura](docs/architecture.md)
- [Configuración](docs/configuration.md)
- [Lecciones Aprendidas](specs/LESSONS-LEARNED-INDEX.md)

## 🔒 Seguridad

- API keys en variables de entorno (no hardcodeadas)
- Redis y Qdrant solo accesibles internamente
- Rate limiting activo en Nginx
- Sin autenticación en MVP (añadir según necesidad)

## 📝 Licencia

[Por definir]