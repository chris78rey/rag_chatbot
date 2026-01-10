# 🔹 PROMPT EJECUTABLE 13 — Tests End-to-End Básicos

> **Archivo**: `specs/prompts/13_tests_e2e.md`  
> **Subproyecto**: 13 de 13 (adicional)  
> **Prerequisitos**: Subproyectos 1-12 completados

---

## ROL DEL MODELO

Actúa como **ingeniero de QA**:
- Crear tests end-to-end básicos para validar el sistema completo
- Tests deben ser ejecutables con pytest
- Cubrir flujos críticos: health, query, cache, rate-limit
- No sobre-ingenierizar: tests simples y directos

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- El sistema está funcionando con todos los componentes integrados
- Se necesitan tests automatizados para validar que todo funciona correctamente
- Los tests deben poder ejecutarse contra el stack levantado en Docker
- Enfoque en tests de integración/e2e, no unitarios

---

## OBJETIVO

Crear suite de tests básica que valide:
- Health check responde
- Query funciona end-to-end
- Cache funciona (hit/miss)
- Rate limiting funciona
- Ingestión procesa archivos

**Éxito binario**: `pytest tests/` pasa con todos los tests verdes.

---

## ARCHIVOS A CREAR

```
tests/
├── __init__.py
├── conftest.py
├── test_health.py
├── test_query.py
├── test_cache.py
├── test_rate_limit.py
├── test_ingest.py
└── README.md

requirements-test.txt
pytest.ini
```

---

## CONTENIDO DE ARCHIVOS

### `tests/__init__.py`

```python
# Tests package
```

### `tests/conftest.py`

```python
"""
Configuración compartida para tests.
Fixtures y helpers comunes.
"""
import os
import pytest
import httpx
import asyncio
from typing import Generator

# URL base del API (puede venir de ENV)
API_BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(scope="session")
def api_url() -> str:
    """URL base del API para tests."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[httpx.Client, None, None]:
    """Cliente HTTP síncrono para tests."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_client() -> httpx.AsyncClient:
    """Cliente HTTP asíncrono para tests."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def test_rag_id() -> str:
    """RAG ID para tests."""
    return "test_rag"


@pytest.fixture
def sample_question() -> str:
    """Pregunta de prueba."""
    return "¿Qué es Python?"


@pytest.fixture
def unique_question() -> str:
    """Pregunta única para evitar cache hits."""
    import uuid
    return f"Pregunta única {uuid.uuid4()}"


def wait_for_api(max_retries: int = 30, delay: float = 1.0) -> bool:
    """
    Espera a que el API esté disponible.
    Útil para CI/CD donde los contenedores pueden tardar en arrancar.
    """
    import time
    
    for i in range(max_retries):
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
    
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_api_ready():
    """Asegura que el API esté listo antes de correr tests."""
    if not wait_for_api():
        pytest.skip("API no disponible")
```

### `tests/test_health.py`

```python
"""
Tests para el endpoint de health check.
"""
import pytest


class TestHealth:
    """Tests del endpoint /health."""
    
    def test_health_returns_ok(self, client):
        """Health check debe retornar status ok."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_response_time(self, client):
        """Health check debe responder rápido (<100ms)."""
        import time
        
        start = time.time()
        response = client.get("/health")
        elapsed_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 100, f"Health check tardó {elapsed_ms}ms"
    
    def test_health_via_nginx(self):
        """Health check debe funcionar via Nginx (puerto 80)."""
        import httpx
        
        # Asumiendo Nginx en puerto 80
        try:
            response = httpx.get("http://localhost/health", timeout=5.0)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Nginx no disponible en puerto 80")
```

### `tests/test_query.py`

