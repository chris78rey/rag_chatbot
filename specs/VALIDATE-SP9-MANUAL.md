# Validación Manual de Subproyecto 9 - Observabilidad

## ⚠️ Requisitos Previos

Antes de validar, asegúrate de que:
1. Docker y Docker Compose están instalados
2. Estás en el directorio raíz del proyecto: `G:\zed_projects\raf_chatbot`
3. Las variables de entorno están configuradas (ver `.env`)

## 🚀 Paso 1: Iniciar los Servicios con Docker Compose

```powershell
# En PowerShell, desde G:\zed_projects\raf_chatbot
cd G:\zed_projects\raf_chatbot

# Iniciar todos los servicios (qdrant, redis, api, nginx, etc.)
docker compose -f deploy/compose/docker-compose.yml up -d
```

**Esperar 15-20 segundos** a que el API se inicie correctamente.

Verificar que está corriendo:
```powershell
# Ver logs del API
docker compose -f deploy/compose/docker-compose.yml logs api

# Debería ver algo como:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

## ✅ Paso 2: Verificar que /metrics está disponible

```powershell
# Test 1: Endpoint responde
curl -s http://localhost:8000/metrics | ConvertFrom-Json | Format-Table

# Debería retornar JSON con estos campos:
# - requests_total
# - errors_total
# - cache_hits_total
# - rate_limited_total
# - avg_latency_ms
# - p95_latency_ms
# - latency_samples
```

**Resultado esperado:**
```json
{
  "requests_total": 0,
  "errors_total": 0,
  "cache_hits_total": 0,
  "rate_limited_total": 0,
  "avg_latency_ms": 0.0,
  "p95_latency_ms": 0.0,
  "latency_samples": 0
}
```

## 🔄 Paso 3: Hacer Consultas para Incrementar Métricas

```powershell
# Hacer 5 consultas al endpoint /query
for ($i = 1; $i -le 5; $i++) {
    $body = @{
        rag_id = "test"
        question = "¿Qué es FastAPI?"
        top_k = 5
    } | ConvertTo-Json
    
    curl -X POST http://localhost:8000/query `
        -H "Content-Type: application/json" `
        -d $body -v
    
    Write-Host "Query $i completado"
    Start-Sleep -Milliseconds 500
}
```

## 📊 Paso 4: Verificar que las Métricas Cambiaron

```powershell
# Test 2: Obtener métricas actuales
curl -s http://localhost:8000/metrics | ConvertFrom-Json | Format-Table

# Debería mostrar:
# ✓ requests_total: 5 (o mayor)
# ✓ avg_latency_ms: > 0 (un número positivo)
# ✓ latency_samples: 5 (o mayor)
```

**Resultado esperado después de 5 queries:**
```json
{
  "requests_total": 5,
  "errors_total": 0,
  "cache_hits_total": 0,
  "rate_limited_total": 0,
  "avg_latency_ms": 234.5,
  "p95_latency_ms": 512.3,
  "latency_samples": 5
}
```

## 🧪 Paso 5: Ejecutar Script de Validación Automática

Una vez que el API esté corriendo:

```powershell
cd G:\zed_projects\raf_chatbot
python scripts/validate-sp9.py
```

Debería ver:
```
============================================================
VALIDACIÓN DE SUBPROYECTO 9 - OBSERVABILIDAD
============================================================

[TEST 1] Verificar que /metrics está disponible...
✓ Endpoint /metrics respondió con 200

[TEST 2] Verificar schema de métricas...
✓ Schema correcto. Campos presentes: requests_total, errors_total, ...

[TEST 3] Verificar estado inicial de métricas...
✓ requests_total inicialmente es 0

[TEST 4] Verificar que requests_total incrementa...
✓ requests_total incrementó de 0 a 5

[TEST 5] Verificar registro de latencias...
✓ Se registraron 5 muestras de latencia
  Latencia promedio: 234.5ms

[TEST 6] Verificar tipos de datos...
✓ requests_total: int = 5
✓ errors_total: int = 0
...

============================================================
RESUMEN DE PRUEBAS
============================================================
✓ PASS: Endpoint /metrics existe
✓ PASS: Schema de métricas correcto
✓ PASS: Estado inicial de métricas
✓ PASS: Incremento de requests_total
✓ PASS: Registro de latencias
✓ PASS: Tipos de datos correctos

Total: 6 pasadas, 0 fallidas
```

## 🛑 Paso 6: Detener los Servicios

Cuando termines la validación:

```powershell
# Detener todos los servicios
docker compose -f deploy/compose/docker-compose.yml down

# (Opcional) Limpiar volúmenes
docker compose -f deploy/compose/docker-compose.yml down -v
```

## ✨ Checklist de Validación

Después de completar los pasos, marca lo siguiente:

- [ ] `/metrics` retorna status 200
- [ ] Schema contiene 7 campos requeridos
- [ ] `requests_total` es 0 al inicio
- [ ] `requests_total` incrementa después de queries
- [ ] `avg_latency_ms` > 0 (no 0)
- [ ] `latency_samples` > 0 
- [ ] Script `validate-sp9.py` pasa todos los tests

## 🐛 Troubleshooting

### Error: "No se puede conectar a localhost:8000"
- Verificar que docker-compose esté corriendo: `docker compose ps`
- Esperar más tiempo (puede tomar 20-30 segundos)
- Verificar logs: `docker compose logs api`

### Error: "requests_total siempre es 0"
- Verificar que el query endpoint esté instrumentado
- Revisar que `observability.py` está importado en `query.py`
- Verificar logs del API

### Error: "latency_samples es 0"
- Confirmar que se están haciendo queries exitosas
- Verificar que Timer está siendo usado correctamente
- Revisar que `record_latency()` se llama

### Error: "Campo faltante en schema"
- Verificar que `MetricsResponse` tiene todos los campos
- Revisar `routes/metrics.py`
- Verificar que `get_snapshot()` retorna todos los campos

## 📖 Información Adicional

- **Documentación completa**: `docs/observability.md`
- **Código fuente**: `services/api/app/observability.py`
- **Endpoint**: `services/api/app/routes/metrics.py`
- **Instrumentación**: `services/api/app/routes/query.py`

## 🎯 Próximos Pasos

Una vez validado SP9:
1. Documentar resultados
2. Proceder con Subproyecto 10 (Gestión de estado)

---

**Nota**: Las métricas se pierden al reiniciar el contenedor (comportamiento esperado en MVP).