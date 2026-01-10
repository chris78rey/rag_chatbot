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
