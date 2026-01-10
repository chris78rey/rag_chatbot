# PROMPT EJECUTABLE 01 - Layout Canónico del Repositorio

> **Subproyecto 1 de 10** | Scaffolding mínimo del repositorio RAG on-premise

---

## 🎯 OBJETIVO

Crear la estructura base de carpetas y archivos del repositorio para un producto RAG comercializable on-premise.

---

## 📋 INSTRUCCIONES PARA EL MODELO

### ROL (modelo ligero):
- Editor mecánico y preciso. No razonar arquitectura. No renombrar nada.
- Si un archivo ya existe, no lo edites salvo que se indique explícitamente.

### REGLA CRÍTICA:
> **El modelo NO debe ejecutar comandos.**  
> **El humano ejecutará los comandos manualmente.**

---

## 📁 PASOS A EJECUTAR

### 1) Crear estas carpetas (vacías si aplica):

```
docs/
deploy/compose/
deploy/nginx/
configs/client/
configs/rags/
data/sources/
data/backups/
services/api/
services/ingest/
scripts/
```

### 2) Crear archivos con contenido mínimo:

- `README.md`
- `docs/architecture.md`
- `docs/operations.md`
- `docs/security.md`
- `.env.example`
- `.gitignore`
- `data/sources/.gitkeep`
- `data/backups/.gitkeep`

---

## 📝 CONTENIDO DE CADA ARCHIVO

### README.md

```markdown
# RAG On-Premise (FastAPI + Qdrant + Redis)

## Propósito
Sistema RAG comercializable, 100% local, replicable por cliente mediante docker-compose aislado.

## Alcance MVP
- ~300 usuarios concurrentes
- Latencia baja
- Multi-RAG (colección por RAG en Qdrant)
- Sin interfaz administrativa avanzada
- Sin Kubernetes

## Componentes
- **FastAPI async**: Consultas en tiempo real
- **Qdrant**: Vector database
- **Redis**: Colas, caché, estado ligero
- **Nginx**: Reverse proxy con rate limiting
- **CLI de ingestión**: Procesamiento de documentos

## Flujo Alto Nivel
1. Documentos → CLI ingestión → Cola Redis → Worker → Qdrant
2. Usuario → Nginx → FastAPI → Qdrant + LLM → Respuesta

## Estructura del Repositorio
- `docs/` - Documentación operativa
- `deploy/` - Docker-compose y configuración Nginx
- `configs/` - Configuración por cliente y por RAG
- `data/` - Fuentes y backups
- `services/` - API y worker de ingestión
- `scripts/` - Scripts operativos

## Cómo Operar
Ver `docs/operations.md`

## Licencia
[Por definir]
```

### docs/architecture.md

```markdown
# Arquitectura del Sistema RAG

## Decisiones Cerradas (no debatir)

| Componente | Decisión |
|------------|----------|
| API de consultas | FastAPI async |
| Ingestión | CLI + colas Redis + worker asíncrono |
| Vector DB | Qdrant |
| Caché/Estado | Redis |
| Reverse Proxy | Nginx |
| Configuración | YAML por RAG + ENV global |
| Multi-RAG | Una colección por RAG en Qdrant |
| LangChain | Solo en ingestión (loaders/splitters) |

## Diagrama de Componentes

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Cliente   │────▶│    Nginx    │────▶│   FastAPI   │
└─────────────┘     │ (rate limit)│     │   (async)   │
                    └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
             ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
             │   Qdrant    │           │    Redis    │           │  OpenRouter │
             │ (vectores)  │           │(cache/cola) │           │    (LLM)    │
             └─────────────┘           └─────────────┘           └─────────────┘
                    ▲                          │
                    │                          │
             ┌──────┴──────┐           ┌───────┴───────┐
             │   Worker    │◀──────────│  Cola Redis   │
             │ (ingestión) │           │               │
             └─────────────┘           └───────────────┘
                    ▲
                    │
             ┌──────┴──────┐
             │  CLI Ingest │
             │  (carpetas) │
             └─────────────┘
```

## Flujo de Consulta
1. Request llega a Nginx
2. Rate limiting aplicado
3. FastAPI recibe query
4. Busca en caché Redis
5. Si miss: retrieval en Qdrant → LLM → respuesta
6. Guarda en caché
7. Retorna respuesta

## Flujo de Ingestión
1. Operador ejecuta CLI
2. CLI encola jobs en Redis
3. Worker consume cola
4. Procesa documentos (chunking, embeddings)
5. Upsert a Qdrant
```

### docs/operations.md

```markdown
# Operaciones

## Arranque

```bash
cd deploy/compose
docker compose up -d
```

## Parada

```bash
docker compose down
```

## Ingestión por CLI

```bash
# Colocar archivos en data/sources/<rag_id>/incoming/
# Ejecutar:
python -m services.ingest.cli submit --rag <rag_id>
```

## Reindexación

```bash
python -m services.ingest.cli reindex --rag <rag_id>
```

## Backups Manuales

[Por implementar - usar volúmenes Docker]

## Logs y Métricas

```bash
# Ver logs
docker compose logs -f api
docker compose logs -f ingest-worker

# Métricas
curl http://localhost/api/metrics
```
```

### docs/security.md

```markdown
# Seguridad

## Exposición por Nginx
- Todo el tráfico externo pasa por Nginx
- API no expuesta directamente

## TLS
- No implementado en MVP
- Recomendación: usar proxy externo o configurar certs en Nginx

## Rate Limiting
- Configurado en Nginx por IP
- Rate limit adicional por RAG en la API

## Autenticación
- No implementada en MVP
- Recomendación para producción: API keys o JWT

## Recomendaciones de Red Local
- Desplegar en red privada
- No exponer puertos de Qdrant/Redis externamente
- Usar firewall para limitar acceso
```

### .env.example

```bash
# OpenRouter LLM
OPENROUTER_API_KEY=your_api_key_here

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# Redis
REDIS_URL=redis://redis:6379/0

# App
DEFAULT_RAG=default
LOG_LEVEL=INFO
```

### .gitignore

```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.Python
pip-log.txt

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build
dist/
build/
*.egg-info/

# Node (si aplica)
node_modules/

# Data (mantener .gitkeep)
data/sources/*
!data/sources/.gitkeep
data/backups/*
!data/backups/.gitkeep

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

### data/sources/.gitkeep

```
# Placeholder para mantener la carpeta en git
# Los archivos de fuentes se colocan aquí organizados por RAG:
# data/sources/<rag_id>/incoming/
# data/sources/<rag_id>/processed/
# data/sources/<rag_id>/failed/
```

### data/backups/.gitkeep

```
# Placeholder para mantener la carpeta en git
# Aquí se almacenan backups manuales
```

---

## ✅ PUNTO DE ESPERA (Validación Humana)

Detenerse y verificar:

1. [ ] Existen exactamente las carpetas listadas
2. [ ] `README.md` existe y describe el alcance MVP
3. [ ] `docs/architecture.md` tiene el diagrama y decisiones
4. [ ] `docs/operations.md` tiene comandos básicos
5. [ ] `docs/security.md` tiene recomendaciones
6. [ ] `.env.example` tiene las variables placeholder
7. [ ] `.gitignore` incluye las exclusiones correctas
8. [ ] `.gitkeep` existe en `data/sources/` y `data/backups/`

---

## 🔒 QUEDA CONGELADO

- Estructura base de carpetas
- Nombres exactos de directorios

## ➡️ HABILITA

- Subproyecto 2: Crear `docker-compose` base en `deploy/compose/`
