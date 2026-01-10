# Lecciones Aprendidas 02 - Router Integration en FastAPI

## 🎯 Problema Identificado

**Error en Subproyecto 9 (Observabilidad)**

Endpoint `/metrics` estaba implementado en `services/api/app/routes/metrics.py` pero no era accesible.

```
curl http://localhost:8001/metrics
# HTTP/1.1 404 Not Found
# {"detail":"Not Found"}
```

FastAPI debería reconocer la ruta pero retornaba 404.

---

## 🔍 Causa Raíz

**Análisis de la Implementación**:

### 1. Endpoint Correctamente Implementado

```python
# ✓ services/api/app/routes/metrics.py - CORRECTO
from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint():
    """Devuelve métricas internas del servicio."""
    snapshot = get_metrics().get_snapshot()
    return MetricsResponse(**snapshot)
```

### 2. El Problema: Router NO Incluido en main.py

```python
# ❌ services/api/main.py - ANTES (INCORRECTO)
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="RAG API", version="0.1.0")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})

# ❌ FALTA: include_router(main_router)
# Por eso /metrics retorna 404
```

### 3. Cadena de Inclusión Rota

```
metrics.py
  ↓ (define router)
__init__.py en routes/
  ↓ (intenta incluir metrics_router)
main.py
  ❌ NO INCLUYE main_router del __init__.py
  
Resultado: Route nunca se registra en FastAPI
```

### 4. Flujo Correcto vs Incorrecto

```
❌ FLUJO INCORRECTO
────────────────────
metrics.py
  └─ router = APIRouter()
     └─ @router.get("/metrics")
        
routes/__init__.py
  └─ main_router.include_router(metrics_router)
  
main.py
  └─ app = FastAPI()  # ❌ NO INCLUYE main_router
     └─ NUNCA se registran /metrics

✓ FLUJO CORRECTO
────────────────
metrics.py
  └─ router = APIRouter()
     └─ @router.get("/metrics")
        
routes/__init__.py
  └─ main_router.include_router(metrics_router)
  
main.py
  └─ app = FastAPI()
     └─ app.include_router(main_router)  # ✓ INCLUYE
        └─ Ahora /metrics está disponible
```

---

## ✅ Solución Implementada

### Paso 1: Crear Estructura de Routers Modular

```python
# services/api/app/routes/__init__.py
"""
Módulo routes: contiene los endpoints del API.
Exports:
- query: Router con endpoint /query para consultas RAG
- metrics: Router con endpoint /metrics para métricas internas
"""

from fastapi import APIRouter

# Importar routers específicos
from app.routes.query import router as query_router
from app.routes.metrics import router as metrics_router

# Crear router principal
main_router = APIRouter()

# Incluir todos los routers
main_router.include_router(query_router)
main_router.include_router(metrics_router)

__all__ = ["main_router", "query_router", "metrics_router"]
```

### Paso 2: Incluir Router Principal en main.py

```python
# services/api/main.py - DESPUÉS (CORRECTO)
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

from app.routes import main_router  # ✓ IMPORTAR

app = FastAPI(title="RAG API", version="0.1.0")

logger = logging.getLogger(__name__)

# ✓ INCLUIR router principal con todos los endpoints
app.include_router(main_router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Paso 3: Verificación

```bash
# ✓ Ahora funciona
curl http://localhost:8001/metrics
# {"requests_total": 0, "errors_total": 0, ...}

# ✓ Health check también funciona
curl http://localhost:8001/health
# {"status": "healthy"}
```

---

## 🛡️ Principios Preventivos Clave

### P1: Router Hierarchy Pattern

**Estructura recomendada para aplicaciones medianas**:

```
services/api/
├── main.py                      # Punto de entrada
├── app/
│   ├── __init__.py
│   ├── observability.py         # Lógica de negocio reutilizable
│   ├── models.py                # Modelos Pydantic
│   ├── routes/
│   │   ├── __init__.py          # ✓ Define main_router
│   │   ├── metrics.py           # Router específico
│   │   ├── query.py             # Router específico
│   │   └── health.py            # (opcional)
│   └── ...otros módulos
```

**En `routes/__init__.py`**:
```python
from fastapi import APIRouter

