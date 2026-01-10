# Lecciones Aprendidas 01 - Docker & Networking

## 🎯 Problema Identificado

**Error en Subproyecto 9 (Observabilidad)**

Endpoint `/metrics` retornaba `404 Not Found` aunque estaba correctamente implementado en FastAPI.

```
curl http://localhost:8000/metrics
# HTTP/1.1 404 Not Found
# {"detail":"Not Found"}
```

---

## 🔍 Causa Raíz

**Análisis**:

1. **Contenedor API corriendo pero puerto no expuesto**
   - `docker-compose.yml` usaba `expose: "8000"` 
   - `expose` solo abre puertos entre contenedores, NO al host
   
2. **Sin mapeo host:container**
   ```yaml
   api:
     expose:
       - "8000"  # ❌ Solo interno a docker network
   ```

3. **Nginx como intermediario adicional**
   - Nginx escuchaba en puerto 80
   - Rutas solo mapeaban `/api/*` y `/health`
   - El endpoint `/metrics` no estaba en nginx.conf
   - Cliente intentaba `localhost:8000` → no accesible desde host

4. **Falta de claridad sobre topología**
   ```
   Host Machine
      ↓
   localhost:8000 (¿?? → NO ACCESIBLE)
      
   Docker Network (interno)
      ↓
   API Container:8000 ✓
      ↓
   Nginx:80 → remapea /api/* pero no /metrics
   ```

---

## ✅ Solución Implementada

### Paso 1: Mapear Puerto Correctamente

```yaml
api:
  ports:
    - "8001:8000"  # ✅ host:container mapping
  networks:
    - rag_network
```

**Por qué 8001 en lugar de 8000**:
- Puerto 8000 ya estaba en uso en el host
- Flexible para futuros servicios

### Paso 2: Actualizar Script de Validación

```python
class ValidatorSP9:
    def __init__(self, base_url: str = "http://localhost:8001"):  # ✅ Usar puerto mapeado
        self.base_url = base_url
        ...
```

### Paso 3: Verificación

```bash
# ✅ Ahora funciona
curl http://localhost:8001/metrics
# {"requests_total": 7, ...}
```

---

## 🛡️ Principio Preventivo Clave

### P1: Topología Explícita de Red

**Siempre documentar la topología de red**:

```
┌─────────────────────────────────────────┐
│ HOST MACHINE (Windows)                  │
├─────────────────────────────────────────┤
│                                         │
│  Port 8001 (Public)                    │
│     ↓                                   │
│  ┌─────────────────────────────────┐   │
│  │ Docker Desktop Network Bridge   │   │
│  │                                 │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │ API Container             │  │   │
│  │  │ - Port 8000 (Internal)    │  │   │
│  │  │ - /query ✓                │  │   │
│  │  │ - /metrics ✓              │  │   │
│  │  └───────────────────────────┘  │   │
│  │                                 │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │ Nginx (Port 80)           │  │   │
│  │  │ - /api/* → API:8000       │  │   │
│  │  │ - /health → API:8000      │  │   │
│  │  └───────────────────────────┘  │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### P2: Diferencia entre `expose` vs `ports`

| Propiedad | Alcance | Uso |
|-----------|---------|-----|
| `expose` | Docker network interno | Comunicación inter-contenedor |
| `ports` | Host machine | Acceso desde afuera del contenedor |

```yaml
# ❌ INCORRECTO para acceso desde host
services:
  api:
    expose:
      - "8000"

# ✅ CORRECTO para acceso desde host
services:
  api:
    ports:
      - "8001:8000"
```

### P3: Puerto en Uso - Diagnosticar Rápido

```bash
# Windows/PowerShell
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill process (Linux)
kill -9 <PID>

# Kill process (Windows - usar taskkill correctamente)
taskkill /PID <PID> /F
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: `404 Not Found` pero endpoint existe

```python
# Checklist:
1. ✓ Endpoint definido en FastAPI router?
2. ✓ Router incluido en main.py?
3. ✓ ¿Firewall bloqueando puerto?
4. ⚠️ ¿Puerto mapeado en docker-compose? (AQUÍ ESTABA EL ERROR)
5. ✓ ¿Endpoint expuesto en nginx/proxy?
```

### Señal 2: Conexión rechazada (`Connection refused`)

```
curl: (7) Failed to connect to localhost port 8000: Connection refused

Esto significa:
- Puerto NO está siendo escuchado
- O puerto está expuesto pero no mapeado al host
```

### Señal 3: Timeout en docker-compose logs

```bash
docker compose logs api
# Si ves "INFO: Uvicorn running" pero no puedes conectar
# → Problema de networking, revisar ports vs expose
```

---

## 💻 Código Reutilizable - Diagnosticar Puertos

### Script: `scripts/diagnose-ports.sh`

