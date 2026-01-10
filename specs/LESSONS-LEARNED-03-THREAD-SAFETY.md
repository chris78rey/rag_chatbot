# Lecciones Aprendidas 03 - Thread Safety en Métricas Compartidas

## 🎯 Problema Identificado

**Subproyecto 9 (Observabilidad) - Métricas en Memoria**

Necesidad de implementar contadores compartidos (`requests_total`, `errors_total`, etc.) que se incrementan desde múltiples requests concurrentes sin corrupción de datos.

```python
# ❌ INCORRECTO - Sin protección
class Metrics:
    def __init__(self):
        self._requests_total = 0
    
    def inc_requests(self):
        # Race condition si dos threads llaman simultáneamente
        self._requests_total += 1  # ❌ NO ATOMIC
        # Thread A: leer valor (5)
        # Thread B: leer valor (5)
        # Thread A: escribir 6
        # Thread B: escribir 6 (perdió el incremento de A!)
```

---

## 🔍 Causa Raíz

### 1. Python GIL No Protege Operaciones Complejas

```python
# En Python, esto se ve atómico pero NO lo es:
self._requests_total += 1

# Se traduce a bytecode:
# 1. LOAD_FAST              # Cargar valor actual (5)
# 2. LOAD_CONST 1           # Cargar constante 1
# 3. BINARY_ADD             # Sumar (5 + 1 = 6)
# 4. STORE_FAST             # Guardar resultado

# Entre pasos 1 y 4, otro thread puede interferir
```

### 2. En Ambiente Concurrente (Uvicorn async)

```
Request 1 (Thread A)          Request 2 (Thread B)
─────────────────────────────────────────────────
inc_requests()                   
  │ Leer: 5                      
  │ Sumar: 5 + 1 = 6             
  │                              inc_requests()
  │                                │ Leer: 5 ❌ (todavía es 5)
  │ Escribir: 6                     │ Sumar: 5 + 1 = 6
  │                                 │ Escribir: 6 ❌ (perdió incremento)
  ▼                                 ▼
Resultado: 6 (debería ser 7)
```

### 3. Uvicorn es Multi-Threaded

```python
# Uvicorn por defecto usa ThreadPoolExecutor
# Múltiples requests pueden procesar en paralelo

# Configuración típica:
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # 4 procesos
    # Cada uno con su ThreadPoolExecutor
)
```

---

## ✅ Solución Implementada

### Paso 1: Usar threading.Lock

```python
import threading
from collections import deque

class Metrics:
    """
    Contenedor thread-safe de métricas en memoria.
    """
    
    def __init__(self, latency_window: int = 1000):
        # ✓ Lock para proteger acceso concurrente
        self._lock = threading.Lock()
        self._requests_total = 0
        self._errors_total = 0
        self._latencies_ms = deque(maxlen=latency_window)
    
    def inc_requests(self) -> None:
        """Incrementar contador de requests totales."""
        with self._lock:  # ✓ Adquirir lock antes
            self._requests_total += 1
            # Dentro del lock: solo este thread puede ejecutar
        # ✓ Lock liberado automáticamente al salir
    
    def inc_errors(self) -> None:
        """Incrementar contador de errores."""
        with self._lock:
            self._errors_total += 1
    
    def record_latency(self, latency_ms: float) -> None:
        """Registrar latencia de un request."""
        with self._lock:
            self._latencies_ms.append(latency_ms)
    
    def get_snapshot(self) -> dict:
        """Obtener snapshot atómico de todas las métricas."""
        with self._lock:  # ✓ Capturar todo bajo un lock
            # Si no hago esto, otro thread podría cambiar valores
            # mientras estoy construyendo el snapshot
            
            avg_latency = 0.0
            p95_latency = 0.0
            
            if self._latencies_ms:
                avg_latency = sum(self._latencies_ms) / len(self._latencies_ms)
                sorted_latencies = sorted(self._latencies_ms)
                idx = int(len(sorted_latencies) * 0.95)
                p95_latency = sorted_latencies[min(idx, len(sorted_latencies) - 1)]
            
            # ✓ Retornar una copia/snapshot
            return {
                "requests_total": self._requests_total,
                "errors_total": self._errors_total,
                "cache_hits_total": self._cache_hits_total,
                "rate_limited_total": self._rate_limited_total,
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "latency_samples": len(self._latencies_ms)
            }
```

