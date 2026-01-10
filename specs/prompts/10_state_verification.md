# 🔹 PROMPT EJECUTABLE 10 — Gestión de Estado y Verificación

> **Subproyecto**: 10 de 10  
> **Objetivo**: Crear verificador de estructura, invariantes y prevención de deriva  
> **Prerequisitos**: Subproyectos 1-9 completados

---

## ROL DEL MODELO

Actúa como **auditor técnico de continuidad**:
- Crear documentación y un script verificador SOLO LECTURA
- No modificar archivos del proyecto
- Definir invariantes y chequeos para detectar inconsistencias

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- El proyecto se ejecuta por subproyectos, y se debe evitar degradación progresiva.
- Existen invariantes: layout repo, nombres docker services, llaves YAML, contrato `/query`, prefijos Redis, colección por RAG.
- Operación: reproducible, auditable, sin asumir memoria previa.

---

## OBJETIVO

Crear un "paquete" de verificación:
- Checklist operacional
- Script de verificación (solo lectura) que valide estructura y archivos esperados

**Éxito binario**: un comando (humano) produce salida `STATE_OK` o `STATE_FAIL` con lista de diferencias.

---

## ARCHIVOS A CREAR

```
docs/state_management.md
scripts/state_expected.json
scripts/verify_state.py
```

---

## CONTENIDO OBLIGATORIO

### `scripts/state_expected.json`

Debe listar todos los invariantes del proyecto:

```json
{
  "version": "1.0.0",
  "description": "Invariantes del proyecto RAG On-Premise",
  
  "required_paths": [
    "README.md",
    ".env.example",
    ".gitignore",
    "docs/architecture.md",
    "docs/operations.md",
    "docs/security.md",
    "docs/configuration.md",
    "docs/qdrant.md",
    "docs/redis.md",
    "docs/llm.md",
    "docs/observability.md",
    "deploy/compose/docker-compose.yml",
    "deploy/nginx/nginx.conf",
    "deploy/nginx/README.md",
    "configs/client/client.yaml.example",
    "configs/rags/example_rag.yaml",
    "configs/rags/prompts/system_default.txt",
    "configs/rags/prompts/user_default.txt",
    "data/sources/.gitkeep",
    "data/backups/.gitkeep",
    "services/api/app/main.py",
    "services/api/app/models.py",
    "services/api/app/routes/health.py",
    "services/api/app/routes/query.py",
    "services/api/app/routes/metrics.py",
    "services/api/app/qdrant_client.py",
    "services/api/app/retrieval.py",
    "services/api/app/redis_client.py",
    "services/api/app/cache.py",
    "services/api/app/sessions.py",
    "services/api/app/rate_limit.py",
    "services/api/app/llm/openrouter_client.py",
    "services/api/app/prompting.py",
    "services/api/app/observability.py",
    "services/api/Dockerfile",
    "services/api/requirements.txt",
    "services/api/README.md",
    "services/ingest/cli.py",
    "services/ingest/worker.py",
    "services/ingest/app.py",
    "services/ingest/cli.md",
    "services/ingest/queue_contract.md",
    "services/ingest/README.md",
    "scripts/verify_state.py",
    "scripts/state_expected.json"
  ],
  
  "required_directories": [
    "docs",
    "deploy/compose",
    "deploy/nginx",
    "configs/client",
    "configs/rags",
    "configs/rags/prompts",
    "data/sources",
    "data/backups",
    "services/api/app",
    "services/api/app/routes",
    "services/api/app/llm",
    "services/ingest",
    "scripts"
  ],
  
  "docker_invariants": {
    "services": [
      "api",
      "qdrant",
      "redis",
      "nginx",
      "ingest-worker"
    ],
    "networks": [
      "rag_network"
    ],
    "volumes": [
      "qdrant_data",
      "redis_data"
    ]
  },
  
  "api_invariants": {
    "endpoints": [
      "GET /health",
      "POST /query",
      "GET /metrics"
    ],
    "query_request_fields": [
      "rag_id",
      "question",
      "session_id",
      "top_k"
    ],
    "query_response_fields": [
      "rag_id",
      "answer",
      "context_chunks",
      "latency_ms",
      "cache_hit",
      "session_id"
    ]
  },
  
  "config_invariants": {
    "client_yaml_keys": [
      "app",
      "qdrant",
      "redis",
      "llm",
      "paths",
      "concurrency",
      "security",
      "cache",
      "sessions"
    ],
    "rag_yaml_keys": [
      "rag_id",
      "collection_name",
      "embeddings",
      "chunking",
      "retrieval",
      "prompting",
      "rate_limit",
      "errors",
      "cache",
      "sessions"
    ]
  },
  
  "redis_invariants": {
    "key_prefixes": [
      "rag:ingest:queue",
      "rag:job:",
      "rag:cache:",
      "rag:session:",
      "rag:ratelimit:"
    ]
  }
}
```

