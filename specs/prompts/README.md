# 📚 Prompts Ejecutables - RAG On-Premise

Este directorio contiene los **13 prompts ejecutables** derivados de los metaprompts del proyecto.

Cada prompt está diseñado para ser ejecutado en un modelo de lenguaje dentro de un IDE, siguiendo un orden secuencial.

---

## 📋 Índice de Prompts

### Prompts Base (1-10)

| # | Archivo | Descripción | Dependencias |
|---|---------|-------------|--------------|
| 01 | [01_layout_repositorio.md](./01_layout_repositorio.md) | Layout canónico del repositorio + scaffolding | Ninguna |
| 02 | [02_docker_compose.md](./02_docker_compose.md) | Docker Compose base (FastAPI, Qdrant, Redis, Nginx) | 01 |
| 03 | [03_configuracion_yaml.md](./03_configuracion_yaml.md) | Esquema de configuración YAML/ENV | 01, 02 |
| 04 | [04_cli_ingestion.md](./04_cli_ingestion.md) | CLI de ingestión (carpetas → colas Redis → worker) | 01, 02, 03 |
| 05 | [05_api_fastapi.md](./05_api_fastapi.md) | Contrato de API + esqueleto FastAPI | 01-04 |
| 06 | [06_qdrant_retrieval.md](./06_qdrant_retrieval.md) | Integración Qdrant + embeddings + retrieval | 01-05 |
| 07 | [07_redis_cache_ratelimit.md](./07_redis_cache_ratelimit.md) | Redis: caché, sesiones, rate limiting | 01-06 |
| 08 | [08_llm_openrouter.md](./08_llm_openrouter.md) | Integración OpenRouter (LLM) + fallback | 01-07 |
| 09 | [09_observability.md](./09_observability.md) | Observabilidad mínima (logs + métricas) | 01-08 |
| 10 | [10_state_verification.md](./10_state_verification.md) | Gestión de estado y verificación | 01-09 |

### Prompts Adicionales (11-13) - Para Producto Funcional

| # | Archivo | Descripción | Dependencias |
|---|---------|-------------|--------------|
| 11 | [11_embeddings_reales.md](./11_embeddings_reales.md) | Embeddings reales (OpenAI/local) | 01-10 |
| 12 | [12_config_loader_pdf.md](./12_config_loader_pdf.md) | Cargador de config YAML + procesador PDF | 01-11 |
| 13 | [13_tests_e2e.md](./13_tests_e2e.md) | Tests end-to-end básicos | 01-12 |

---

## 📊 Estado de Completitud

| Fase | Prompts | Resultado |
|------|---------|-----------|
| **Arquitectura** | 01-10 | Estructura completa, código esqueleto |
| **Funcionalidad** | 11-12 | Embeddings reales, PDFs, config runtime |
| **Validación** | 13 | Tests automatizados |

### Con prompts 1-10 obtienes:
- ✅ Estructura de repositorio completa
- ✅ Docker Compose funcional
- ✅ API FastAPI con endpoints
- ⚠️ Embeddings DUMMY (no semánticos)
- ⚠️ Sin procesamiento PDF real
- ⚠️ Sin tests automatizados

### Con prompts 1-13 obtienes:
- ✅ Todo lo anterior
- ✅ Embeddings reales (OpenAI)
- ✅ Procesamiento PDF funcional
- ✅ Carga de configuración YAML en runtime
- ✅ Tests e2e básicos
- ✅ **Sistema listo para producción**

---

## 🚀 Cómo Usar

### Orden de Ejecución

Los prompts **DEBEN** ejecutarse en orden secuencial (01 → 13). Cada uno depende de los artefactos generados por los anteriores.

### Proceso por Prompt

1. **Abrir** el archivo del prompt correspondiente
2. **Copiar** el contenido completo
3. **Pegar** en el chat del modelo en el IDE
4. **Esperar** a que el modelo genere los archivos
5. **Validar** según el checklist de cada prompt
6. **Confirmar** antes de continuar al siguiente

