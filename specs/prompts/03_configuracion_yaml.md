# 🔧 PROMPT EJECUTABLE #03 — Esquema de Configuración (YAML/ENV)

> **Subproyecto 3 de 10**  
> **Objetivo**: Definir formato y ejemplos de configuración declarativa para cliente y RAGs

---

## ROL (modelo ligero)

Actúa como editor mecánico. Tu única tarea es:
- Crear YAMLs de ejemplo y documentación sin cambiar llaves ni nombres.
- No razonar arquitectura. No optimizar. No añadir campos no solicitados.

---

## ⚠️ REGLA CRÍTICA

```
El modelo NO debe ejecutar comandos.
El humano ejecutará los comandos manualmente.
```

---

## 📁 ARCHIVOS A CREAR

| Archivo | Descripción |
|---------|-------------|
| `configs/client/client.yaml.example` | Configuración global del cliente |
| `configs/rags/example_rag.yaml` | Ejemplo de configuración por RAG |
| `docs/configuration.md` | Documentación de todos los campos |

---

## 📄 CONTENIDO OBLIGATORIO

### 1. `configs/client/client.yaml.example`

Debe incluir las siguientes secciones y campos:

```yaml
# Configuración global del cliente RAG On-Premise
# Copiar a client.yaml y ajustar valores

app:
  host: "0.0.0.0"
  port: 8000
  log_level: "info"  # debug, info, warning, error

qdrant:
  url: "http://qdrant:6333"
  api_key: ""  # opcional, dejar vacío si no se usa

redis:
  url: "redis://redis:6379/0"

llm:
  provider: "openrouter"
  api_key_env_var: "OPENROUTER_API_KEY"
  default_model: "openai/gpt-3.5-turbo"
  fallback_model: "anthropic/claude-instant-v1"
  timeout_s: 30
  max_retries: 2

paths:
  sources_root: "/app/data/sources"
  rags_config_dir: "/app/configs/rags"

concurrency:
  global_max_inflight_requests: 100
  global_rate_limit: 50  # requests por segundo

security:
  behind_nginx: true
  trusted_proxies:
    - "172.16.0.0/12"
    - "192.168.0.0/16"

cache:
  enabled: true
  ttl_seconds: 300

sessions:
  enabled: true
  ttl_seconds: 1800
```

---

### 2. `configs/rags/example_rag.yaml`

Debe incluir:

```yaml
# Configuración específica para un RAG
# Un archivo por cada RAG del sistema

rag_id: "example_rag"
collection_name: "example_rag_collection"

embeddings:
  model_name: "text-embedding-ada-002"  # o modelo local
  dim: 1536  # dimensión del vector
  batch_size: 100

chunking:
  splitter: "recursive"  # recursive, character, token
  chunk_size: 500
  chunk_overlap: 50

retrieval:
  top_k: 5
  score_threshold: 0.7  # opcional, filtrar por score mínimo
  max_context_chunks: 10

prompting:
  system_template_path: "prompts/system_default.txt"
  user_template_path: "prompts/user_default.txt"
  max_tokens: 1024
  temperature: 0.7

rate_limit:
  rps: 10  # requests por segundo para este RAG
  burst: 20

errors:
  no_context_message: "No encontré información relevante para responder tu pregunta."
  provider_error_message: "El servicio está temporalmente no disponible. Intenta de nuevo."

cache:
  enabled: true
  ttl_seconds: 600

sessions:
  history_turns: 5  # turnos de conversación a mantener
  ttl_seconds: 1800
```

---

### 3. `docs/configuration.md`

Debe incluir:

#### Encabezado
```markdown
# Configuración del Sistema RAG

Este documento describe todos los campos de configuración disponibles.
```