### Paso 2: Context Manager para Latencias

```python
class Timer:
    """Context manager para medir latencia con thread-safety."""
    
    def __init__(self, record_func=None):
        self.record_func = record_func or metrics.record_latency
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # ✓ record_latency() internamente usa lock
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.record_func(self.elapsed_ms)  # Thread-safe
        return False

# Uso:
with Timer() as timer:
    # hacer algo
    pass
# Timer.record_latency() automáticamente usa lock
```

### Paso 3: Uso en Query Endpoint

```python
from app.observability import get_metrics, Timer

@router.post("/query")
async def query_rag(request: QueryRequest):
    """Endpoint con instrumentación thread-safe."""
    
    metrics = get_metrics()
    metrics.inc_requests()  # ✓ Thread-safe
    
    with Timer() as timer:  # ✓ Latencia medida con lock
        try:
            # ... procesamiento ...
            
            return QueryResponse(...)
            
        except Exception as e:
            metrics.inc_errors()  # ✓ Thread-safe
            raise
```

---

## 🛡️ Principios Preventivos Clave

### P1: Compartir Estado = Necesitar Lock

**Regla de Oro**:
```
Si múltiples threads acceden a la misma variable
  → Necesitas un lock (o Atomic, o Queue)
```

```python
# ❌ MAL - Sin lock
shared_counter = 0

def increment():
    global shared_counter
    shared_counter += 1  # ❌ Race condition

# ✓ BIEN - Con lock
lock = threading.Lock()
shared_counter = 0

def increment():
    global shared_counter
    with lock:
        shared_counter += 1  # ✓ Thread-safe
```

### P2: Granularidad del Lock

**Tener un lock NO es suficiente si lo usas mal**:

```python
# ❌ MAL - Lock demasiado estrecho
class BadMetrics:
    def get_snapshot(self):
        with self._lock:
            total = self._requests_total  # Capturar bajo lock
        
        with self._lock:
            errors = self._errors_total   # Liberar y volver a adquirir
        
        # ❌ Entre los dos locks, otro thread pudo cambiar valores
        # Snapshot NO es consistente
        return {
            "requests_total": total,
            "errors_total": errors,  # Puede ser de momento diferente
        }

# ✓ BIEN - Lock durante todo snapshot
class GoodMetrics:
    def get_snapshot(self):
        with self._lock:  # Adquirir una sola vez
            total = self._requests_total
            errors = self._errors_total
            # ... todas las operaciones aquí ...
            
            return {
                "requests_total": total,
                "errors_total": errors,
            }
        # Liberar cuando salgo del with
```

### P3: Evitar Deadlocks

```python
# ❌ DEADLOCK POTENCIAL
class BadLocking:
    def __init__(self):
        self.lock1 = threading.Lock()
        self.lock2 = threading.Lock()
    
    def method_a(self):
        with self.lock1:
            with self.lock2:
                # Hacer algo
                pass
    
    def method_b(self):
        with self.lock2:  # ❌ Orden inverso
            with self.lock1:  # ❌ Si method_a está aquí, DEADLOCK
                # Hacer algo
                pass

# ✓ BIEN - Siempre mismo orden de locks
class GoodLocking:
    def __init__(self):
        self.lock1 = threading.Lock()
        self.lock2 = threading.Lock()
    
    def method_a(self):
        with self.lock1:
            with self.lock2:
                pass
    
    def method_b(self):
        with self.lock1:  # ✓ Mismo orden
            with self.lock2:
                pass
```

### P4: threading.Lock vs RLock

```python
# threading.Lock - Standard
# - Un thread adquiere, otro espera
# - Si mismo thread intenta 2x → DEADLOCK

lock = threading.Lock()

with lock:
    # Aquí estoy dentro
    with lock:  # ❌ DEADLOCK - mismo thread intenta 2x
        pass

# threading.RLock - Reentrant
# - Permite que mismo thread adquiera múltiples veces
# - Usa contador interno

rlock = threading.RLock()

with rlock:
    # Aquí estoy dentro
    with rlock:  # ✓ OK - contador interno = 2
        pass
    # contador decrece a 1
# contador decrece a 0

# Usar RLock si tienes código reentrante:
class Metrics:
    def __init__(self):
        self._lock = threading.RLock()  # Mejor para métricas
    
    def get_snapshot(self):
        with self._lock:
            avg = self.get_avg_latency_ms()  # Usa lock internamente
            # Con RLock: OK, con Lock: DEADLOCK
    
    def get_avg_latency_ms(self):
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            return sum(self._latencies_ms) / len(self._latencies_ms)
```

