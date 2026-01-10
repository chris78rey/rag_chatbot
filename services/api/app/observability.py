"""
Módulo de observabilidad: métricas y logging estructurado.

Implementa contadores en memoria para:
- requests_total
- errors_total
- cache_hits_total
- rate_limited_total
- latencias (para calcular avg y p95 aproximado)
"""
import time
import threading
from typing import Optional
from collections import deque


class Metrics:
    """
    Contenedor thread-safe de métricas en memoria.
    
    Nota: Las métricas se pierden al reiniciar el proceso.
    Esto es comportamiento esperado en MVP.
    """
    
    def __init__(self, latency_window: int = 1000):
        """
        Args:
            latency_window: Número de latencias a mantener para cálculo de p95
        """
        self._lock = threading.Lock()
        self._requests_total = 0
        self._errors_total = 0
        self._cache_hits_total = 0
        self._rate_limited_total = 0
        self._latencies_ms = deque(maxlen=latency_window)
    
    def inc_requests(self) -> None:
        """Incrementar contador de requests totales."""
        with self._lock:
            self._requests_total += 1
    
    def inc_errors(self) -> None:
        """Incrementar contador de errores."""
        with self._lock:
            self._errors_total += 1
    
    def inc_cache_hits(self) -> None:
        """Incrementar contador de cache hits."""
        with self._lock:
            self._cache_hits_total += 1
    
    def inc_rate_limited(self) -> None:
        """Incrementar contador de requests rate-limited (429)."""
        with self._lock:
            self._rate_limited_total += 1
    
    def record_latency(self, latency_ms: float) -> None:
        """Registrar latencia de un request."""
        with self._lock:
            self._latencies_ms.append(latency_ms)
    
    def get_avg_latency_ms(self) -> float:
        """Obtener latencia promedio."""
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            return sum(self._latencies_ms) / len(self._latencies_ms)
    
    def get_p95_latency_ms(self) -> float:
        """Obtener p95 aproximado de latencia."""
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            sorted_latencies = sorted(self._latencies_ms)
            idx = int(len(sorted_latencies) * 0.95)
            return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_snapshot(self) -> dict:
        """Obtener snapshot de todas las métricas."""
        with self._lock:
            avg_latency = 0.0
            p95_latency = 0.0
            if self._latencies_ms:
                avg_latency = sum(self._latencies_ms) / len(self._latencies_ms)
                sorted_latencies = sorted(self._latencies_ms)
                idx = int(len(sorted_latencies) * 0.95)
                p95_latency = sorted_latencies[min(idx, len(sorted_latencies) - 1)]
            
            return {
                "requests_total": self._requests_total,
                "errors_total": self._errors_total,
                "cache_hits_total": self._cache_hits_total,
                "rate_limited_total": self._rate_limited_total,
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "latency_samples": len(self._latencies_ms)
            }


# Instancia global de métricas
metrics = Metrics()


class Timer:
    """Context manager para medir latencia de operaciones."""
    
    def __init__(self, record_func: Optional[callable] = None):
        self.record_func = record_func or metrics.record_latency
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.record_func(self.elapsed_ms)
        return False


def get_metrics() -> Metrics:
    """Obtener instancia global de métricas."""
    return metrics