```bash
#!/bin/bash

# Diagnóstico automático de puertos y networking
# Uso: bash scripts/diagnose-ports.sh

COLORS='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'

echo -e "${BLUE}═══════════════════════════════════════${COLORS}"
echo -e "${BLUE}Diagnóstico de Puertos y Networking${COLORS}"
echo -e "${BLUE}═══════════════════════════════════════${COLORS}\n"

# Función para verificar puerto
check_port() {
    local port=$1
    local service=$2
    
    echo -n "Verificando puerto $port ($service)... "
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓ ABIERTO${COLORS}"
        return 0
    else
        echo -e "${RED}✗ CERRADO${COLORS}"
        return 1
    fi
}

# Función para listar procesos en puerto
list_port_usage() {
    local port=$1
    
    echo -e "\n${YELLOW}Procesos usando puerto $port:${COLORS}"
    
    if command -v netstat &> /dev/null; then
        netstat -ano | grep ":$port"
    elif command -v lsof &> /dev/null; then
        lsof -i :$port
    else
        echo "netstat o lsof no disponibles"
    fi
}

# Función para verificar docker-compose
check_docker_config() {
    echo -e "\n${YELLOW}Configuración Docker-Compose:${COLORS}"
    
    if [ -f "deploy/compose/docker-compose.yml" ]; then
        grep -A5 "ports:" deploy/compose/docker-compose.yml | head -20
    else
        echo -e "${RED}docker-compose.yml no encontrado${COLORS}"
    fi
}

# Función para verificar servicios corriendo
check_docker_services() {
    echo -e "\n${YELLOW}Servicios Docker Corriendo:${COLORS}"
    
    if docker ps 2>/dev/null; then
        docker ps --format "table {{.Names}}\t{{.Ports}}"
    else
        echo -e "${RED}Docker no disponible${COLORS}"
    fi
}

# Main
check_port 8000 "API (directo)"
check_port 8001 "API (mapeado)"
check_port 8080 "Nginx"
check_port 6333 "Qdrant"
check_port 6379 "Redis"

list_port_usage 8000
check_docker_config
check_docker_services

echo -e "\n${BLUE}═══════════════════════════════════════${COLORS}"
echo -e "${BLUE}Diagnóstico completado${COLORS}"
echo -e "${BLUE}═══════════════════════════════════════${COLORS}\n"
```

### Script Python: `scripts/validate-ports.py`

```python
#!/usr/bin/env python3
"""
Validación automática de puertos y networking.
Uso: python scripts/validate-ports.py
"""

import socket
import sys
from typing import Tuple

class PortValidator:
    """Validador de puertos y conectividad."""
    
    def __init__(self):
        self.results = []
        self.port_map = {
            8001: ("API", "FastAPI"),
            8000: ("API (Docker)", "FastAPI interno"),
            8080: ("Nginx", "Reverse proxy"),
            6333: ("Qdrant", "Vector DB"),
            6379: ("Redis", "Cache/Queue"),
        }
    
    def check_port(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Verificar si puerto está abierto."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"Error al verificar {host}:{port}: {e}")
            return False
    
    def validate_all(self, host: str = "localhost") -> bool:
        """Validar todos los puertos."""
        print("=" * 60)
        print("VALIDACIÓN DE PUERTOS Y NETWORKING")
        print("=" * 60)
        
        all_ok = True
        
        for port, (service, description) in self.port_map.items():
            status = self.check_port(host, port)
            symbol = "✓" if status else "✗"
            status_text = "ABIERTO" if status else "CERRADO"
            
            print(f"{symbol} {service:20} ({port:5}): {status_text}")
            print(f"  → {description}")
            
            if not status:
                all_ok = False
        
        print("\n" + "=" * 60)
        
        if all_ok:
            print("✓ Todos los puertos están disponibles")
            return True
        else:
            print("✗ Algunos puertos no están disponibles")
            print("\nTroubleshooting:")
            print("1. docker compose -f deploy/compose/docker-compose.yml up -d")
            print("2. sleep 10")
            print("3. python scripts/validate-ports.py")
            return False
        
        return all_ok

if __name__ == "__main__":
    validator = PortValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)
```

---

## 📋 Checklist de Implementación

### Antes de desplegar un servicio nuevo

- [ ] Identificar todos los puertos necesarios
- [ ] Documentar topología de red en diagrama
- [ ] En docker-compose: usar `ports:` (NO `expose:`) para acceso host
- [ ] Probar conectividad: `curl localhost:PUERTO`
- [ ] Verificar nginx/proxy si lo usas: ¿está mapeando rutas?
- [ ] Ejecutar script de validación de puertos
- [ ] Documentar excepciones (ej: port 8001 en lugar de 8000)

### En desarrollo iterativo

```bash
# Ciclo típico
docker compose down
docker compose build api
docker compose up -d
sleep 10
python scripts/validate-ports.py
curl http://localhost:8001/metrics
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-02-ROUTER-INTEGRATION.md` (incluir routers en FastAPI)
- Ver: `LESSONS-LEARNED-03-THREAD-SAFETY.md` (métricas compartidas)
- Ver: `LESSONS-LEARNED-04-LLM-FALLBACK.md` (manejo de errores con fallback)

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - Docker networking |

---

## ✨ Key Takeaway

> **"No asumir que `expose` en docker-compose mapea puertos al host. Siempre usar `ports:` para acceso externo y documentar la topología de red explícitamente."**

```yaml
# Patrón seguro
services:
  api:
    build: ./services/api
    ports:
      - "${API_PORT_HOST}:${API_PORT_CONTAINER}"  # ✓ Uso variables de entorno
    environment:
      - API_PORT=${API_PORT_CONTAINER}
    networks:
      - rag_network
```

---