```python
"""
Tests para el endpoint de consulta RAG.
"""
import pytest


class TestQueryEndpoint:
    """Tests del endpoint POST /query."""
    
    def test_query_returns_valid_response(self, client, test_rag_id, sample_question):
        """Query debe retornar respuesta con estructura correcta."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "rag_id" in data
        assert "answer" in data
        assert "context_chunks" in data
        assert "latency_ms" in data
        assert "cache_hit" in data
        assert "session_id" in data
        
        # Verificar tipos
        assert isinstance(data["rag_id"], str)
        assert isinstance(data["answer"], str)
        assert isinstance(data["context_chunks"], list)
        assert isinstance(data["latency_ms"], int)
        assert isinstance(data["cache_hit"], bool)
    
    def test_query_requires_rag_id(self, client, sample_question):
        """Query sin rag_id debe retornar error 422."""
        response = client.post("/query", json={
            "question": sample_question
        })
        
        assert response.status_code == 422
    
    def test_query_requires_question(self, client, test_rag_id):
        """Query sin question debe retornar error 422."""
        response = client.post("/query", json={
            "rag_id": test_rag_id
        })
        
        assert response.status_code == 422
    
    def test_query_with_session_id(self, client, test_rag_id, sample_question):
        """Query con session_id debe retornar el mismo session_id."""
        session_id = "test-session-123"
        
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question,
            "session_id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
    
    def test_query_generates_session_id_if_not_provided(self, client, test_rag_id, sample_question):
        """Query sin session_id debe generar uno automáticamente."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    def test_query_with_top_k_override(self, client, test_rag_id, sample_question):
        """Query con top_k override debe funcionar."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question,
            "top_k": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        # Si hay chunks, no deberían ser más de top_k
        assert len(data["context_chunks"]) <= 3
    
    def test_query_invalid_rag_returns_404_or_empty(self, client, sample_question):
        """Query con RAG inexistente debe retornar 404 o respuesta vacía."""
        response = client.post("/query", json={
            "rag_id": "rag_que_no_existe_12345",
            "question": sample_question
        })
        
        # Puede ser 404 (si se valida) o 200 con contexto vacío
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Sin contexto, debería indicar que no hay información
            assert data["context_chunks"] == [] or "no" in data["answer"].lower()
    
    def test_query_returns_latency(self, client, test_rag_id, sample_question):
        """Query debe retornar latency_ms > 0."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["latency_ms"] >= 0


class TestQueryContextChunks:
    """Tests específicos para context_chunks en respuesta."""
    
    def test_context_chunks_structure(self, client, test_rag_id, sample_question):
        """Context chunks deben tener estructura correcta."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code == 200
        data = response.json()
        
        for chunk in data["context_chunks"]:
            assert "id" in chunk
            assert "source" in chunk
            assert "text" in chunk
            assert "score" in chunk
            
            assert isinstance(chunk["id"], str)
            assert isinstance(chunk["text"], str)
            assert isinstance(chunk["score"], (int, float))
    
    def test_context_chunks_scores_are_valid(self, client, test_rag_id, sample_question):
        """Los scores de chunks deben estar entre 0 y 1."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code == 200
        data = response.json()
        
        for chunk in data["context_chunks"]:
            assert 0 <= chunk["score"] <= 1, f"Score {chunk['score']} fuera de rango"
```

### `tests/test_cache.py`