### Regla Crítica

> ⚠️ **El modelo NO debe ejecutar comandos.**  
> **El humano ejecutará los comandos manualmente.**

---

## 📁 Estructura de Artefactos Generados

Después de ejecutar los 13 prompts, el proyecto tendrá esta estructura:

```
raf_chatbot/
├── README.md
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements-test.txt
├── docs/
│   ├── architecture.md
│   ├── operations.md
│   ├── security.md
│   ├── configuration.md
│   ├── qdrant.md
│   ├── redis.md
│   ├── llm.md
│   ├── observability.md
│   └── state_management.md
├── deploy/
│   ├── compose/
│   │   └── docker-compose.yml
│   └── nginx/
│       ├── nginx.conf
│       └── README.md
├── configs/
│   ├── client/
│   │   └── client.yaml.example
│   └── rags/
│       ├── example_rag.yaml
│       └── prompts/
│           ├── system_default.txt
│           └── user_default.txt
├── data/
│   ├── sources/
│   │   └── .gitkeep
│   └── backups/
│       └── .gitkeep
├── services/
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── query.py
│   │   │   │   └── metrics.py
│   │   │   ├── qdrant_client.py
│   │   │   ├── retrieval.py
│   │   │   ├── redis_client.py
│   │   │   ├── cache.py
│   │   │   ├── sessions.py
│   │   │   ├── rate_limit.py
│   │   │   ├── prompting.py
│   │   │   ├── observability.py
│   │   │   ├── embeddings/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── openai_embeddings.py
│   │   │   │   └── local_embeddings.py
│   │   │   └── llm/
│   │   │       └── openrouter_client.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   └── ingest/
│       ├── app.py
│       ├── worker.py
│       ├── cli.py
│       ├── pdf_processor.py
│       ├── cli.md
│       ├── queue_contract.md
│       ├── requirements.txt
│       └── README.md
├── scripts/
│   ├── verify_state.py
│   ├── state_expected.json
│   └── seed_demo_data.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_query.py
│   ├── test_cache.py
│   ├── test_rate_limit.py
│   ├── test_ingest.py
│   ├── test_metrics.py
│   └── README.md
└── specs/
    ├── metaprompts.md
    └── prompts/
        └── (este directorio)
```

---

## ✅ Checklist Global

Antes de considerar el proyecto completo:

- [ ] Todos los 13 prompts ejecutados en orden
- [ ] `python scripts/verify_state.py` devuelve `STATE_OK`
- [ ] `docker compose config` valida sin errores
- [ ] Los contenedores levantan (`docker compose up -d`)
- [ ] `/health` responde OK
- [ ] `/query` funciona con datos de prueba
- [ ] `/metrics` muestra contadores
- [ ] Embeddings son semánticamente relevantes
- [ ] PDFs se procesan correctamente
- [ ] `pytest tests/` pasa con >80% tests verdes

---

## 🔑 Variables de Entorno Requeridas

```bash
# LLM (requerido)
OPENROUTER_API_KEY=sk-or-xxx

# Embeddings (requerido para producción)
OPENAI_API_KEY=sk-xxx

# Servicios (configurados en docker-compose)
QDRANT_URL=http://qdrant:6333
REDIS_URL=redis://redis:6379/0

# Opcionales
LOG_LEVEL=INFO
EMBEDDING_MODEL=text-embedding-ada-002
```

---

## 📖 Documentación Relacionada

- [Metaprompts originales](../metaprompts.md) - Especificación completa
- [Arquitectura](../../docs/architecture.md) - Diseño del sistema
- [Operaciones](../../docs/operations.md) - Guía de operación

---

## 🔄 Versionado

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2024-XX-XX | Versión inicial con 10 prompts |
| 1.1.0 | 2024-XX-XX | Añadidos prompts 11-13 para producto completo |