### P5: Alternativas a Locks (Cuando Aplicable)

```python
# 1. Queue (thread-safe por diseño)
from queue import Queue

task_queue = Queue()  # Internamente usa lock
task_queue.put(item)  # Thread-safe
item = task_queue.get()  # Thread-safe

# 2. Atomic Operations (en librerías especializadas)
from threading import Event

event = Event()  # Internamente atomic
event.set()  # Thread-safe
event.is_set()  # Thread-safe

# 3. Multiprocessing (No compartir, pasar mensajes)
from multiprocessing import Manager

with Manager() as manager:
    shared_dict = manager.dict()  # Sincronizado entre procesos
    shared_dict['key'] = value  # Thread-safe y process-safe
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: Race Condition en Tests

```python
# test_metrics.py
def test_concurrent_increments():
    """Test que falla sin lock, pasa con lock."""
    metrics = Metrics()
    
    def increment_many():
        for _ in range(1000):
            metrics.inc_requests()
    
    # Ejecutar 10 threads en paralelo
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increment_many) for _ in range(10)]
        concurrent.futures.wait(futures)
    
    # ✓ Con lock: requests_total == 10,000
    # ❌ Sin lock: requests_total < 10,000 (lost updates)
    assert metrics.get_snapshot()["requests_total"] == 10_000
```

### Señal 2: Valores Inconsistentes en Snapshot

```python
# ❌ Sin lock en get_snapshot
metrics_before = metrics.get_snapshot()
# {"requests_total": 10, "avg_latency_ms": 50.5}

metrics_after = metrics.get_snapshot()
# {"requests_total": 10, "avg_latency_ms": 45.2}

# avg_latency_ms cambió pero requests_total es igual
# = Snapshot NO fue atómico

# ✓ Con lock en get_snapshot
# Cambios siempre consistentes (O se ven ambos, O ninguno)
```

### Señal 3: Load Testing Revela Issues

```bash
# Ejecutar muchos requests concurrentes
ab -n 1000 -c 100 http://localhost:8001/query

# Sin thread-safety:
# - Algunos requests fallan
# - Contadores inconsistentes
# - Latencias negativas o NaN

# Con thread-safety:
# - Todos los requests exitosos
# - Contadores consistentes
# - Métricas confiables
```

---

## 💻 Código Reutilizable

### Componente: MetricsThreadSafe

```python
# services/api/app/observability.py
"""
Implementación thread-safe de métricas.
Reutilizable para cualquier aplicación.
"""

import threading
import time
from typing import Optional, Dict, List
from collections import deque
from contextlib import contextmanager