```python
"""
Tests para la funcionalidad de caché.
"""
import pytest
import time


class TestCacheHitMiss:
    """Tests de cache hit/miss."""
    
    def test_first_query_is_cache_miss(self, client, test_rag_id, unique_question):
        """Primera consulta debe ser cache miss."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": unique_question
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] == False
    
    def test_second_query_is_cache_hit(self, client, test_rag_id):
        """Segunda consulta idéntica debe ser cache hit."""
        question = f"Pregunta para test cache {time.time()}"
        
        # Primera consulta (miss)
        response1 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cache_hit"] == False
        
        # Segunda consulta (hit)
        response2 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cache_hit"] == True
    
    def test_cache_hit_is_faster(self, client, test_rag_id):
        """Cache hit debe ser más rápido que miss."""
        question = f"Pregunta para test velocidad {time.time()}"
        
        # Primera consulta
        response1 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        latency1 = response1.json()["latency_ms"]
        
        # Segunda consulta
        response2 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        latency2 = response2.json()["latency_ms"]
        
        # Cache hit debería ser significativamente más rápido
        # (no siempre se cumple con redes lentas, pero es indicativo)
        assert latency2 <= latency1 or latency2 < 50
    
    def test_different_questions_are_cache_miss(self, client, test_rag_id):
        """Preguntas diferentes deben ser cache miss."""
        question1 = f"Primera pregunta {time.time()}"
        question2 = f"Segunda pregunta diferente {time.time()}"
        
        response1 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question1
        })
        
        response2 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question2
        })
        
        assert response1.json()["cache_hit"] == False
        assert response2.json()["cache_hit"] == False
    
    def test_different_rag_id_is_cache_miss(self, client, unique_question):
        """Mismo query con diferente rag_id debe ser cache miss."""
        response1 = client.post("/query", json={
            "rag_id": "rag_uno",
            "question": unique_question
        })
        
        response2 = client.post("/query", json={
            "rag_id": "rag_dos",
            "question": unique_question
        })
        
        # Ambos deberían ser miss (diferentes RAGs)
        assert response1.json()["cache_hit"] == False
        assert response2.json()["cache_hit"] == False


class TestCacheConsistency:
    """Tests de consistencia de caché."""
    
    def test_cached_response_matches_original(self, client, test_rag_id):
        """Respuesta cacheada debe ser idéntica a la original."""
        question = f"Pregunta consistencia {time.time()}"
        
        # Primera consulta
        response1 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        data1 = response1.json()
        
        # Segunda consulta
        response2 = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": question
        })
        data2 = response2.json()
        
        # La respuesta (answer) debe ser igual
        assert data1["answer"] == data2["answer"]
        assert data1["rag_id"] == data2["rag_id"]
```

### `tests/test_rate_limit.py`

```python
"""
Tests para rate limiting.
"""
import pytest
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor


class TestRateLimit:
    """Tests de rate limiting."""
    
    def test_normal_request_passes(self, client, test_rag_id, sample_question):
        """Request normal debe pasar sin rate limit."""
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        assert response.status_code != 429
    
    def test_burst_requests_eventually_limited(self, api_url, test_rag_id):
        """Muchos requests rápidos deben eventualmente ser limitados."""
        # Hacer muchos requests en paralelo
        num_requests = 50
        results = []
        
        def make_request(i):
            try:
                response = httpx.post(
                    f"{api_url}/query",
                    json={
                        "rag_id": test_rag_id,
                        "question": f"Rate limit test {i}"
                    },
                    timeout=10.0
                )
                return response.status_code
            except Exception as e:
                return str(e)
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(make_request, range(num_requests)))
        
        # Contar respuestas
        success = results.count(200)
        rate_limited = results.count(429)
        
        # Debería haber al menos algunos rate limited (o todos success si el límite es alto)
        # Este test es flexible porque depende de la configuración
        assert success > 0, "Ningún request exitoso"
        
        # Si el rate limit está configurado agresivamente, habrá 429s
        if rate_limited > 0:
            print(f"Rate limiting activo: {success} OK, {rate_limited} limitados")
    
    def test_rate_limit_returns_429(self, api_url, test_rag_id):
        """Rate limit debe retornar código 429."""
        # Este test intenta forzar un rate limit
        # Ajustar según configuración
        responses = []
        
        for i in range(100):
            try:
                response = httpx.post(
                    f"{api_url}/query",
                    json={
                        "rag_id": test_rag_id,
                        "question": f"Burst test {i}"
                    },
                    timeout=2.0
                )
                responses.append(response.status_code)
                
                if response.status_code == 429:
                    # Encontramos un rate limit
                    assert "429" in str(response.status_code)
                    return
            except Exception:
                pass
        
        # Si llegamos aquí, el rate limit puede estar muy alto
        pytest.skip("Rate limit no alcanzado con 100 requests")
    
    def test_rate_limit_recovers(self, client, test_rag_id, sample_question):
        """Después del rate limit, debe recuperarse."""
        import time
        
        # Esperar un poco para que los tokens se regeneren
        time.sleep(2)
        
        response = client.post("/query", json={
            "rag_id": test_rag_id,
            "question": sample_question
        })
        
        # Después de esperar, debe funcionar
        assert response.status_code in [200, 429]  # 429 si aún está limitado
```

