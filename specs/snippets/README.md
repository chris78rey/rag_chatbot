# Snippets de Código Reutilizable

Esta carpeta contiene código reutilizable extraído de las lecciones aprendidas del proyecto RAF Chatbot.

## 📁 Archivos Disponibles

| Archivo | Descripción | Lección Relacionada |
|---------|-------------|---------------------|
| `docker_services.py` | Service Locator para URLs dinámicas Docker/Local | LL-01, LL-05 |
| `pydantic_helpers.py` | Helpers para validación con Pydantic | LL-02 |
| `qdrant_compatible_client.py` | Cliente Qdrant multi-versión compatible | LL-07 |

## 🚀 Uso Rápido

### Docker Service Locator

```python
from snippets.docker_services import ServiceLocator

# Auto-detecta si está en Docker o local
locator = ServiceLocator()

# Obtener URLs
qdrant_url = locator.get_url("qdrant", "http")  # http://qdrant:6333 o http://localhost:6333
redis_url = locator.get_url("redis", "redis")   # redis://redis:6379 o redis://localhost:6379
```

### Qdrant Compatible Client

```python
from snippets.qdrant_compatible_client import QdrantCompatibleClient

# Funciona con cualquier versión de qdrant-client (< 1.7 y >= 1.7)
client = QdrantCompatibleClient(url="http://localhost:6333")

# API unificada de búsqueda
results = client.search(
    collection_name="my_collection",
    query_vector=[0.1] * 384,
    limit=5
)

# Resultados normalizados
for r in results:
    print(f"ID: {r['id']}, Score: {r['score']:.4f}")
```

## 📋 Instalación en tu Proyecto

### Opción 1: Copiar archivos directamente

```bash
# Copiar el snippet que necesites
cp specs/snippets/qdrant_compatible_client.py your_project/utils/
```

### Opción 2: Importar desde specs

```python
import sys
sys.path.insert(0, "specs/snippets")

from qdrant_compatible_client import QdrantCompatibleClient
```

## 🔗 Lecciones Aprendidas Relacionadas

- **LL-01**: Docker Networking - Puertos y conectividad
- **LL-02**: Router Integration - FastAPI modular
- **LL-05**: Qdrant Health Endpoint - Health checks
- **LL-07**: Qdrant Client API Compatibility - Breaking changes en librerías

Ver documentación completa en `specs/LESSONS-LEARNED-INDEX.md`

## ⚡ Verificación

Puedes verificar que los snippets funcionan con:

```bash
# Verificar Qdrant client
python scripts/verify_qdrant_api.py --test-connection

# Verificar Service Locator
python specs/snippets/docker_services.py
```

## 📝 Contribuir

Si encuentras un patrón reutilizable durante el desarrollo:

1. Documenta el problema y la solución en una nueva lección (`LESSONS-LEARNED-XX-TOPIC.md`)
2. Extrae el código reutilizable a esta carpeta
3. Actualiza `LESSONS-LEARNED-INDEX.md` con la nueva lección
4. Actualiza este README con el nuevo snippet

## 📅 Historial

| Fecha | Cambio |
|-------|--------|
| 2026-01-09 | Añadido `qdrant_compatible_client.py` (LL-07) |
| 2026-01-09 | Añadido `docker_services.py` (LL-01, LL-05) |
| 2026-01-08 | Añadido `pydantic_helpers.py` (LL-02) |
| 2026-01-08 | Creación inicial |