#### Tabla de campos para client.yaml

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `app.host` | string | sí | "0.0.0.0" | Host de la API |
| `app.port` | int | sí | 8000 | Puerto de la API |
| `app.log_level` | string | no | "info" | Nivel de logging |
| `qdrant.url` | string | sí | - | URL de Qdrant |
| `qdrant.api_key` | string | no | "" | API key de Qdrant |
| `redis.url` | string | sí | - | URL de Redis |
| `llm.provider` | string | sí | "openrouter" | Proveedor LLM |
| `llm.api_key_env_var` | string | sí | - | Variable de entorno con API key |
| `llm.default_model` | string | sí | - | Modelo principal |
| `llm.fallback_model` | string | sí | - | Modelo de respaldo |
| `llm.timeout_s` | int | no | 30 | Timeout en segundos |
| `llm.max_retries` | int | no | 2 | Reintentos máximos |
| `paths.sources_root` | string | sí | - | Ruta raíz de fuentes |
| `paths.rags_config_dir` | string | sí | - | Directorio de configs RAG |
| `concurrency.global_max_inflight_requests` | int | no | 100 | Máximo de requests simultáneos |
| `concurrency.global_rate_limit` | int | no | 50 | Rate limit global (rps) |
| `cache.enabled` | bool | no | true | Activar caché |
| `cache.ttl_seconds` | int | no | 300 | TTL del caché |
| `sessions.enabled` | bool | no | true | Activar sesiones |
| `sessions.ttl_seconds` | int | no | 1800 | TTL de sesiones |

#### Tabla de campos para <rag_id>.yaml

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `rag_id` | string | sí | - | Identificador único del RAG |
| `collection_name` | string | sí | - | Nombre de colección en Qdrant |
| `embeddings.model_name` | string | sí | - | Modelo de embeddings |
| `embeddings.dim` | int | sí | - | Dimensión de vectores |
| `embeddings.batch_size` | int | no | 100 | Tamaño de batch |
| `chunking.splitter` | string | no | "recursive" | Tipo de splitter |
| `chunking.chunk_size` | int | no | 500 | Tamaño de chunks |
| `chunking.chunk_overlap` | int | no | 50 | Overlap entre chunks |
| `retrieval.top_k` | int | no | 5 | Chunks a recuperar |
| `retrieval.score_threshold` | float | no | null | Score mínimo |
| `retrieval.max_context_chunks` | int | no | 10 | Máximo chunks en contexto |
| `prompting.system_template_path` | string | sí | - | Ruta template sistema |
| `prompting.user_template_path` | string | sí | - | Ruta template usuario |
| `prompting.max_tokens` | int | no | 1024 | Tokens máximos respuesta |
| `prompting.temperature` | float | no | 0.7 | Temperatura del modelo |
| `rate_limit.rps` | int | no | 10 | Requests por segundo |
| `rate_limit.burst` | int | no | 20 | Burst permitido |

#### Sección de reglas

```markdown
## Reglas de Configuración

1. **Un RAG = Una Colección**: Cada `rag_id` debe tener su propia `collection_name` en Qdrant.
2. **Override por RAG**: Los valores de `cache` y `sessions` en el RAG sobreescriben los globales.
3. **Variables de entorno**: Usar `api_key_env_var` para referenciar secrets, nunca hardcodear.
4. **Paths**: Las rutas de templates son relativas a `paths.rags_config_dir`.
```

---

## 🛑 PUNTO DE ESPERA

Después de crear los 3 archivos:

1. Detente completamente
2. Solicita confirmación humana de que:
   - Los YAML son sintácticamente válidos
   - Todos los campos requeridos están presentes
   - La documentación es coherente con los ejemplos

---

## ✅ CRITERIO DE ÉXITO

- [ ] `configs/client/client.yaml.example` existe y es YAML válido
- [ ] `configs/rags/example_rag.yaml` existe y es YAML válido  
- [ ] `docs/configuration.md` documenta todos los campos con tabla
- [ ] No hay mezcla de config global con config por RAG
- [ ] Los defaults están documentados

---

## 🔗 DEPENDENCIAS

| Requiere completado | Habilita |
|---------------------|----------|
| Subproyecto 1 (Layout) | Subproyecto 4 (CLI Ingestión) |
| Subproyecto 2 (Docker) | - |

---

## 📝 NOTAS

- La lógica de carga real de estos YAML se implementa en subproyectos posteriores
- Los campos deben ser explícitos, evitar "magic defaults" no documentados
- El esquema aquí definido queda **congelado** para los siguientes subproyectos