---

### `scripts/verify_state.py`

Script verificador de solo lectura:

```python
#!/usr/bin/env python3
"""
Verificador de estado del proyecto RAG On-Premise.

Este script valida que el proyecto cumple con todos los invariantes
definidos en state_expected.json.

USO:
    python scripts/verify_state.py

SALIDA:
    STATE_OK - si todo cumple
    STATE_FAIL - si hay incumplimientos (con lista detallada)

NOTA: Este script es SOLO LECTURA. No modifica ningún archivo.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Determinar raíz del proyecto
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATE_FILE = SCRIPT_DIR / "state_expected.json"


def load_state_expected() -> dict:
    """Carga el archivo de invariantes esperados."""
    if not STATE_FILE.exists():
        print(f"ERROR: No se encontró {STATE_FILE}")
        sys.exit(1)
    
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_required_paths(expected: List[str]) -> Tuple[List[str], List[str]]:
    """Verifica existencia de archivos requeridos."""
    found = []
    missing = []
    
    for path in expected:
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            found.append(path)
        else:
            missing.append(path)
    
    return found, missing


def check_required_directories(expected: List[str]) -> Tuple[List[str], List[str]]:
    """Verifica existencia de directorios requeridos."""
    found = []
    missing = []
    
    for path in expected:
        full_path = PROJECT_ROOT / path
        if full_path.is_dir():
            found.append(path)
        else:
            missing.append(path)
    
    return found, missing


def check_docker_compose(invariants: dict) -> Tuple[List[str], List[str]]:
    """Verifica que docker-compose contiene los servicios esperados."""
    docker_compose_path = PROJECT_ROOT / "deploy" / "compose" / "docker-compose.yml"
    
    if not docker_compose_path.exists():
        return [], ["docker-compose.yml no existe"]
    
    found = []
    missing = []
    
    with open(docker_compose_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar servicios (búsqueda simple de texto)
    for service in invariants.get("services", []):
        # Buscar patrón "service_name:" como definición de servicio
        if f"{service}:" in content:
            found.append(f"service:{service}")
        else:
            missing.append(f"service:{service}")
    
    # Verificar networks
    for network in invariants.get("networks", []):
        if network in content:
            found.append(f"network:{network}")
        else:
            missing.append(f"network:{network}")
    
    # Verificar volumes
    for volume in invariants.get("volumes", []):
        if volume in content:
            found.append(f"volume:{volume}")
        else:
            missing.append(f"volume:{volume}")
    
    return found, missing


def check_docs_exist(required_docs: List[str]) -> Tuple[List[str], List[str]]:
    """Verifica que los documentos críticos existen."""
    found = []
    missing = []
    
    for doc in required_docs:
        if doc.startswith("docs/"):
            full_path = PROJECT_ROOT / doc
            if full_path.exists():
                found.append(doc)
            else:
                missing.append(doc)
    
    return found, missing


def print_results(title: str, found: List[str], missing: List[str]):
    """Imprime resultados de una verificación."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"✅ Encontrados: {len(found)}")
    print(f"❌ Faltantes: {len(missing)}")
    
    if missing:
        print("\nFaltantes:")
        for item in missing:
            print(f"  - {item}")


def main():
    """Ejecuta todas las verificaciones."""
    print("🔍 VERIFICADOR DE ESTADO - RAG On-Premise")
    print("=" * 60)
    print(f"Raíz del proyecto: {PROJECT_ROOT}")
    print(f"Archivo de invariantes: {STATE_FILE}")
    
    # Cargar invariantes
    state = load_state_expected()
    print(f"\nVersión de invariantes: {state.get('version', 'unknown')}")
    
    all_missing = []
    
    # 1. Verificar archivos requeridos
    found, missing = check_required_paths(state.get("required_paths", []))
    print_results("ARCHIVOS REQUERIDOS", found, missing)
    all_missing.extend([f"file:{m}" for m in missing])
    
    # 2. Verificar directorios requeridos
    found, missing = check_required_directories(state.get("required_directories", []))
    print_results("DIRECTORIOS REQUERIDOS", found, missing)
    all_missing.extend([f"dir:{m}" for m in missing])
    
    # 3. Verificar docker-compose
    found, missing = check_docker_compose(state.get("docker_invariants", {}))
    print_results("DOCKER COMPOSE", found, missing)
    all_missing.extend([f"docker:{m}" for m in missing])
    
    # 4. Verificar docs críticos
    critical_docs = [
        "docs/configuration.md",
        "docs/architecture.md",
        "docs/operations.md"
    ]
    found, missing = check_docs_exist(critical_docs)
    print_results("DOCUMENTACIÓN CRÍTICA", found, missing)
    all_missing.extend([f"doc:{m}" for m in missing])
    
    # Resultado final
    print("\n" + "=" * 60)
    if not all_missing:
        print("🎉 STATE_OK")
        print("Todos los invariantes se cumplen.")
        print("=" * 60)
        return 0
    else:
        print("❌ STATE_FAIL")
        print(f"Total de incumplimientos: {len(all_missing)}")
        print("=" * 60)
        print("\nResumen de faltantes:")
        for item in all_missing:
            print(f"  - {item}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

### `docs/state_management.md`

```markdown
# Gestión de Estado del Proyecto

