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