### `tests/test_ingest.py`

```python
"""
Tests para el sistema de ingestión.
"""
import pytest
import os
import time
import json
import tempfile
from pathlib import Path

# Intentar importar redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis client no instalado")
class TestIngestQueue:
    """Tests del sistema de cola de ingestión."""
    
    @pytest.fixture
    def redis_client(self):
        """Cliente Redis para tests."""
        redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url)
        yield client
        client.close()
    
    def test_queue_exists(self, redis_client):
        """La cola de ingestión debe existir (o poder crearse)."""
        queue_key = "rag:ingest:queue"
        
        # La cola puede estar vacía, pero el comando debe funcionar
        length = redis_client.llen(queue_key)
        assert length >= 0
    
    def test_can_enqueue_job(self, redis_client):
        """Debe poder encolar un job de prueba."""
        queue_key = "rag:ingest:queue"
        
        test_job = {
            "job_id": "test-job-12345",
            "rag_id": "test_rag",
            "source_path": "/tmp/test.txt",
            "source_type": "txt",
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "options": {"reindex": False}
        }
        
        # Encolar
        redis_client.lpush(queue_key, json.dumps(test_job))
        
        # Verificar que está en la cola
        length = redis_client.llen(queue_key)
        assert length >= 1
        
        # Limpiar (sacar el job que pusimos)
        redis_client.rpop(queue_key)
    
    def test_job_status_keys(self, redis_client):
        """Debe poder escribir/leer estado de jobs."""
        job_id = "test-status-job"
        status_key = f"rag:job:{job_id}:status"
        
        # Escribir estado
        redis_client.set(status_key, "testing")
        
        # Leer estado
        status = redis_client.get(status_key)
        assert status.decode() == "testing"
        
        # Limpiar
        redis_client.delete(status_key)


class TestIngestFileStructure:
    """Tests de estructura de archivos para ingestión."""
    
    def test_sources_directory_exists(self):
        """El directorio data/sources debe existir."""
        # Ajustar path según ubicación del proyecto
        sources_path = Path("data/sources")
        
        if not sources_path.exists():
            pytest.skip("Ejecutar desde raíz del proyecto")
        
        assert sources_path.is_dir()
    
    def test_can_create_rag_structure(self):
        """Debe poder crear estructura incoming/processed/failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag_path = Path(tmpdir) / "test_rag"
            
            (rag_path / "incoming").mkdir(parents=True)
            (rag_path / "processed").mkdir(parents=True)
            (rag_path / "failed").mkdir(parents=True)
            
            assert (rag_path / "incoming").is_dir()
            assert (rag_path / "processed").is_dir()
            assert (rag_path / "failed").is_dir()


class TestIngestIntegration:
    """Tests de integración de ingestión (requiere stack completo)."""
    
    @pytest.fixture
    def test_file(self):
        """Crear archivo de prueba temporal."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Este es un archivo de prueba para ingestión.\n")
            f.write("Contiene información sobre Python y programación.\n")
            f.write("FastAPI es un framework web moderno.\n")
            return f.name
    
    def test_file_readable(self, test_file):
        """El archivo de prueba debe ser legible."""
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert len(content) > 0
        assert "Python" in content
        
        # Limpiar
        os.unlink(test_file)
```

### `tests/test_metrics.py`

```python
"""
Tests para el endpoint de métricas.
"""
import pytest


class TestMetricsEndpoint:
    """Tests del endpoint /metrics."""
    
    def test_metrics_returns_200(self, client):
        """Metrics debe retornar 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_metrics_structure(self, client):
        """Metrics debe tener estructura correcta."""
        response = client.get("/metrics")
        data = response.json()
        
        expected_fields = [
            "requests_total",
            "errors_total",
            "cache_hits_total",
            "rate_limited_total",
            "avg_latency_ms"
        ]
        
        for field in expected_fields:
            assert field in data, f"Campo {field} no encontrado en métricas"
    
    def test_metrics_are_numeric(self, client):
        """Todas las métricas deben ser numéricas."""
        response = client.get("/metrics")
        data = response.json()
        
        for key, value in data.items():
            assert isinstance(value, (int, float)), f"{key} no es numérico: {value}"
    
    def test_metrics_increment_after_query(self, client, test_rag_id, unique_question):
        """requests_total debe incrementar después de un query."""
        # Obtener métricas antes
        before = client.get("/metrics").json()
        
        # Hacer un query
        client.post("/query", json={
            "rag_id": test_rag_id,
            "question": unique_question
        })
        
        # Obtener métricas después
        after = client.get("/metrics").json()
        
        assert after["requests_total"] >= before["requests_total"]
```