# Centralizar inclusión de routers
main_router = APIRouter()
main_router.include_router(query_router)
main_router.include_router(metrics_router)
```

**En `main.py`**:
```python
from app.routes import main_router
app.include_router(main_router)  # ✓ Un solo include
```

### P2: Diferencia entre APIRouter vs FastAPI

| Concepto | Uso | Ventaja |
|----------|-----|---------|
| `APIRouter()` | Define rutas modulares | Reutilizable, testeable |
| `FastAPI()` | App principal | Configuración global, startup/shutdown |
| `app.include_router()` | Registra routes en app | Dinámico, composable |

```python
# ✓ PATRÓN CORRECTO
router = APIRouter()  # Define rutas

@router.get("/metrics")
async def get_metrics():
    return {"status": "ok"}

app = FastAPI()  # App principal
app.include_router(router)  # Registra en app
```

### P3: Debugging - Verificar Rutas Registradas

```python
# Verificar qué rutas están registradas
from fastapi import FastAPI

app = FastAPI()

# Después de incluir todos los routers
for route in app.routes:
    print(f"{route.path} - {route.methods}")
    
# Output:
# /health - {'GET'}
# /metrics - {'GET'}
# /query - {'POST'}
```

Script para debugging:

```python
# scripts/debug-routes.py
#!/usr/bin/env python3
"""
Lista todas las rutas registradas en FastAPI.
Uso: python scripts/debug-routes.py
"""

from services.api.main import app

print("=" * 60)
print("RUTAS REGISTRADAS EN FASTAPI")
print("=" * 60)

for route in app.routes:
    path = getattr(route, 'path', 'N/A')
    methods = getattr(route, 'methods', set())
    name = getattr(route, 'name', 'N/A')
    
    methods_str = ', '.join(methods) if methods else 'N/A'
    print(f"{methods_str:8} {path:30} ({name})")

print("\n" + "=" * 60)
print(f"Total: {len(app.routes)} rutas")
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: `404 Not Found` en endpoint que SABES que existe

```python
# Checklist:
1. ✓ El endpoint está definido en routes/metrics.py?
2. ✓ El router está creado? (router = APIRouter())
3. ✓ El decorator está correcto? (@router.get("/metrics"))
4. ⚠️ ¿Se incluye el router en routes/__init__.py? (AQUÍ FALLÓ)
5. ⚠️ ¿Se incluye main_router en main.py? (AQUÍ FALLÓ)
6. ✓ ¿Hay typos en imports?
```

### Señal 2: Imports Circulares

```python
# ❌ Problema potencial
# main.py
from app.routes import main_router  # imports routes/__init__.py

# app/routes/__init__.py
from app.routes.metrics import router as metrics_router  # imports metrics.py

# app/routes/metrics.py
from app.observability import get_metrics  # imports observability.py

# app/observability.py
# (no importa main.py ni routes) ✓ OK

# Solución: evitar que modules_inferior importen modules_superior
```

### Señal 3: RuntimeError en app initialization

```
RuntimeError: Dependency is not subscriptable
```

Esto puede significar:
- Router no está correctamente incluido
- Hay circular imports
- Modelo Pydantic mal importado

---

## 💻 Código Reutilizable

### Template: Router Modular Completo

```python
# services/api/app/routes/example.py
"""
Router ejemplo para endpoints de feature X.
Incluible en main_router.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/example",  # (Opcional) prefijo de rutas
    tags=["example"],   # (Opcional) para documentación
)

class ExampleRequest(BaseModel):
    """Modelo de request."""
    name: str
    value: int

class ExampleResponse(BaseModel):
    """Modelo de response."""
    id: str
    status: str

@router.post("/action", response_model=ExampleResponse)
async def example_action(request: ExampleRequest):
    """
    Endpoint ejemplo.
    
    Docstring para Swagger/OpenAPI.
    """
    try:
        # Lógica
        return ExampleResponse(id="123", status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def example_status():
    """Estado del ejemplo."""
    return {"status": "active"}
```

### Template: main.py Escalable