class ThreadSafeMetrics:
    """
    Contenedor thread-safe de métricas.
    
    Attributes:
        _lock: threading.RLock para proteger acceso
        _counters: dict de contadores
        _samples: dict de muestras (deques)
    """
    
    def __init__(self, sample_window: int = 1000):
        """
        Args:
            sample_window: Número de muestras a mantener para percentiles
        """
        self._lock = threading.RLock()
        self._sample_window = sample_window
        
        # Contadores
        self._counters: Dict[str, int] = {}
        
        # Muestras para cálculos (latencias, etc)
        self._samples: Dict[str, deque] = {}
    
    def register_counter(self, name: str, initial: int = 0) -> None:
        """Registrar un nuevo contador."""
        with self._lock:
            self._counters[name] = initial
    
    def register_samples(self, name: str) -> None:
        """Registrar un nuevo tipo de muestras."""
        with self._lock:
            self._samples[name] = deque(maxlen=self._sample_window)
    
    def increment(self, counter_name: str, amount: int = 1) -> None:
        """Incrementar contador de forma thread-safe."""
        with self._lock:
            if counter_name not in self._counters:
                raise KeyError(f"Counter '{counter_name}' no registrado")
            self._counters[counter_name] += amount
    
    def add_sample(self, sample_name: str, value: float) -> None:
        """Agregar muestra de forma thread-safe."""
        with self._lock:
            if sample_name not in self._samples:
                raise KeyError(f"Sample '{sample_name}' no registrado")
            self._samples[sample_name].append(value)
    
    def get_counter(self, name: str) -> int:
        """Obtener valor de contador."""
        with self._lock:
            return self._counters.get(name, 0)
    
    def get_percentile(self, sample_name: str, percentile: float) -> float:
        """Calcular percentil de muestras."""
        with self._lock:
            if sample_name not in self._samples:
                return 0.0
            
            samples = self._samples[sample_name]
            if not samples:
                return 0.0
            
            sorted_samples = sorted(samples)
            idx = int(len(sorted_samples) * (percentile / 100.0))
            return float(sorted_samples[min(idx, len(sorted_samples) - 1)])
    
    def get_average(self, sample_name: str) -> float:
        """Obtener promedio de muestras."""
        with self._lock:
            if sample_name not in self._samples:
                return 0.0
            
            samples = self._samples[sample_name]
            if not samples:
                return 0.0
            
            return sum(samples) / len(samples)
    
    def get_snapshot(self) -> Dict:
        """Obtener snapshot atómico de todas las métricas."""
        with self._lock:
            snapshot = {}
            
            # Counters
            snapshot.update(self._counters)
            
            # Estadísticas de muestras
            for name, samples in self._samples.items():
                if samples:
                    snapshot[f"{name}_avg"] = round(sum(samples) / len(samples), 2)
                    snapshot[f"{name}_p95"] = round(self.get_percentile(name, 95), 2)
                    snapshot[f"{name}_count"] = len(samples)
                else:
                    snapshot[f"{name}_avg"] = 0.0
                    snapshot[f"{name}_p95"] = 0.0
                    snapshot[f"{name}_count"] = 0
            
            return snapshot
    
    def reset(self) -> None:
        """Reiniciar todas las métricas."""
        with self._lock:
            for key in self._counters:
                self._counters[key] = 0
            for key in self._samples:
                self._samples[key].clear()

@contextmanager
def time_operation(metrics: ThreadSafeMetrics, sample_name: str):
    """
    Context manager para medir tiempo de operaciones.
    
    Uso:
        with time_operation(metrics, "query_latency"):
            # hacer algo
            pass
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics.add_sample(sample_name, elapsed_ms)


# Uso:
if __name__ == "__main__":
    # Crear métricas
    metrics = ThreadSafeMetrics()
    
    # Registrar contadores
    metrics.register_counter("requests_total")
    metrics.register_counter("errors_total")
    
    # Registrar muestras
    metrics.register_samples("latency_ms")
    
    # Usar en requests
    metrics.increment("requests_total")
    
    with time_operation(metrics, "latency_ms"):
        # Hacer algo
        pass
    
    # Obtener snapshot
    print(metrics.get_snapshot())
    # {'requests_total': 1, 'errors_total': 0, 
    #  'latency_ms_avg': 10.5, 'latency_ms_p95': 10.5, ...}
```

### Script de Testing: `tests/test_metrics_thread_safety.py`

```python
#!/usr/bin/env python3
"""
Tests de thread-safety para métricas.
Ejecutar: pytest tests/test_metrics_thread_safety.py -v
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from app.observability import Metrics, Timer


