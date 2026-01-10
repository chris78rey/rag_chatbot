"""
Módulo routes: contiene los endpoints del API.

Exports:
- query: Router con endpoint /query para consultas RAG
- metrics: Router con endpoint /metrics para métricas internas
"""

from fastapi import APIRouter

# Importar routers
from app.routes.query import router as query_router
from app.routes.metrics import router as metrics_router

# Crear router principal
main_router = APIRouter()

# Incluir routers
main_router.include_router(query_router)
main_router.include_router(metrics_router)

__all__ = ["main_router", "query_router", "metrics_router"]