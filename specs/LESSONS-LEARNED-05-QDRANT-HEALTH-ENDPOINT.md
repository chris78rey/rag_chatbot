# Lecciones Aprendidas #5: Qdrant Health Endpoint Discrepancy

**Subproject 10 - State Verification & Management**

---

## 🎯 Problema Identificado

**Qdrant `/health` endpoint retorna 404 en lugar de 200**

Durante la implementación de verificación de estado (SP10), el script de validación falló al intentar verificar la salud del servicio Qdrant:

```
✗ FAIL: Qdrant Health
ERROR: Qdrant health check failed: 404
```

El endpoint `/health` que es estándar en muchos servicios no existe en Qdrant, causando que todas las verificaciones de estado del vector database fallaran, impidiendo completar la validación del sistema.

---

## 🔍 Causa Raíz

### 1. Asunción Incorrecta sobre API Standard

**El problema**: Se asumió que Qdrant expone un endpoint `/health` siguiendo la convención REST común.

```python
# ❌ INCORRECTO - Asunción de endpoint estándar
response = requests.get(f"{QDRANT_BASE_URL}/health", timeout=5)
# Retorna 404 porque `/health` no existe en Qdrant
```

**La realidad**: Qdrant utiliza `/readyz` (readiness check) y `/livez` (liveness check) siguiendo la convención de Kubernetes, no la convención REST tradicional.

### 2. Falta de Validación de API antes de Implementación

No se consultó la documentación de Qdrant antes de codificar la verificación. El endpoint correcto debería haber sido identificado durante la fase de diseño.

### 3. Pruebas Insuficientes en Ambiente Real

La verificación se escribió sin probar contra un instancia real de Qdrant en ejecución. Si se hubiera testado localmente, el error habría sido detectado inmediatamente.

### 4. Acceso Restringido desde Host

Qdrant en Docker solo era accesible desde dentro de la red de Docker (desde el contenedor `api`), no desde el host.

```
Host (Windows)
    ↓ (localhost:6333 ❌ NO ACCESIBLE)
    ↓
Docker Network (rag_network)
    ↓ (qdrant:6333 ✓ ACCESIBLE)
    ↓
Qdrant Container
```

---

## ✅ Solución Implementada

### Paso 1: Identificar el Endpoint Correcto

Probamos los endpoints de Qdrant desde dentro del contenedor:

```bash
# ❌ Este falla
docker exec api curl -v http://qdrant:6333/health
# Resultado: 404 Not Found

# ✓ Este funciona
docker exec api curl -s http://qdrant:6333/readyz
# Resultado: all shards are ready
```

**Endpoints correctos en Qdrant**:
- `/readyz` - Readiness check (Kubernetes style)
- `/livez` - Liveness check (Kubernetes style)
- `/health` - NO EXISTE (causa 404)

### Paso 2: Usar docker exec para Acceso a Servicios Internos

Implementamos una función helper que ejecuta comandos dentro del contenedor API para acceder a servicios internos:

```python
def _docker_exec_curl(self, url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    """Execute curl inside Docker container to access internal services."""
    try:
        cmd = [
            "docker", "exec", "api",
            "curl", "-s", "-w", "\n%{http_code}", "-m", str(timeout), url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        
        if result.returncode != 0:
            return False, result.stderr or "Unknown error", 0
        
        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1]) if lines[-1].isdigit() else 0
        content = '\n'.join(lines[:-1]) if len(lines) > 1 else ""
        
        return True, content, status_code
    except Exception as e:
        return False, str(e), 0
```

### Paso 3: Actualizar Verificación para Usar Endpoint Correcto

```python
def verify_qdrant_health(self) -> bool:
    """Verify Qdrant service is healthy using correct endpoint."""
    success, content, status_code = self._docker_exec_curl("http://qdrant:6333/readyz")
    
    if success and status_code == 200:
        return True
    else:
        self.errors.append(f"Qdrant health check failed: {status_code or 'unreachable'}")
        return False
```

### Paso 4: Validación

```bash
python scripts/verify_state.py
# Resultado:
# ✓ PASS: Qdrant Health
```