```python
# services/api/main.py
"""
Punto de entrada de FastAPI.
Incluye todos los routers de forma modular.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Importar routers
from app.routes import main_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app
app = FastAPI(
    title="RAG API",
    version="0.1.0",
    description="API para RAG on-premise",
)

# Middleware CORS (si necesitas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✓ Incluir todos los routers
app.include_router(main_router)

# Health check (sin necesidad de router)
@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({"status": "healthy"})

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("✓ API iniciada")
    logger.info(f"✓ Rutas registradas: {len(app.routes)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("✓ API detenida")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
```

### Función Reutilizable: Listar Rutas

```python
# services/api/app/utils/routes.py
"""
Utilidades para manejo de routers.
"""

from typing import List, Dict
from fastapi import FastAPI

def get_all_routes(app: FastAPI) -> List[Dict]:
    """
    Obtiene todas las rutas registradas en FastAPI.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Lista de dicts con info de rutas
    """
    routes = []
    
    for route in app.routes:
        route_info = {
            'path': getattr(route, 'path', 'N/A'),
            'methods': list(getattr(route, 'methods', set())),
            'name': getattr(route, 'name', 'N/A'),
            'summary': getattr(route, 'summary', None),
        }
        routes.append(route_info)
    
    return routes

def print_routes(app: FastAPI) -> None:
    """
    Imprime todas las rutas de forma legible.
    
    Args:
        app: FastAPI application instance
    """
    routes = get_all_routes(app)
    
    print("=" * 80)
    print("RUTAS REGISTRADAS EN FASTAPI")
    print("=" * 80)
    
    for route in routes:
        methods = ', '.join(route['methods']) if route['methods'] else 'N/A'
        path = route['path']
        name = route['name']
        
        print(f"{methods:15} {path:40} ({name})")
    
    print("\n" + "=" * 80)
    print(f"Total: {len(routes)} rutas")

def validate_routes(app: FastAPI, required_routes: List[str]) -> bool:
    """
    Valida que todas las rutas requeridas estén registradas.
    
    Args:
        app: FastAPI application instance
        required_routes: Lista de rutas que deben existir
        
    Returns:
        True si todas las rutas existen, False en caso contrario
    """
    routes = get_all_routes(app)
    registered_paths = [r['path'] for r in routes]
    
    missing = [r for r in required_routes if r not in registered_paths]
    
    if missing:
        print(f"✗ Rutas faltantes: {missing}")
        return False
    
    print(f"✓ Todas las rutas requeridas están registradas")
    return True

# Uso:
# from app.utils.routes import print_routes, validate_routes
# 
# if __name__ == "__main__":
#     from main import app
#     print_routes(app)
#     validate_routes(app, ["/health", "/metrics", "/query"])
```

### Script de Validación: `scripts/validate-routes.py`

```python
#!/usr/bin/env python3
"""
Valida que todos los routers estén correctamente incluidos.
Uso: python scripts/validate-routes.py
"""

import sys
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent / "services/api"))

from main import app
from app.utils.routes import print_routes, validate_routes

def main():
    print("\n" + "=" * 80)
    print("VALIDACIÓN DE ROUTERS EN FASTAPI")
    print("=" * 80 + "\n")
    
    # Imprimir todas las rutas
    print_routes(app)
    
    # Validar rutas críticas
    print("\nValidando rutas críticas...")
    
    required_routes = [
        "/health",
        "/metrics",
        "/query",
    ]
    
    success = validate_routes(app, required_routes)
    
    print("\n" + "=" * 80)
    
    if success:
        print("✓ Validación exitosa: Todos los routers están correctamente incluidos")
        return 0
    else:
        print("✗ Validación fallida: Faltan routers")
        print("\nChecklist:")
        print("1. ¿Están definidos los routers en routes/*.py?")
        print("2. ¿Están importados en routes/__init__.py?")
        print("3. ¿app.include_router(main_router) está en main.py?")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 📋 Checklist de Implementación

### Antes de agregar un nuevo endpoint

- [ ] Crear archivo `services/api/app/routes/feature_name.py`
- [ ] Definir `router = APIRouter()`
- [ ] Implementar endpoints con `@router.get()`, `@router.post()`, etc.
- [ ] Importar router en `services/api/app/routes/__init__.py`
- [ ] Incluir en `main_router`: `main_router.include_router(feature_router)`
- [ ] Verificar que `main_router` está en `main.py`: `app.include_router(main_router)`
- [ ] Ejecutar: `python scripts/validate-routes.py`
- [ ] Probar: `curl http://localhost:8001/endpoint`