class TestMetricsThreadSafety:
    """Suite de tests para thread-safety."""
    
    def test_concurrent_increments(self):
        """Test que múltiples threads pueden incrementar sin pérdida."""
        metrics = Metrics()
        num_threads = 10
        increments_per_thread = 1000
        
        def increment_many():
            for _ in range(increments_per_thread):
                metrics.inc_requests()
        
        # Ejecutar threads en paralelo
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(increment_many) for _ in range(num_threads)]
            for future in futures:
                future.result()
        
        # Verificar que todos los increments se registraron
        expected = num_threads * increments_per_thread
        actual = metrics.get_snapshot()["requests_total"]
        
        assert actual == expected, f"Expected {expected}, got {actual}"
    
    def test_snapshot_consistency(self):
        """Test que snapshot es atómico y consistente."""
        metrics = Metrics()
        
        # Estado inicial
        snapshot1 = metrics.get_snapshot()
        assert snapshot1["requests_total"] == 0
        
        # Incrementar requests
        for _ in range(100):
            metrics.inc_requests()
            metrics.record_latency(10.0)
        
        # Snapshot debe ser consistente
        snapshot2 = metrics.get_snapshot()
        assert snapshot2["requests_total"] == 100
        assert snapshot2["latency_samples"] == 100
        
        # Verificar que no hay valores parciales
        # (ambos valores deben reflejar el mismo estado)
        assert snapshot2["requests_total"] >= snapshot2["latency_samples"]
    
    def test_error_increments_concurrent(self):
        """Test que error counter es thread-safe."""
        metrics = Metrics()
        errors_per_thread = 500
        num_threads = 5
        
        def record_errors():
            for _ in range(errors_per_thread):
                metrics.inc_errors()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_errors) for _ in range(num_threads)]
            for future in futures:
                future.result()
        
        expected = num_threads * errors_per_thread
        actual = metrics.get_snapshot()["errors_total"]
        assert actual == expected
    
    def test_latency_recording_concurrent(self):
        """Test que latencias se registran correctamente."""
        metrics = Metrics()
        latencies_per_thread = 100
        num_threads = 10
        
        def record_latencies():
            for i in range(latencies_per_thread):
                metrics.record_latency(float(i % 100))
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_latencies) for _ in range(num_threads)]
            for future in futures:
                future.result()
        
        snapshot = metrics.get_snapshot()
        expected_samples = num_threads * latencies_per_thread
        assert snapshot["latency_samples"] == expected_samples
        assert snapshot["avg_latency_ms"] > 0
        assert snapshot["p95_latency_ms"] > 0
    
    def test_timer_context_manager(self):
        """Test que Timer mide latencia correctamente."""
        metrics = Metrics()
        
        with Timer() as timer:
            time.sleep(0.01)  # 10ms
        
        snapshot = metrics.get_snapshot()
        assert snapshot["latency_samples"] == 1
        # Debería ser ~10ms
        assert snapshot["avg_latency_ms"] >= 8  # Allow some variance
    
    def test_snapshot_does_not_block_increments(self):
        """Test que leer snapshot no bloquea increments."""
        metrics = Metrics()
        results = []
        
        def getter():
            # Obtener snapshot muchas veces
            for _ in range(100):
                metrics.get_snapshot()
        
        def incrementer():
            # Incrementar mientras se obtienen snapshots
            for i in range(100):
                metrics.inc_requests()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            getter_future = executor.submit(getter)
            incr_futures = [executor.submit(incrementer) for _ in range(2)]
            
            getter_future.result()
            for future in incr_futures:
                future.result()
        
        # Debe haber registrado todos los increments
        final_count = metrics.get_snapshot()["requests_total"]
        assert final_count == 200  # 2 threads x 100 each


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 📋 Checklist de Implementación

### Antes de agregar contadores compartidos

- [ ] Identificar si múltiples threads accederán
- [ ] Usar `threading.Lock()` o `threading.RLock()`
- [ ] Proteger TODAS las operaciones con `with self._lock:`
- [ ] Granularidad correcta: todo snapshot bajo UN lock
- [ ] Evitar deadlocks: mismo orden de locks siempre
- [ ] Tests concurrentes con `ThreadPoolExecutor`
- [ ] Load testing: `ab -n 1000 -c 100 http://localhost:8001/endpoint`

### En revisión de código

```python
# Preguntas a hacer:
1. ¿Este contador es accedido desde múltiples threads? → Necesita lock
2. ¿El lock protege TODAS las operaciones? → Revisar `with self._lock:`
3. ¿Hay snapshot? ¿Está bajo un solo lock? → Sí ✓
4. ¿Riesgo de deadlock? → Revisar orden de locks
5. ¿Hay tests concurrentes? → ThreadPoolExecutor, increments muchos
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-01-DOCKER-NETWORKING.md` (puertos en docker)
- Ver: `LESSONS-LEARNED-02-ROUTER-INTEGRATION.md` (routers FastAPI)
- Ver: `LESSONS-LEARNED-04-LLM-FALLBACK.md` (manejo de errores)

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - Thread safety |

---

## ✨ Key Takeaway

> **"Nunca compartas estado entre threads sin lock. Usa `threading.Lock()` o `threading.RLock()` para proteger contadores e implementa snapshot bajo un único lock para consistencia atómica."**

```python
# Patrón ganador
class Metrics:
    def __init__(self):
        self._lock = threading.RLock()  # Reentrant
        self._counters = {}
    
    def increment(self, name: str):
        with self._lock:  # ✓ Siempre dentro de lock
            self._counters[name] += 1
    
    def get_snapshot(self):
        with self._lock:  # ✓ Un solo lock
            return dict(self._counters)  # Copia atómica
```

---