---

## 🛡️ Principios Preventivos Clave

### P1: Consultar Documentación Antes de Codificar

**Principio**: Antes de asumir una API o comportamiento, valida contra la documentación oficial.

```python
# ❌ MAL - Asumir endpoints sin validar
def verify_service():
    response = requests.get("http://service:port/health")
    return response.status_code == 200

# ✓ BIEN - Consultar documentación y casos reales
# Qdrant usa /readyz según su documentación
# https://qdrant.tech/documentation/
def verify_service():
    response = requests.get("http://service:port/readyz")
    return response.status_code == 200
```

### P2: Pruebas en Ambiente Real Antes de Producción

**Principio**: Todo verificador de estado debe ser probado contra un instancia real del servicio antes de ser integrado.

```python
# ✓ MEJOR PRÁCTICA
# 1. Levantar servicio localmente
# docker run -d qdrant/qdrant:latest

# 2. Validar endpoints manualmente
# curl http://localhost:6333/readyz

# 3. Recién entonces codificar el verificador
```

### P3: Usar Convenciones de Plataforma, no Suposiciones

**Principio**: Diferentes plataformas/tecnologías pueden seguir diferentes convenciones:
- **REST tradicional**: `/health`
- **Kubernetes**: `/readyz`, `/livez`
- **Prometheus**: `/metrics`
- **gRPC**: Diferentes mecanismos

```python
# ✓ MEJOR PRÁCTICA - Detectar y adaptar
HEALTH_ENDPOINTS = {
    "qdrant": "/readyz",      # Kubernetes style
    "redis": "/ping",          # Redis style
    "postgres": "SELECT 1",    # SQL style
    "api": "/health",         # Custom REST
}

def verify_health(service: str, url: str) -> bool:
    endpoint = HEALTH_ENDPOINTS[service]
    # Llamar endpoint específico
    return check_endpoint(url, endpoint)
```

### P4: Considerar Topología de Red en Verificadores

**Principio**: Un verificador debe ser consciente de la topología de red y usar las rutas correctas para acceder a servicios.

```python
# ❌ MAL - Asume acceso directo desde host
QDRANT_URL = "http://localhost:6333"  # No accesible desde host en Docker

# ✓ BIEN - Conoce la topología
QDRANT_URL_FROM_HOST = "http://localhost:6333"     # No disponible
QDRANT_URL_FROM_DOCKER = "http://qdrant:6333"      # Disponible
# Y usar docker exec para acceder desde host
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: Status Code 404 en Verificador

```
✗ Qdrant health check failed: 404
```

**Esto significa**: El endpoint que se intenta acceder no existe en el servicio.

**Pasos a seguir**:
1. Verificar documentación oficial del servicio
2. Probar endpoints manualmente desde shell
3. Confirmar que el URL está correcto
4. Revisar changelog de versión del servicio

### Señal 2: "Connection Refused" desde Host pero Funciona desde Container

```
✗ Cannot reach Qdrant: Connection refused
# Pero funciona:
docker exec api curl http://qdrant:6333/readyz
```

**Esto significa**: El servicio está en red Docker pero no está expuesto al host.

**Pasos a seguir**:
1. Verificar `docker-compose.yml` para port mappings
2. Confirmar si es intencional (algunos servicios solo para red interna)
3. Si es necesario acceso desde host: agregar `ports:` en compose
4. Si no: usar `docker exec` para verificación desde host

### Señal 3: Cambio de Versión con Comportamiento Diferente

```
# Versión vieja (qdrant:0.11)
curl http://qdrant:6333/health    # ✓ Funciona

# Versión nueva (qdrant:latest)
curl http://qdrant:6333/readyz    # ✓ Funciona (cambio de API)
```

**Esto significa**: El servicio cambió su API entre versiones.

**Pasos a seguir**:
1. Revisar release notes / changelog
2. Actualizar verificadores
3. Usar versión específica en `docker-compose.yml`
4. Documentar cambios de API en specs

---

## 💻 Código Reutilizable

### Componente: Docker-Aware Health Checker

```python
"""
HealthChecker que es consciente de la topología Docker
Reutilizable para verificar servicios en redes Docker
"""