### En el ciclo de desarrollo

```bash
# Después de cambios en routers
python scripts/validate-routes.py

# Reconstruir contenedor si uses docker
docker compose build api

# Reiniciar
docker compose down && docker compose up -d

# Validar nuevamente
sleep 5
python scripts/validate-routes.py
curl http://localhost:8001/health
```

---

## 🔗 Anti-Patterns a Evitar

### ❌ Anti-Pattern 1: Todos los endpoints en main.py

```python
# ❌ MAL - main.py se vuelve enorme
app = FastAPI()

@app.get("/metrics")
async def get_metrics():
    ...

@app.post("/query")
async def query_rag():
    ...

@app.get("/health")
async def health():
    ...

# Máximo 100+ líneas si hay muchos endpoints
```

### ✓ Solución

```python
# ✓ BIEN - Usar routers modulares
app = FastAPI()
app.include_router(metrics_router)
app.include_router(query_router)
```

### ❌ Anti-Pattern 2: No incluir router en main.py

```python
# routes/__init__.py
main_router = APIRouter()
main_router.include_router(metrics_router)  # ✓ Correcto aquí

# main.py
app = FastAPI()
# ❌ OLVIDA include_router(main_router)
# Resultado: 404 en todos los endpoints
```

### ❌ Anti-Pattern 3: Circular imports

```python
# ❌ main.py imports routes/__init__.py
# ❌ routes/__init__.py imports metrics.py
# ❌ metrics.py imports main.py (CIRCULO!)

# Solución: importar solo hacia abajo en jerarquía
# main.py → routes/__init__.py → routes/metrics.py
# No al revés
```

---

## 💡 Best Practices

### BP1: Usar prefixes en routers para organizar

```python
# services/api/app/routes/api_v1.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.get("/status")
async def status():
    return {"version": "1.0"}

# services/api/main.py
from app.routes.api_v1 import router as api_v1_router
app.include_router(api_v1_router)

# Resultado: GET /api/v1/status
```

### BP2: Usar tags para documentación

```python
router = APIRouter(
    prefix="/metrics",
    tags=["monitoring"],  # Agrupa en Swagger
    responses={404: {"description": "Not found"}},
)

# En Swagger: aparece en grupo "monitoring"
```

### BP3: Documentación automática

```python
@router.get(
    "/metrics",
    summary="Obtener métricas del sistema",
    description="Retorna métricas en memoria del servicio",
    responses={
        200: {"description": "Métricas obtenidas exitosamente"},
        500: {"description": "Error interno"},
    }
)
async def get_metrics():
    """Endpoint de métricas."""
    ...
```

---

## 📈 Impacto de la Solución

| Métrica | Antes | Después |
|---------|-------|---------|
| Líneas en main.py | ~200 (muchos endpoints) | ~30 (solo includes) |
| Reusabilidad de routers | No | Sí |
| Testabilidad | Difícil | Fácil (test routers aislados) |
| Mantenibilidad | Baja (todo en un archivo) | Alta (modular) |
| Escalabilidad | Limitada | Ilimitada |

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-01-DOCKER-NETWORKING.md` (puertos en docker)
- Ver: `LESSONS-LEARNED-03-THREAD-SAFETY.md` (métricas compartidas)
- Ver: `LESSONS-LEARNED-04-LLM-FALLBACK.md` (manejo de errores)

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - Router integration |

---

## ✨ Key Takeaway

> **"Siempre usar APIRouter para endpoints modulares. Incluir en una carpeta routes/__init__.py que centraliza y luego include_router(main_router) en main.py. Esto evita 404s misteriosos y mantiene el código escalable."**

```python
# Patrón ganador
# routes/__init__.py
main_router = APIRouter()
main_router.include_router(metrics_router)
main_router.include_router(query_router)

# main.py
from app.routes import main_router
app.include_router(main_router)  # ✓ Un solo lugar
```

---