## Propósito

Este documento define cómo mantener la consistencia del proyecto a través de múltiples iteraciones de desarrollo.

## Invariantes del Sistema

Los siguientes elementos están **congelados** y no deben modificarse sin actualizar el verificador:

### Estructura de Repositorio

| Directorio | Propósito |
|------------|-----------|
| `docs/` | Documentación operativa |
| `deploy/compose/` | Docker Compose |
| `deploy/nginx/` | Configuración Nginx |
| `configs/client/` | Config global |
| `configs/rags/` | Config por RAG |
| `data/sources/` | Fuentes de documentos |
| `services/api/` | API FastAPI |
| `services/ingest/` | CLI y Worker |
| `scripts/` | Scripts operativos |

### Nombres de Servicios Docker

| Servicio | Descripción |
|----------|-------------|
| `api` | FastAPI |
| `qdrant` | Vector DB |
| `redis` | Cache/Queue |
| `nginx` | Reverse proxy |
| `ingest-worker` | Procesador |

### Contrato API `/query`

Request:
- `rag_id` (string, requerido)
- `question` (string, requerido)
- `session_id` (string, opcional)
- `top_k` (int, opcional)

Response:
- `rag_id`
- `answer`
- `context_chunks`
- `latency_ms`
- `cache_hit`
- `session_id`

### Prefijos Redis

| Prefijo | Uso |
|---------|-----|
| `rag:ingest:queue` | Cola de ingestión |
| `rag:job:*` | Estado de jobs |
| `rag:cache:*` | Caché de respuestas |
| `rag:session:*` | Sesiones de usuario |
| `rag:ratelimit:*` | Rate limiting |

## Verificación de Estado

### Ejecutar Verificador

```bash
python scripts/verify_state.py
```

### Interpretar Resultados

- `STATE_OK`: Todo cumple con los invariantes
- `STATE_FAIL`: Hay incumplimientos que deben corregirse

### Qué Hacer si STATE_FAIL

1. Revisar la lista de faltantes
2. Crear/restaurar archivos faltantes
3. Verificar que docker-compose tiene todos los servicios
4. Re-ejecutar el verificador hasta obtener STATE_OK

## Checklist Operacional

Antes de cualquier cambio mayor, verificar:

- [ ] `python scripts/verify_state.py` devuelve STATE_OK
- [ ] `docker compose config` no arroja errores
- [ ] Todos los tests pasan (cuando existan)
- [ ] La documentación está actualizada

## Evolución de Invariantes

Si es necesario cambiar un invariante:

1. Documentar la razón del cambio
2. Actualizar `scripts/state_expected.json`
3. Actualizar este documento
4. Notificar al equipo
5. Ejecutar verificador para confirmar coherencia
```

---

## VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# Ejecutar el verificador
python scripts/verify_state.py

# Resultado esperado (si todo está completo):
# STATE_OK

# Si hay faltantes:
# STATE_FAIL + lista de incumplimientos
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `python scripts/verify_state.py` ejecuta sin errores de sintaxis
- [ ] El script imprime `STATE_OK` cuando todo está correcto
- [ ] El script imprime `STATE_FAIL` + lista cuando hay faltantes

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| FileNotFoundError | state_expected.json no existe | Crear el archivo primero |
| SyntaxError en JSON | JSON mal formado | Validar JSON con herramienta externa |
| Falsos negativos | Path incorrecto | Verificar que PROJECT_ROOT apunta a la raíz |

---

## LO QUE SE CONGELA

✅ Lista de invariantes del proyecto  
✅ Script verificador como "puerta" antes de cambios  
✅ Proceso de validación documentado

---

## LO QUE SE HABILITA

➡️ Evolución futura del proyecto con control de trazabilidad  
➡️ UI Vue más completa  
➡️ Autenticación  
➡️ TLS real  
➡️ Mejoras de procesamiento PDF  

Todo esto sin perder control ni consistencia del sistema base.