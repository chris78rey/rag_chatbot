# Operaciones - RAF Chatbot

## 📋 Índice

- [Arranque del Sistema](#arranque-del-sistema)
- [Parada del Sistema](#parada-del-sistema)
- [Verificación de Estado](#verificación-de-estado)
- [Ingesta de Documentos](#ingesta-de-documentos)
- [Consultas](#consultas)
- [Monitoreo y Métricas](#monitoreo-y-métricas)
- [Logs](#logs)
- [Cache](#cache)
- [Troubleshooting](#troubleshooting)

---

## Arranque del Sistema

### Inicio completo

```bash
cd deploy/compose
docker compose up -d
```

### Verificar que todos los servicios están corriendo

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Salida esperada:**

| Servicio | Estado | Puerto |
|----------|--------|--------|
| nginx | Up | 0.0.0.0:8080->80/tcp |
| api | Up | 0.0.0.0:8001->8000/tcp |
| redis | Up | 6379/tcp (interno) |
| qdrant | Up | 6333-6334/tcp (interno) |

---

## Parada del Sistema

### Parada normal (mantiene datos)

```bash
cd deploy/compose
docker compose down
```

### Parada y eliminar volúmenes (⚠️ BORRA DATOS)

```bash
cd deploy/compose
docker compose down -v
```

---

## Verificación de Estado

### Health check vía Nginx

```bash
curl http://localhost:8080/health
```

**Respuesta esperada:**
```json
{"status": "ok"}
```

### Health check directo a API

```bash
curl http://localhost:8001/health
```

### Verificar Qdrant

```bash
docker exec api python -c "
from qdrant_client import QdrantClient
client = QdrantClient('http://qdrant:6333')
collections = client.get_collections()
print('Colecciones:', [c.name for c in collections.collections])
"
```

### Verificar Redis

```bash
docker exec redis redis-cli ping
```

**Respuesta esperada:** `PONG`

---

## Ingesta de Documentos

### Ingestar un PDF

1. **Copiar el archivo al contenedor:**

```bash
docker cp "C:\ruta\a\mi_documento.pdf" api:/workspace/data/
```

2. **Ejecutar la ingesta:**

```bash
docker exec api python scripts/ingest_pdf.py /workspace/data/mi_documento.pdf --rag-id default
```

**Parámetros opcionales:**
- `--rag-id`: ID de la colección RAG (default: "default")
- `--chunk-size`: Tamaño de chunks (default: 500)
- `--chunk-overlap`: Overlap entre chunks (default: 50)

### Verificar ingesta exitosa

```bash
docker exec api python -c "
from qdrant_client import QdrantClient
client = QdrantClient('http://qdrant:6333')
info = client.get_collection('default')
print(f'Puntos en colección: {info.points_count}')
"
```

---

## Consultas

### Consulta simple (endpoint web)

```bash
curl -X POST http://localhost:8080/api/query/simple \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuál es el tema principal del documento?",
    "rag_id": "default",
    "top_k": 5
  }'
```

### Consulta completa

```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "default",
    "question": "¿Cuál es el tema principal?",
    "top_k": 5,
    "score_threshold": 0.0
  }'
```

### Acceder a la UI web

Abrir en navegador: `http://localhost:8001`

### Documentación OpenAPI

Abrir en navegador: `http://localhost:8001/docs`

---

## Monitoreo y Métricas

### Ver métricas actuales

```bash
curl http://localhost:8080/api/metrics
```

**Respuesta ejemplo:**
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

### Métricas importantes

| Métrica | Descripción | Valor saludable |
|---------|-------------|-----------------|
| `cache_hits_total` / `requests_total` | Cache hit rate | > 50% |
| `errors_total` / `requests_total` | Error rate | < 5% |
| `avg_latency_ms` | Latencia promedio | < 500ms con cache |
| `rate_limited_total` | Requests bloqueados | Bajo |

---

## Logs

### Ver logs de todos los servicios

```bash
cd deploy/compose
docker compose logs -f
```

### Ver logs solo de la API

```bash
docker compose -f deploy/compose/docker-compose.yml logs -f api
```

### Ver logs de Nginx

```bash
docker compose -f deploy/compose/docker-compose.yml logs -f nginx
```

### Ver últimas 100 líneas

```bash
docker compose -f deploy/compose/docker-compose.yml logs --tail=100 api
```

---

## Cache

### Verificar estado del cache

```bash
docker exec redis redis-cli KEYS "rag:cache:*" | head -20
```

### Ver TTL de una key de cache

```bash
docker exec redis redis-cli TTL "rag:cache:default:<hash>"
```

### Limpiar todo el cache (⚠️ con cuidado)

```bash
docker exec redis redis-cli FLUSHDB
```

### Estadísticas de Redis

```bash
docker exec redis redis-cli INFO stats
```

---

## Troubleshooting

### API no responde

1. Verificar que el contenedor está corriendo:
```bash
docker ps | grep api
```

2. Ver logs de errores:
```bash
docker logs api --tail=50
```

3. Reiniciar el servicio:
```bash
docker restart api
```

### Error de conexión a Qdrant

1. Verificar que Qdrant está corriendo:
```bash
docker ps | grep qdrant
```

2. Probar conexión desde API:
```bash
docker exec api python -c "
from qdrant_client import QdrantClient
client = QdrantClient('http://qdrant:6333')
print(client.get_collections())
"
```

### Error de LLM / OpenRouter

1. Verificar que la API key está configurada:
```bash
docker exec api printenv | grep OPENROUTER
```

2. Si falta, añadir a `.env` y reiniciar:
```bash
# Editar .env
OPENROUTER_API_KEY=sk-or-...

# Reiniciar
docker compose -f deploy/compose/docker-compose.yml restart api
```

### Rate limiting (429 Too Many Requests)

El rate limit está configurado en 10 req/s por IP con burst de 20.

Para ajustar, editar `deploy/nginx/nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

Y reiniciar Nginx:
```bash
docker restart nginx
```

### Cache no funciona

1. Verificar conexión a Redis:
```bash
docker exec api python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print('Redis OK:', r.ping())
"
```

2. Ver si hay keys de cache:
```bash
docker exec redis redis-cli DBSIZE
```

---

## Comandos de Mantenimiento

### Rebuild de la imagen API

```bash
cd deploy/compose
docker compose build api
docker compose up -d api
```

### Actualizar todos los servicios

```bash
cd deploy/compose
docker compose pull
docker compose up -d
```

### Backup de Qdrant (volumen)

```bash
docker run --rm -v raf_chatbot_qdrant_data:/data -v $(pwd):/backup alpine \
  tar cvf /backup/qdrant_backup.tar /data
```

### Espacio en disco de volúmenes

```bash
docker system df -v
```

---

## Pruebas de Carga

### Ejecutar load test

```bash
docker exec api python scripts/load_test.py --users 100 --requests 5 --timeout 60
```

### Parámetros disponibles

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--users` | Usuarios concurrentes | 10 |
| `--requests` | Requests por usuario | 5 |
| `--timeout` | Timeout en segundos | 60 |
| `--url` | URL del endpoint | http://localhost:8000/query/simple |

---

## Contacto y Soporte

Para problemas no cubiertos aquí, revisar:
- [Lecciones Aprendidas](../specs/LESSONS-LEARNED-INDEX.md)
- Logs del sistema
- Documentación de los componentes individuales