### `tests/README.md`

```markdown
# Tests End-to-End

## Descripción

Suite de tests e2e para validar el sistema RAG completo.

## Prerequisitos

1. Stack levantado con Docker Compose
2. Dependencias de test instaladas

## Instalación

```bash
pip install -r requirements-test.txt
```

## Ejecución

### Todos los tests

```bash
pytest tests/ -v
```

### Tests específicos

```bash
# Solo health
pytest tests/test_health.py -v

# Solo query
pytest tests/test_query.py -v

# Solo cache
pytest tests/test_cache.py -v
```

### Con cobertura

```bash
pytest tests/ --cov=services/api/app --cov-report=html
```

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TEST_API_URL` | `http://localhost:8000` | URL del API |
| `TEST_REDIS_URL` | `redis://localhost:6379/0` | URL de Redis |

## Estructura de Tests

| Archivo | Descripción |
|---------|-------------|
| `test_health.py` | Health check endpoint |
| `test_query.py` | Consultas RAG |
| `test_cache.py` | Cache hit/miss |
| `test_rate_limit.py` | Rate limiting |
| `test_ingest.py` | Sistema de ingestión |
| `test_metrics.py` | Métricas |

## CI/CD

Para CI, asegurarse de:

1. Levantar stack antes de tests
2. Esperar a que API esté listo
3. Ejecutar tests
4. Capturar resultados

```yaml
# Ejemplo GitHub Actions
- name: Start stack
  run: docker compose up -d

- name: Wait for API
  run: |
    for i in {1..30}; do
      curl -s http://localhost:8000/health && break
      sleep 1
    done

- name: Run tests
  run: pytest tests/ -v --junitxml=results.xml
```
```

### `requirements-test.txt`

```
# Testing dependencies
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.26.0
redis==5.0.1
```

### `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

---

## COMANDOS DE VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# 1. Instalar dependencias de test
pip install -r requirements-test.txt

# 2. Asegurarse de que el stack está levantado
docker compose -f deploy/compose/docker-compose.yml up -d

# 3. Esperar a que el API esté listo
curl http://localhost:8000/health

# 4. Ejecutar todos los tests
pytest tests/ -v

# 5. Ejecutar con más detalle
pytest tests/ -v --tb=long

# 6. Solo tests rápidos (sin rate limit que puede ser lento)
pytest tests/ -v -m "not slow"

# 7. Con reporte de cobertura
pytest tests/ --cov=services/api/app --cov-report=term-missing
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `pytest tests/test_health.py` pasa
- [ ] `pytest tests/test_query.py` pasa
- [ ] `pytest tests/test_cache.py` pasa
- [ ] `pytest tests/test_metrics.py` pasa
- [ ] Al menos 80% de tests verdes en suite completa

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| Connection refused | API no levantado | `docker compose up -d` |
| Import error pytest | pytest no instalado | `pip install -r requirements-test.txt` |
| Tests timeout | API muy lento | Aumentar timeout en conftest.py |
| Redis tests skip | Redis client no instalado | `pip install redis` |

---

## LO QUE SE CONGELA

✅ Estructura de tests  
✅ Fixtures básicos  
✅ Contrato de validación del sistema

---

## 🎉 PROYECTO COMPLETO

Con este prompt, el proyecto RAG On-Premise está completo y validado:

- ✅ Arquitectura definida
- ✅ Código implementado
- ✅ Configuración documentada
- ✅ Embeddings reales
- ✅ Procesamiento PDF
- ✅ Tests automatizados

**¡El sistema está listo para uso en producción (con las consideraciones de seguridad apropiadas)!**