import subprocess
import requests
from typing import Tuple, Dict
from dataclasses import dataclass

@dataclass
class ServiceEndpoint:
    """Definición de un endpoint de servicio."""
    service_name: str
    docker_hostname: str      # Nombre en red Docker (e.g., "qdrant")
    docker_port: int
    health_path: str          # Endpoint específico (e.g., "/readyz")
    container_name: str       # Nombre del contenedor donde verificar desde
    
    @property
    def docker_url(self) -> str:
        """URL accesible desde dentro de Docker network."""
        return f"http://{self.docker_hostname}:{self.docker_port}{self.health_path}"


class DockerAwareHealthChecker:
    """Verifica salud de servicios en redes Docker."""
    
    def __init__(self, docker_container: str = "api"):
        self.docker_container = docker_container
    
    def check_via_docker_exec(self, url: str, timeout: int = 5) -> Tuple[bool, int, str]:
        """
        Ejecuta curl dentro de un contenedor Docker para acceder a servicios internos.
        
        Args:
            url: URL completa a verificar
            timeout: Timeout en segundos
            
        Returns:
            (success: bool, status_code: int, content: str)
        """
        try:
            cmd = [
                "docker", "exec", self.docker_container,
                "curl", "-s", "-w", "\n%{http_code}", "-m", str(timeout), url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            
            if result.returncode != 0:
                return False, 0, result.stderr or "Unknown error"
            
            lines = result.stdout.strip().split('\n')
            status_code = int(lines[-1]) if lines[-1].isdigit() else 0
            content = '\n'.join(lines[:-1]) if len(lines) > 1 else ""
            
            return True, status_code, content
        except Exception as e:
            return False, 0, str(e)
    
    def check_health(self, endpoint: ServiceEndpoint) -> Dict[str, any]:
        """
        Verifica salud de un servicio.
        
        Returns:
            {
                "healthy": bool,
                "status_code": int,
                "content": str,
                "service": str
            }
        """
        success, status_code, content = self.check_via_docker_exec(endpoint.docker_url)
        
        return {
            "healthy": success and status_code == 200,
            "status_code": status_code,
            "content": content,
            "service": endpoint.service_name,
            "url": endpoint.docker_url
        }


# Uso:
if __name__ == "__main__":
    checker = DockerAwareHealthChecker(docker_container="api")
    
    qdrant = ServiceEndpoint(
        service_name="qdrant",
        docker_hostname="qdrant",
        docker_port=6333,
        health_path="/readyz",
        container_name="api"
    )
    
    result = checker.check_health(qdrant)
    print(f"Qdrant healthy: {result['healthy']}")
    print(f"Status code: {result['status_code']}")
```

### Script: `scripts/diagnose-qdrant.sh`

```bash
#!/bin/bash
# Diagnóstico de Qdrant - Verifica accesibilidad y endpoints

set -e

echo "=== Qdrant Diagnostics ==="
echo ""

# Verificar si contenedor existe
if ! docker ps -a | grep -q "qdrant"; then
    echo "❌ Qdrant container not found"
    echo "Start with: docker-compose up -d qdrant"
    exit 1
fi

# Verificar si está corriendo
if ! docker ps | grep -q "qdrant"; then
    echo "❌ Qdrant container not running"
    echo "Start with: docker-compose up -d qdrant"
    exit 1
fi

echo "✓ Qdrant container is running"
echo ""

# Probar acceso desde host
echo "Testing access from host (localhost:6333)..."
if timeout 2 bash -c "</dev/tcp/127.0.0.1/6333" 2>/dev/null; then
    echo "✓ Port 6333 is accessible from host"
else
    echo "⚠ Port 6333 is NOT accessible from host (normal if using Docker network)"
fi
echo ""

# Probar desde contenedor API
echo "Testing access from api container..."

# Prueba /readyz
echo -n "  Testing /readyz endpoint... "
if docker exec api curl -s http://qdrant:6333/readyz > /dev/null 2>&1; then
    echo "✓"
else
    echo "❌"
fi

# Prueba /livez
echo -n "  Testing /livez endpoint... "
if docker exec api curl -s http://qdrant:6333/livez > /dev/null 2>&1; then
    echo "✓"
else
    echo "❌"
fi

# Prueba /health (debería fallar)
echo -n "  Testing /health endpoint... "
if docker exec api curl -s http://qdrant:6333/health > /dev/null 2>&1; then
    echo "✓ (endpoint exists)"
else
    echo "❌ (endpoint doesn't exist - EXPECTED)"
fi

echo ""
echo "=== Collections ==="
docker exec api curl -s http://qdrant:6333/collections | python -m json.tool 2>/dev/null || echo "Error fetching collections"

echo ""
echo "=== Qdrant Version ==="
docker exec api curl -s http://qdrant:6333/version | python -m json.tool 2>/dev/null || echo "Error fetching version"
```

### Script: `scripts/service-health-check.py`

```python
#!/usr/bin/env python3
"""
Service Health Check Utility
Verifica múltiples servicios con endpoints específicos
"""

import subprocess
import json
from typing import Dict, List
from dataclasses import dataclass, asdict
from enum import Enum

class ServiceType(Enum):
    """Tipos de servicios soportados."""
    QDRANT = "qdrant"
    REDIS = "redis"
    POSTGRES = "postgres"
    API = "api"
    CUSTOM = "custom"

@dataclass
class ServiceConfig:
    """Configuración de servicio."""
    name: str
    service_type: ServiceType
    docker_hostname: str
    port: int
    health_endpoint: str
    docker_container: str = "api"  # Desde dónde verificar

# Mapeo de tipos a configuraciones por defecto
DEFAULT_ENDPOINTS = {
    ServiceType.QDRANT: "/readyz",
    ServiceType.REDIS: "/ping",
    ServiceType.API: "/health",
    ServiceType.POSTGRES: None,  # SQL query
    ServiceType.CUSTOM: None,     # Especificar
}

class ServiceHealthChecker:
    """Verifica salud de múltiples servicios."""
    
    def __init__(self, docker_container: str = "api"):
        self.docker_container = docker_container
    
    def check_http_health(self, config: ServiceConfig) -> Dict:
        """Verifica salud de servicio HTTP."""
        url = f"http://{config.docker_hostname}:{config.port}{config.health_endpoint}"
        
        try:
            cmd = [
                "docker", "exec", self.docker_container,
                "curl", "-s", "-w", "\n%{http_code}", "-m", "5", url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7)
            
            lines = result.stdout.strip().split('\n')
            status_code = int(lines[-1]) if lines[-1].isdigit() else 0
            
            return {
                "service": config.name,
                "healthy": status_code == 200,
                "status_code": status_code,
                "url": url,
                "error": None
            }
        except Exception as e:
            return {
                "service": config.name,
                "healthy": False,
                "status_code": 0,
                "url": url,
                "error": str(e)
            }
    
    def check_redis_health(self, config: ServiceConfig) -> Dict:
        """Verifica salud de Redis."""
        try:
            cmd = [
                "docker", "exec", self.docker_container,
                "redis-cli", "-h", config.docker_hostname, "PING"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            is_healthy = "PONG" in result.stdout
            return {
                "service": config.name,
                "healthy": is_healthy,
                "response": result.stdout.strip(),
                "error": None if is_healthy else result.stderr
            }
        except Exception as e:
            return {
                "service": config.name,
                "healthy": False,
                "response": None,
                "error": str(e)
            }
    
    def check_all(self, services: List[ServiceConfig]) -> Dict[str, Dict]:
        """Verifica salud de múltiples servicios."""
        results = {}
        for service in services:
            if service.service_type == ServiceType.REDIS:
                result = self.check_redis_health(service)
            else:
                result = self.check_http_health(service)
            results[service.name] = result
        
        return results
    
    def print_report(self, results: Dict[str, Dict]) -> None:
        """Imprime reporte de salud."""
        print("\n" + "=" * 60)
        print("SERVICE HEALTH REPORT")
        print("=" * 60)
        
        for service_name, result in results.items():
            status = "✓ HEALTHY" if result["healthy"] else "✗ UNHEALTHY"
            print(f"{status}: {service_name}")
            if result.get("error"):
                print(f"  Error: {result['error']}")
        
        all_healthy = all(r["healthy"] for r in results.values())
        print("=" * 60)
        print(f"OVERALL: {'✓ ALL HEALTHY' if all_healthy else '✗ SOME UNHEALTHY'}")
        print("=" * 60)

# Uso:
if __name__ == "__main__":
    checker = ServiceHealthChecker()
    
    services = [
        ServiceConfig(
            name="Qdrant",
            service_type=ServiceType.QDRANT,
            docker_hostname="qdrant",
            port=6333,
            health_endpoint="/readyz"
        ),
        ServiceConfig(
            name="Redis",
            service_type=ServiceType.REDIS,
            docker_hostname="redis",
            port=6379,
            health_endpoint=""
        ),
        ServiceConfig(
            name="API",
            service_type=ServiceType.API,
            docker_hostname="api",
            port=8000,
            health_endpoint="/health"
        ),
    ]
    
    results = checker.check_all(services)
    checker.print_report(results)
```

---

## 📋 Checklist de Implementación

### Antes de Agregar Verificación de Nuevo Servicio

- [ ] Consultar documentación oficial del servicio
- [ ] Probar endpoints disponibles manualmente
  - [ ] `curl http://service:port/health` (REST estándar)
  - [ ] `curl http://service:port/readyz` (Kubernetes)
  - [ ] `curl http://service:port/livez` (Kubernetes)
  - [ ] `curl http://service:port/metrics` (Prometheus)
- [ ] Verificar topología de red (¿accesible desde host o solo desde Docker?)
- [ ] Crear script de diagnóstico específico para el servicio
- [ ] Implementar verificador
- [ ] Probar en ambiente real con servicio running
- [ ] Documentar endpoint correcto en specs
- [ ] Agregar a verificador de estado global

### En Revisión de Código

```python
# Preguntas a hacer:
1. ¿Se consultó la documentación del servicio? → Sí, link incluido
2. ¿Se probó el endpoint manualmente? → Sí, probado con curl
3. ¿Se considera la topología de red? → Sí, usa docker exec si es necesario
4. ¿Hay timeout adecuado? → Sí, 5 segundos
5. ¿Se maneja el error correctamente? → Sí, try-except con logging
```

---

## 🔗 Anti-Patterns a Evitar

### ❌ Anti-Pattern 1: Asumir Convención Estándar

```python
# ❌ MAL - Asume que todos los servicios usan /health
def verify_service(service_url: str) -> bool:
    response = requests.get(f"{service_url}/health")
    return response.status_code == 200
# Esto falla para: Qdrant (/readyz), Redis (PING), gRPC (diferente)
```

**Problema**: Cada servicio puede tener su propia convención. No existe "estándar universal".

### ❌ Anti-Pattern 2: No Considerar Topología de Red

```python
# ❌ MAL - Intenta acceso directo desde host a servicio en Docker
QDRANT_URL = "http://localhost:6333"  # No expuesto al host
response = requests.get(f"{QDRANT_URL}/readyz")
# ConnectionRefused porque puerto no está mapeado
```

**Problema**: Los servicios en redes Docker internas no son accesibles desde el host excepto si están en `ports:` del compose.

### ❌ Anti-Pattern 3: Sin Testing en Ambiente Real

```python
# ❌ MAL - Código escrito sin probar contra Qdrant real
# Documentación dice /health existe, pero no fue verificado
def verify_qdrant():
    return requests.get("http://qdrant:6333/health").status_code == 200
# Falla en producción porque endpoint no existe
```

**Problema**: Las asunciones no se validan hasta que se ejecutan en un ambiente real.

### ✓ Solución Correcta

```python
# ✓ BIEN - Considerando topología y endpoint correcto
def verify_qdrant_from_host(docker_container: str = "api") -> bool:
    """
    Verifica Qdrant usando docker exec.
    Usa endpoint correcto (/readyz) según documentación oficial.
    """
    try:
        cmd = ["docker", "exec", docker_container, "curl", "-s", "http://qdrant:6333/readyz"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and "ready" in result.stdout.lower()
    except Exception:
        return False
```

---

## 💡 Best Practices

### BP1: Documentar Endpoint y Versión

```python
# ✓ PATRÓN RECOMENDADO
class QdrantHealthCheck:
    """
    Verifica salud de Qdrant.
    
    Endpoint: /readyz (Kubernetes-style readiness check)
    Docs: https://qdrant.tech/documentation/
    Versions: Tested with qdrant:latest (v1.7+)
    Note: /health endpoint DOES NOT EXIST (returns 404)
    """
    
    QDRANT_HEALTH_ENDPOINT = "/readyz"
    QDRANT_LIVENESS_ENDPOINT = "/livez"
    # NOT /health - esto retorna 404
```

Ventajas:
- Documentación inline evita confusión
- Link a documentación oficial
- Nota explícita sobre endpoint que NO existe
- Versiones soportadas

### BP2: Crear Función Centralizada para Topología Docker

```python
# ✓ PATRÓN RECOMENDADO
def docker_exec_curl(container: str, url: str, timeout: int = 5) -> Tuple[bool, int, str]:
    """
    Ejecuta curl dentro de un contenedor Docker.
    
    Esto es necesario porque:
    - Servicios en redes Docker internas no son accesibles desde host
    - Desde dentro de Docker network, se usa hostname (ej: "qdrant")
    - Desde host, solo acceso a puertos mapeados
    
    Args:
        container: Nombre del contenedor desde donde ejecutar (ej: "api")
        url: URL completa (ej: "http://qdrant:6333/readyz")
        timeout: Timeout en segundos
    
    Returns:
        (success, status_code, content)
    """
    # ... implementación
```

Ventajas:
- Reutilizable para múltiples servicios
- Documentación clara de por qué es necesario
- Manejo consistente de errores

### BP3: Versión y Changelog Mapping

```python
# ✓ PATRÓN RECOMENDADO - Mapear cambios de API por versión
QDRANT_ENDPOINTS = {
    "0.11": {
        "health": "/health",
        "readiness": "/health",
        "liveness": "/health",
    },
    "1.0+": {
        "health": None,  # REMOVED
        "readiness": "/readyz",  # NEW
        "liveness": "/livez",    # NEW
    }
}

def get_health_endpoint(version: str) -> str:
    """Obtiene endpoint correcto según versión."""
    if version.startswith("0."):
        return QDRANT_ENDPOINTS["0.11"]["health"]
    else:
        return QDRANT_ENDPOINTS["1.0+"]["readiness"]
```

Ventajas:
- Soporta múltiples versiones
- Documentación de cambios de API
- Fácil de mantener cuando cambian versiones

---

## 📈 Impacto de la Solución

| Métrica | Antes | Después |
|---------|-------|---------|
| Verificación Qdrant Health | ✗ FAIL (404) | ✓ PASS |
| Acceso a Servicios Docker | ❌ Timeout | ✓ docker exec |
| Conocimiento de Endpoints | Asunción | Documentado |
| Reusabilidad del Código | Específico | Genérico |
| Mantenibilidad Futura | Frágil | Robusto |

---

## 🧪 Tests Relacionados

### Test File: `tests/test_qdrant_verification.py`

```python
#!/usr/bin/env python3
"""
Tests para verificación de Qdrant
Ejecutar: pytest tests/test_qdrant_verification.py -v
"""

import pytest
from scripts.verify_state import StateVerifier
import subprocess

class TestQdrantVerification:
    """Suite de tests para Qdrant."""
    
    def test_qdrant_readyz_endpoint_exists(self):
        """Verifica que /readyz endpoint existe y responde."""
        try:
            result = subprocess.run(
                ["docker", "exec", "api", "curl", "-s", "http://qdrant:6333/readyz"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, "Qdrant /readyz endpoint should exist"
            assert "ready" in result.stdout.lower(), "Should contain 'ready' in response"
        except subprocess.TimeoutExpired:
            pytest.skip("Qdrant not running")
    
    def test_qdrant_health_endpoint_returns_404(self):
        """Verifica que /health endpoint retorna 404 (no existe)."""
        try:
            result = subprocess.run(
                ["docker", "exec", "api", "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://qdrant:6333/health"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.stdout.strip() == "404", "/health should return 404 in Qdrant"
        except subprocess.TimeoutExpired:
            pytest.skip("Qdrant not running")
    
    def test_docker_exec_curl_helper(self):
        """Verifica que helper de docker exec funciona."""
        verifier = StateVerifier()
        success, status_code, content = verifier._docker_exec_curl("http://qdrant:6333/readyz")
        
        if success:
            assert status_code == 200, "Should get 200 from /readyz"
            assert "ready" in content.lower(), "Response should mention ready"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-01-DOCKER-NETWORKING.md` (Topología Docker)
- Ver: `scripts/verify_state.py` (Implementación de la solución)
- Ver: `docs/state_management.md` (Documentación de SP10)
- Código: `services/api/app/routes/metrics.py` (Integración de endpoints)
- Qdrant Docs: https://qdrant.tech/documentation/

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - Qdrant health endpoint discovery |

---

## ✨ Key Takeaway

> **"No asumas convenciones estándar - consulta la documentación y prueba en ambiente real. Diferentes servicios usan diferentes endpoints de health (/health, /readyz, /livez, PING)."**

```python
# Patrón ganador: Documentar endpoint específico + docker-aware checker
SERVICE_ENDPOINTS = {
    "qdrant": {
        "endpoint": "/readyz",           # NO /health
        "docs": "https://qdrant.tech",
        "access": "via docker exec"      # No accesible directo desde host
    },
    "redis": {
        "endpoint": "PING",
        "docs": "https://redis.io",
        "access": "via docker exec"
    },
    "api": {
        "endpoint": "/health",
        "docs": "custom",
        "access": "localhost:8001"       # Mapeado al host
    }
}

def verify_service(config: dict) -> bool:
    """Verifica usando endpoint documentado."""
    endpoint = config["endpoint"]
    # Usar docker exec si está en "via docker exec"
```

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Qdrant API Documentation](https://qdrant.tech/documentation/api-reference/)
- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [REST API Health Check Conventions](https://tools.ietf.org/html/draft-inadarei-api-health-check-01)

### Ejemplos en el Proyecto
- `scripts/verify_state.py` - Implementación final
- `scripts/diagnose-qdrant.sh` - Script de diagnóstico
- `deploy/compose/docker-compose.yml` - Configuración de servicios

### Referencias Externas
- [HTTP Status Codes](https://httpwg.org/specs/rfc7231.html#status.codes) - 404 Not Found
- [Docker Networking Guide](https://docs.docker.com/network/) - Topología de redes

---

## ❓ FAQ

### P: ¿Por qué Qdrant usa /readyz y no /health?

R: Qdrant sigue la convención de Kubernetes para health checks, que distingue entre readiness (/readyz) y liveness (/livez). Esto permite mayor granularidad en orchestración.

### P: ¿Puedo exponer Qdrant al host para acceder directo?

R: Sí, agregando `ports:` en docker-compose.yml. Pero para verificadores internos que se ejecutan en el host, es mejor usar `docker exec` para evitar complejidad de mapeos.

### P: ¿Y si cambio de versión de Qdrant?

R: Revisa el changelog. Las versiones 1.0+ usan /readyz. Si usas versiones viejas, verifica su API específica y documéntalo.

### P: ¿Cómo valido que funcionó la solución?

R: Ejecuta `python scripts/verify_state.py` y verifica que todos los checks pasen, especialmente "✓ PASS: Qdrant Health".

---

## 🎓 Lecciones Relacionadas

- **Lección 1**: Docker Networking - Topología de redes y conectividad
- **Lección 2**: Router Integration - Cómo integrar endpoints en FastAPI
- **Lección 10** (próxima): Internal Service Discovery - Cómo descubrir servicios disponibles

---