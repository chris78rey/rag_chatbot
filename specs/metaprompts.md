---
tags:
  - rag
  - docker
  - python
  - langchain
  - fastapi
---
1. **Subproyecto 1 – Layout canónico del repositorio + scaffolding mínimo**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 1 de 10
    
    _(Este metaprompt se ejecuta en el MODELO GRANDE. Su salida será un PROMPT EJECUTABLE EN IDE.)_
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto técnico de producto RAG on-premise**, especializado en definir **estructura de repositorio auditable** y generar **instrucciones ejecutables en IDE**, sin ejecutar código ni asumir decisiones no explícitas.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Producto: RAG comercializable, 100% local, replicable por cliente mediante **docker-compose** aislado.
        
    - Objetivo de rendimiento: **~300 usuarios concurrentes**, latencia baja.
        
    - Stack decidido (no debatir): **FastAPI async** (consultas), **colas externas solo para ingestión**, **Qdrant** vector DB, **Redis** (colas/caché/estado ligero), **Nginx** reverse proxy, **configuración YAML/ENV**, ingestión por **CLI** basada en carpetas, **multi-RAG** (colección por RAG en Qdrant), **LangChain parcial** solo en ingestión (loaders/splitters).
        
    - No-MVP: interfaz administrativa avanzada, auto-update, Kubernetes, “auto-tuning” inteligente.
        
    - Requisito operativo: mantenimiento simple cambiando parámetros; auditable; reproducible.
        
    - Restricción: el modelo no ejecuta comandos, no asume archivos previos, no inventa estado.
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Definir y crear el **layout canónico del repositorio** (carpetas y archivos vacíos/plantilla) que soporte los siguientes subproyectos.
    
    - Éxito binario: existe una estructura de directorios y archivos base con nombres exactos y propósito documentado en `README.md`.
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: Markdown, archivos vacíos, plantillas `.env.example`, YAML de ejemplo, `.gitignore`.
        
    - Prohibido: implementar lógica de negocio, dependencias, código funcional de la API, docker-compose completo (eso es Subproyecto 2).
        
    - Convención: rutas en minúsculas, nombres explícitos, nada “misc”.
        
    - No modificar: nada (repositorio inicia vacío, se crea todo en este subproyecto).
        
    - Todo archivo creado debe incluir un encabezado de comentario/nota de propósito (si aplica al formato).
        
    
    ### 5) Artefactos esperados
    
    Estructura mínima:
    
    - `README.md`
        
    - `docs/` (documentación operativa)
        
        - `docs/architecture.md`
            
        - `docs/operations.md`
            
        - `docs/security.md`
            
    - `deploy/` (todo lo de despliegue)
        
        - `deploy/compose/` (docker-compose y archivos relacionados)
            
        - `deploy/nginx/` (plantillas)
            
    - `configs/` (configuración declarativa)
        
        - `configs/client/`
            
        - `configs/rags/`
            
    - `data/` (solo placeholders + `.gitkeep`)
        
        - `data/sources/`
            
        - `data/backups/`
            
    - `services/`
        
        - `services/api/` (FastAPI)
            
        - `services/ingest/` (CLI/worker)
            
    - `scripts/` (scripts operativos locales)
        
    - `.env.example`
        
    - `.gitignore`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    #### 6.1 Rol del modelo ligero
    
    El modelo ligero actúa como **asistente de edición mecánica**:
    
    - Puede crear carpetas/archivos y pegar contenido literal.
        
    - No puede rediseñar, no puede cambiar nombres, no puede “mejorar”.
        
    - Si falta información, debe detenerse y marcarlo como bloqueo.
        
    
    #### 6.2 Instrucciones operativas claras
    
    Debe crear exactamente la estructura y contenidos mínimos solicitados.
    
    #### 6.3 Ejecución controlada
    
    Debe incluir textualmente:
    
    > “El modelo NO debe ejecutar comandos.  
    > El humano ejecutará los comandos manualmente.”
    
    **PROMPT EJECUTABLE EN IDE (para copiar/pegar tal cual):**
    
    ```text
    ROL (modelo ligero):
    - Editor mecánico y preciso. No razonar arquitectura. No renombrar nada.
    - Si un archivo ya existe, no lo edites salvo que se indique explícitamente.
    
    OBJETIVO:
    - Crear el layout canónico del repositorio para un producto RAG on-premise.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    PASOS:
    1) Crear estas carpetas (vacías si aplica):
       - docs/
       - deploy/compose/
       - deploy/nginx/
       - configs/client/
       - configs/rags/
       - data/sources/
       - data/backups/
       - services/api/
       - services/ingest/
       - scripts/
    
    2) Crear archivos con contenido mínimo (exacto) indicado:
       - README.md
       - docs/architecture.md
       - docs/operations.md
       - docs/security.md
       - .env.example
       - .gitignore
       - data/sources/.gitkeep
       - data/backups/.gitkeep
    
    3) Pegar estos contenidos:
    
    README.md:
    - Título: "RAG On-Premise (FastAPI + Qdrant + Redis)"
    - Secciones: Propósito, Alcance MVP, Componentes, Flujo alto nivel, Estructura del repo, Cómo operar (placeholders), Licencia (placeholder).
    
    docs/architecture.md:
    - Describir decisiones cerradas: FastAPI async consultas; ingestión por CLI/colas; Qdrant; Redis; Nginx; YAML/ENV; multi-RAG por colección.
    - Incluir diagrama textual (sin mermaid obligatorio).
    
    docs/operations.md:
    - Secciones: Arranque, Parada, Ingestión por CLI, Reindexación, Backups manuales, Logs/Métricas.
    
    docs/security.md:
    - Secciones: Exposición por Nginx, TLS, rate limiting, sin auth en MVP, recomendaciones de red local.
    
    .env.example:
    - Colocar variables placeholder para: OPENROUTER_API_KEY, QDRANT_URL, REDIS_URL, DEFAULT_RAG, LOG_LEVEL.
    
    .gitignore:
    - Ignorar: .env, __pycache__/, .venv/, dist/, node_modules/, data/sources/* (except .gitkeep), data/backups/* (except .gitkeep)
    
    PUNTO DE ESPERA (validación humana):
    - Detenerse y pedir verificación cuando todo esté creado.
    ```
    
    ### 7) Validación y control de estado
    
    Validación binaria (humana):
    
    - Verificar que existen exactamente las carpetas/archivos listados.
        
    - Verificar que `README.md` describe alcance MVP y decisiones cerradas.
        
    - Errores típicos: nombres distintos (`config` vs `configs`), rutas mal ubicadas, `.gitignore` ignorando `.gitkeep`.
        
    
    ### 8) Cierre del metaprompt
    
    Al finalizar, queda congelado:
    
    - La **estructura base** y nombres de carpetas.  
        Habilita el siguiente subproyecto:
        
    - Crear `docker-compose` base en `deploy/compose/` sin ambigüedad.
        

---

2. **Subproyecto 2 – docker-compose base (FastAPI, Qdrant, Redis, Nginx) + volúmenes**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 2 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto DevOps on-premise** para empaquetado con **docker-compose**, enfocado en reproducibilidad y aislamiento por cliente.
    
    ### 2) Contexto autosuficiente del sistema
    
    Decisiones cerradas:
    
    - Todo en `docker-compose` por cliente.
        
    - Servicios mínimos: `api` (FastAPI), `qdrant`, `redis`, `nginx`, `ingest-worker` (tareas pesadas asíncronas).
        
    - Persistencia: volúmenes Docker para Qdrant, Redis (si se decide persistir), fuentes (carpetas), logs.
        
    - Reverse proxy: Nginx con rate limiting básico.
        
    - Config: `.env` y YAML por RAG (más adelante).
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Crear `deploy/compose/docker-compose.yml` + plantillas mínimas Nginx para levantar el stack.
    
    - Éxito binario: `docker compose config` no arroja errores y el stack levanta (validación humana).
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: `docker-compose.yml`, `nginx.conf` o `default.conf`, `Dockerfile` placeholders si aplica.
        
    - Prohibido: implementar lógica completa del API; inventar puertos no documentados; añadir servicios extra (Prometheus, etc.).
        
    - Qdrant obligatorio.
        
    - Redis obligatorio.
        
    - Nginx obligatorio.
        
    - Ingest worker obligatorio (aunque sea placeholder).
        
    
    ### 5) Artefactos esperados
    
    - `deploy/compose/docker-compose.yml`
        
    - `deploy/nginx/nginx.conf` (o `deploy/nginx/conf.d/default.conf`)
        
    - `deploy/nginx/README.md` (cómo aplicar TLS luego, sin implementarlo aún)
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    #### 6.1 Rol del modelo ligero
    
    Editor mecánico: crear/pegar YAML y configs sin cambiar nombres.
    
    #### 6.3 Ejecución controlada
    
    Debe incluir textualmente:
    
    > “El modelo NO debe ejecutar comandos.  
    > El humano ejecutará los comandos manualmente.”
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Crear archivos exactos y pegar contenido literal. No optimizar.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    ARCHIVOS A CREAR/MODIFICAR:
    - deploy/compose/docker-compose.yml
    - deploy/nginx/nginx.conf
    - deploy/nginx/README.md
    
    docker-compose.yml (requisitos):
    - version: "3.9"
    - services:
      - qdrant (imagen oficial), puerto 6333 expuesto solo a red interna (o localhost), volumen persistente
      - redis (imagen oficial), puerto 6379 (idealmente interno), volumen opcional
      - api (FastAPI): build desde services/api (Dockerfile placeholder permitido), env_file .env, depende de qdrant/redis
      - ingest-worker: build desde services/ingest, env_file .env, depende de redis/qdrant, comando placeholder
      - nginx: imagen nginx, mapea 80:80, proxy hacia api, rate limiting básico
    - networks: una red dedicada
    - volumes: qdrant_data, redis_data (si se define), sources_data (mapeo a data/sources), logs_data
    
    deploy/nginx/nginx.conf:
    - server escucha 80
    - location /api/ proxy_pass http://api:8000/
    - rate limit básico por IP (zona y burst)
    - headers proxy básicos
    
    deploy/nginx/README.md:
    - Explicar cómo añadir TLS luego (certs), sin implementarlo.
    
    COMANDOS (humano ejecuta manualmente, no ejecutar aquí):
    1) docker compose -f deploy/compose/docker-compose.yml config
    2) docker compose -f deploy/compose/docker-compose.yml up -d
    3) docker compose -f deploy/compose/docker-compose.yml ps
    
    PUNTO DE ESPERA:
    - Detenerse para que el humano confirme que 'config' valida y que los contenedores levantan.
    ```
    
    ### 7) Validación y control de estado
    
    - Validación humana: `docker compose config` OK; `ps` muestra servicios “Up”.
        
    - Errores típicos: rutas build incorrectas, puertos en conflicto, Nginx proxy a nombre equivocado.
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Nombres de servicios y volúmenes.  
        Habilita:
        
    - Contrato de configuración y arranque uniforme del API/worker (Subproyecto 3).
        

---

3. **Subproyecto 3 – Esquema de configuración (YAML/ENV) por cliente y por RAG**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 3 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto de configuración declarativa** para un producto multi-RAG.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Sin DB de configuración: todo por archivos.
        
    - Multi-RAG: una colección por RAG en Qdrant.
        
    - Cada RAG define: colección, embeddings, chunking, top-k, límites de tokens, prompt templates, rate limit, mensajes de error.
        
    - Cliente define: puertos, límites globales, modelo LLM default, fallback, rutas de fuentes.
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Definir formato y ejemplos de:
    
    - `configs/client/client.yaml`
        
    - `configs/rags/<rag_id>.yaml`
        
    - Éxito binario: existen ejemplos completos + documentación de campos.
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: YAML y Markdown.
        
    - Prohibido: lógica de carga real (eso se implementa luego).
        
    - Campos deben ser explícitos y con defaults documentados.
        
    
    ### 5) Artefactos esperados
    
    - `configs/client/client.yaml.example`
        
    - `configs/rags/example_rag.yaml`
        
    - `docs/configuration.md`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Crear YAMLs de ejemplo y documentación sin cambiar llaves ni nombres.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    CREAR ARCHIVOS:
    - configs/client/client.yaml.example
    - configs/rags/example_rag.yaml
    - docs/configuration.md
    
    client.yaml.example debe incluir:
    - app: host, port, log_level
    - qdrant: url, api_key(optional)
    - redis: url
    - llm: provider=openrouter, api_key_env_var, default_model, fallback_model, timeout_s, max_retries
    - paths: sources_root, rags_config_dir
    - concurrency: global_max_inflight_requests, global_rate_limit
    - security: behind_nginx=true, trusted_proxies
    - cache: enabled, ttl_seconds
    - sessions: enabled, ttl_seconds
    
    example_rag.yaml debe incluir:
    - rag_id
    - collection_name
    - embeddings: model_name (string), dim (int placeholder), batch_size
    - chunking: splitter, chunk_size, chunk_overlap
    - retrieval: top_k, score_threshold(optional), max_context_chunks
    - prompting: system_template_path, user_template_path, max_tokens, temperature
    - rate_limit: rps, burst
    - errors: no_context_message, provider_error_message
    - cache: enabled, ttl_seconds
    - sessions: history_turns, ttl_seconds
    
    docs/configuration.md:
    - Tabla de campos (campo, tipo, requerido, default, descripción)
    - Ejemplos de override por cliente
    - Reglas: un RAG = una colección
    
    PUNTO DE ESPERA:
    - Detenerse y solicitar confirmación de que los YAML están completos y coherentes.
    ```
    
    ### 7) Validación y control de estado
    
    - Validación humana: revisión de que cada campo requerido existe.
        
    - Error típico: mezclar config global con config por RAG.
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Llaves YAML y significado.  
        Habilita:
        
    - Implementar loader de config en API/worker y CLI de ingestión (Subproyecto 4).
        

---

4. **Subproyecto 4 – CLI de ingestión (carpetas → colas Redis → worker)**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 4 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto de pipeline de ingestión** (PDF/texto) con colas, orientado a mantenibilidad.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Ingestión no debe bloquear consultas.
        
    - Ingestión se ejecuta por CLI obligatoria (comandos).
        
    - Worker procesa tareas pesadas: lectura PDF, chunking, embeddings, upsert a Qdrant.
        
    - Redis hace de broker (cola) y también caché/estado (ya decidido).
        
    - PDFs deben “entenderse bien” (mejor loader + extracción robusta; sin prometer OCR en MVP si no se definió).
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Definir comandos, estructura de carpetas de fuentes por RAG y contrato de mensajes en la cola.
    
    - Éxito binario: existe `services/ingest/cli.md` + `services/ingest/queue_contract.md` + estructura de fuentes.
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: documentación y esqueletos (archivos `.py` vacíos con docstring) sin lógica completa.
        
    - Prohibido: implementar embeddings reales (se hará en Subproyecto 6).
        
    - Debe ser explícito el formato: `data/sources/<rag_id>/...`
        
    
    ### 5) Artefactos esperados
    
    - `services/ingest/README.md`
        
    - `services/ingest/cli.md`
        
    - `services/ingest/queue_contract.md`
        
    - `data/sources/README.md`
        
    - Placeholders: `services/ingest/app.py`, `services/ingest/worker.py`, `services/ingest/cli.py`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Crear documentación + esqueletos de archivos Python con docstrings. No implementar lógica real.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    CREAR/MODIFICAR:
    - data/sources/README.md
    - services/ingest/README.md
    - services/ingest/cli.md
    - services/ingest/queue_contract.md
    - services/ingest/app.py
    - services/ingest/worker.py
    - services/ingest/cli.py
    
    CONTENIDO OBLIGATORIO:
    data/sources/README.md:
    - Estructura: data/sources/<rag_id>/incoming, processed, failed
    - Regla: solo CLI mueve/gestiona
    
    services/ingest/queue_contract.md:
    - Definir cola Redis: key name (ej: rag:ingest:queue)
    - Mensaje JSON: job_id, rag_id, source_path, source_type(pdf|txt), submitted_at, options{reindex,bool}
    - Estados: queued, processing, done, failed; key de estado por job_id
    
    services/ingest/cli.md:
    - Comandos propuestos (documentados):
      1) ingest submit --rag <id> --path data/sources/<id>/incoming
      2) ingest reindex --rag <id>
      3) ingest status --job <job_id>
    - Explicar que el worker consume cola y escribe logs.
    
    Archivos .py:
    - Solo docstring describiendo responsabilidades y funciones esperadas (sin código real).
    
    PUNTO DE ESPERA:
    - Detenerse para revisión humana del contrato de cola y comandos.
    ```
    
    ### 7) Validación y control de estado
    
    - Validación humana: coherencia entre rutas, cola, y estados.
        
    - Error típico: no separar “incoming vs processed”.
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Contrato de cola y rutas de fuentes.  
        Habilita:
        
    - Implementar API de consulta y servicio FastAPI (Subproyecto 5).
        

---

5. **Subproyecto 5 – Contrato de API (consulta RAG) + esqueleto FastAPI**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 5 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto de API** enfocado en latencia baja y contrato estable.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Consultas: FastAPI async en tiempo real.
        
    - Multi-RAG: el cliente elige `rag_id`.
        
    - Sesión ligera: historial corto (temporal).
        
    - Caché de respuestas: Redis por hash (rag_id + query + parámetros).
        
    - Sin autenticación en MVP; pero detrás de Nginx con rate limiting.
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Definir endpoints y crear esqueleto de proyecto FastAPI sin lógica de retrieval todavía.
    
    - Éxito binario: existen rutas FastAPI con modelos Pydantic y documentación OpenAPI visible al levantar (validación humana).
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: FastAPI, Pydantic, estructura app, endpoints que devuelven dummy.
        
    - Prohibido: integrar Qdrant real o OpenRouter real (eso viene después).
        
    - Debe existir endpoint de métricas básicas (placeholder) ya decidido.
        
    
    ### 5) Artefactos esperados
    
    - `services/api/app/main.py`
        
    - `services/api/app/models.py`
        
    - `services/api/app/routes/query.py`
        
    - `services/api/app/routes/health.py`
        
    - `services/api/app/routes/metrics.py`
        
    - `services/api/README.md`
        
    - `services/api/Dockerfile` (mínimo)
        
    - `services/api/requirements.txt` (mínimo)
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Crear esqueleto FastAPI con endpoints y respuestas dummy. No integrar Qdrant/LLM.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    CREAR ESTRUCTURA:
    - services/api/app/
      - main.py
      - models.py
      - routes/health.py
      - routes/query.py
      - routes/metrics.py
    - services/api/README.md
    - services/api/Dockerfile
    - services/api/requirements.txt
    
    CONTRATO ENDPOINTS (mínimo):
    1) GET /health -> {status:"ok"}
    2) POST /query
       Request:
         - rag_id: string
         - question: string
         - session_id: string optional
         - top_k: int optional (override)
       Response:
         - rag_id
         - answer (string)
         - context_chunks: list[{id, source, text, score}]
         - latency_ms (int)
         - cache_hit (bool)
         - session_id (string)
    3) GET /metrics -> contadores dummy (json)
    
    IMPLEMENTACIÓN:
    - main.py registra routers y habilita docs.
    - query endpoint responde dummy con answer="NOT_IMPLEMENTED" y lista vacía.
    - models.py define Pydantic models exactos.
    
    COMANDOS (humano ejecuta manualmente):
    1) docker compose -f deploy/compose/docker-compose.yml build api
    2) docker compose -f deploy/compose/docker-compose.yml up -d api
    3) Abrir /docs vía Nginx (/api/docs si aplica el proxy)
    
    PUNTO DE ESPERA:
    - Confirmación humana de que /health y /docs responden.
    ```
    
    ### 7) Validación y control de estado
    
    - `/health` responde ok.
        
    - OpenAPI muestra `/query` con schemas correctos.
        
    - Errores típicos: rutas montadas distinto por Nginx (`/api`).
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Contrato request/response de `/query`.  
        Habilita:
        
    - Integración con Qdrant (Subproyecto 6) y Redis cache (Subproyecto 7).
        

---

6. **Subproyecto 6 – Integración Qdrant + embeddings + upsert/retrieval básico**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 6 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto backend RAG** enfocado en integrar Qdrant con colecciones por RAG y retrieval eficiente.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Qdrant es vector DB en contenedor.
        
    - Multi-RAG: colección por RAG.
        
    - Embeddings: modelo configurable por YAML (en MVP puede usarse un proveedor simple; si no se definió local embeddings, se documenta como parámetro).
        
    - Ingestión: worker consume cola y hace upsert.
        
    - Consulta: API hace search top_k y arma contexto.
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Implementar:
    
    - Cliente Qdrant
        
    - Creación/validación de colección por RAG
        
    - Upsert de puntos con payload mínimo
        
    - Búsqueda top_k para `/query` (todavía sin llamada LLM final si se decide separarlo)
        
    - Éxito binario: `/query` devuelve `context_chunks` reales desde Qdrant (con datos de prueba).
        
    
    ### 4) Reglas estrictas de implementación
    
    - Permitido: qdrant-client, httpx/requests, Python async si aplica.
        
    - Prohibido: cambiar contrato de `/query`.
        
    - Debe respetar `collection_name` del YAML.
        
    - Payload mínimo por chunk: `source_path`, `page`, `chunk_index`, `text`.
        
    
    ### 5) Artefactos esperados
    
    - `services/api/app/qdrant_client.py`
        
    - `services/api/app/retrieval.py`
        
    - `services/ingest/worker_impl.py` (o ampliar `worker.py`)
        
    - `scripts/seed_demo_data.py` (opcional, para validar)
        
    - Documentación: `docs/qdrant.md`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Implementar integración mínima con Qdrant respetando contratos existentes. No cambiar schemas.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    IMPLEMENTAR:
    1) services/api/app/qdrant_client.py
       - Funciones: get_client(), ensure_collection(rag_config), upsert_chunks(rag_config, vectors+payload), search(rag_config, query_vector, top_k)
    
    2) services/api/app/retrieval.py
       - Función: retrieve_context(rag_id, question, top_k_override=None) -> lista chunks con score
    
    3) Modificar services/api/app/routes/query.py
       - En vez de dummy, llamar retrieve_context y devolver context_chunks con textos reales.
       - answer puede seguir "NOT_IMPLEMENTED" si LLM aún no se integra aquí.
    
    4) Worker:
       - Extender services/ingest/worker.py para leer job, cargar rag_config, producir chunks (placeholder si splitter no está aún), y hacer upsert.
       - Si splitter aún no se implementa, crear un modo DEMO: cada txt línea=chunk.
    
    VALIDACIÓN (humano ejecuta):
    - Crear un RAG ejemplo con rag_id y collection_name.
    - Poner un .txt en data/sources/<rag_id>/incoming
    - Ejecutar CLI submit (documentado) y verificar que worker lo procesa.
    - Consultar /query y ver context_chunks no vacíos.
    
    COMANDOS (humano):
    1) docker compose -f deploy/compose/docker-compose.yml build api ingest-worker
    2) docker compose -f deploy/compose/docker-compose.yml up -d
    3) Ver logs: docker compose -f ... logs -f ingest-worker
    4) Probar /query con curl o /docs
    
    PUNTO DE ESPERA:
    - Confirmación humana de que Qdrant tiene la colección y /query devuelve chunks.
    ```
    
    ### 7) Validación y control de estado
    
    - Validar colección en Qdrant (UI/endpoint) y puntos insertados.
        
    - Validar `/query` retorna `context_chunks` con `score` numérico.
        
    - Errores típicos: dimensión embedding inconsistente, colección no creada, payload faltante.
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Estructura payload y nombre de colección por RAG.  
        Habilita:
        
    - Redis cache, rate limiting y sesiones (Subproyecto 7).
        

---

7. **Subproyecto 7 – Redis: colas, caché de respuestas, sesiones ligeras, rate limit por RAG**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 7 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto de performance y concurrencia** con Redis, orientado a límites configurables por RAG.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Redis ya se usa como broker para ingestión.
        
    - Caché: hash(query+rag+params) con TTL por RAG.
        
    - Sesiones: historial corto por session_id con TTL.
        
    - Rate limit: configurable por RAG (rps/burst) y aplicable en API (complementario a Nginx).
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Implementar utilidades Redis y middleware simple para:
    
    - cache hit/miss en `/query`
        
    - session store
        
    - rate limiting por RAG
        
    - Éxito binario: `/query` marca `cache_hit=true` al repetir la consulta y aplica 429 cuando excede límites.
        
    
    ### 4) Reglas estrictas de implementación
    
    - No cambiar contrato `/query`.
        
    - No introducir dependencias complejas (solo redis client).
        
    - Si rate limit falla, debe degradar con mensaje controlado (según config).
        
    
    ### 5) Artefactos esperados
    
    - `services/api/app/redis_client.py`
        
    - `services/api/app/cache.py`
        
    - `services/api/app/sessions.py`
        
    - `services/api/app/rate_limit.py`
        
    - Documentación: `docs/redis.md`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Implementar cache/sessions/rate-limit en FastAPI con Redis. No rediseñar.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    TAREAS:
    1) Crear redis_client.py con get_redis() y helpers async/sync (según librería elegida).
    2) cache.py:
       - build_cache_key(rag_id, question, top_k, etc.)
       - get_cached_answer(...)
       - set_cached_answer(..., ttl)
    3) sessions.py:
       - get_session_history(session_id)
       - append_turn(session_id, question, answer)
       - ttl por config
    4) rate_limit.py:
       - check_rate_limit(rag_id, client_ip) usando token bucket simple en Redis
       - si excede: levantar HTTPException 429 con mensaje configurable
    5) Integrar en /query:
       - aplicar rate limit
       - consultar cache antes de retrieval/LLM
       - set cache al final
    
    VALIDACIÓN (humano):
    - Ejecutar 2 veces la misma consulta y verificar cache_hit cambia a true
    - Disparar muchas consultas y verificar 429
    
    PUNTO DE ESPERA:
    - Confirmación humana de cache_hit y 429.
    ```
    
    ### 7) Validación y control de estado
    
    - Validar keys en Redis (prefijos consistentes).
        
    - Validar TTL efectivo.
        
    - Error típico: cache key no incluye parámetros → respuestas incorrectas.
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Prefijos de keys Redis y algoritmo rate limit.  
        Habilita:
        
    - Integración LLM OpenRouter + fallback (Subproyecto 8).
        

---

8. **Subproyecto 8 – Integración OpenRouter (LLM) + fallback + prompts por RAG**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 8 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto de integración LLM** centrado en confiabilidad y control de costo.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Proveedor: OpenRouter (API key por ENV).
        
    - Estrategia: modelo principal barato + fallback si falla.
        
    - Prompts: configurables por archivo por RAG (templates).
        
    - Contexto: top_k/chunks/tokens por RAG.
        
    - Respuestas deben incluir trazabilidad básica (latencia_ms, etc.).
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Implementar llamada al LLM en `/query` usando contexto de Qdrant + templates por RAG, con fallback automático.
    
    - Éxito binario: `/query` devuelve `answer` generado; si se fuerza fallo del modelo principal, usa fallback.
        
    
    ### 4) Reglas estrictas de implementación
    
    - No cambiar contrato `/query`.
        
    - No hardcodear modelos: deben venir de config.
        
    - Temperatura y max_tokens deben venir de config por RAG (override).
        
    - Fallback solo ante error/timeout.
        
    
    ### 5) Artefactos esperados
    
    - `services/api/app/llm/openrouter_client.py`
        
    - `services/api/app/prompting.py`
        
    - Plantillas:
        
        - `configs/rags/prompts/system_default.txt`
            
        - `configs/rags/prompts/user_default.txt`
            
    - Docs: `docs/llm.md`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Implementar cliente OpenRouter y prompting por plantillas. No cambiar contratos.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    IMPLEMENTAR:
    1) openrouter_client.py:
       - call_chat_completion(model, messages, timeout) con retries limitados
       - manejo de errores y retorno estructurado
    2) prompting.py:
       - load_template(path)
       - build_messages(system_template, user_template, question, context_chunks, session_history)
    3) Integrar en /query:
       - retrieval_context
       - build_messages
       - call principal model; en excepción: call fallback model
       - set answer final
       - respetar max_tokens/temperature configurados
    
    CREAR PLANTILLAS:
    - configs/rags/prompts/system_default.txt (instrucciones breves, responder solo con evidencia del contexto)
    - configs/rags/prompts/user_default.txt (formato que inserta {question} y {context})
    
    VALIDACIÓN (humano):
    - Probar consulta real y ver answer no vacío.
    - Simular fallo (cambiar temporalmente modelo principal a uno inválido) y verificar fallback.
    
    PUNTO DE ESPERA:
    - Confirmación humana de fallback funcional.
    ```
    
    ### 7) Validación y control de estado
    
    - Validar que se registran errores y se activa fallback.
        
    - Validar que prompts se cargan desde archivos y se recargan sin redeploy si así se implementa (mínimo: lectura en cada request o caché con invalidación simple).
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Interfaz cliente OpenRouter y rutas de templates.  
        Habilita:
        
    - Observabilidad y métricas reales (Subproyecto 9).
        

---

9. **Subproyecto 9 – Observabilidad mínima: logs estructurados + métricas básicas por endpoint**  
    → **METAPROMPT COMPLETO**
    
    ---
    
    ## 🔹 METAPROMPT — Subproyecto 9 de 10
    
    ### 1) Rol que debe asumir el modelo
    
    Actúa como **arquitecto SRE mínimo viable**, enfocado en diagnósticos sin infraestructura extra.
    
    ### 2) Contexto autosuficiente del sistema
    
    - Se requiere: logs + métricas internas (JSON endpoint).
        
    - Métricas: latencia, errores, cache hit rate, rate limit triggers, ingest jobs.
        
    - Sin Prometheus/Grafana en MVP.
        
    
    ### 3) Objetivo técnico único del subproyecto
    
    Implementar contadores y mediciones simples expuestas en `/metrics` y logs estructurados.
    
    - Éxito binario: `/metrics` devuelve contadores reales que cambian al hacer consultas.
        
    
    ### 4) Reglas estrictas de implementación
    
    - No añadir servicios.
        
    - No cambiar contrato de `/query`.
        
    - Logs sin datos sensibles (no imprimir API keys ni contexto completo si se considera riesgoso).
        
    
    ### 5) Artefactos esperados
    
    - `services/api/app/observability.py`
        
    - Ajustes en `routes/metrics.py`
        
    - Documentación: `docs/observability.md`
        
    
    ### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)
    
    **PROMPT EJECUTABLE EN IDE:**
    
    ```text
    ROL (modelo ligero):
    - Implementar contadores/latencias en memoria del proceso y exponerlos por /metrics.
    
    REGLA CRÍTICA:
    El modelo NO debe ejecutar comandos.
    El humano ejecutará los comandos manualmente.
    
    TAREAS:
    1) Crear observability.py con:
       - contadores globales: requests_total, errors_total, cache_hits_total, rate_limited_total
       - latencia: avg_ms simple o lista limitada para p95 aproximado (sin librerías extra)
    2) En /query:
       - medir start/end, actualizar contadores
       - marcar cache_hit
    3) /metrics:
       - devolver json con contadores y latencias
    
    VALIDACIÓN (humano):
    - Llamar /metrics, luego hacer 5 consultas, luego /metrics y ver cambios.
    
    PUNTO DE ESPERA:
    - Confirmación humana de métricas cambiantes.
    ```
    
    ### 7) Validación y control de estado
    
    - Verificar que métricas no se reinician salvo reinicio del contenedor (esperado).
        
    - Errores típicos: condiciones de carrera (mitigar con locks simples si aplica).
        
    
    ### 8) Cierre del metaprompt
    
    Congelar:
    
    - Nombres de métricas expuestas.  
        Habilita:
        
    - Pruebas de carga y validación de 300 concurrencia (Subproyecto 10).
        

---

10. **Subproyecto 10 – Gestión de estado (obligatorio): verificación de estructura, invariantes y prevención de deriva**  
    → **METAPROMPT COMPLETO**
    

---

## 🔹 METAPROMPT — Subproyecto 10 de 10

### 1) Rol que debe asumir el modelo

Actúa como **auditor técnico de continuidad**: define invariantes, chequeos y procedimientos para detectar inconsistencias entre ejecuciones.

### 2) Contexto autosuficiente del sistema

- El proyecto se ejecuta por subproyectos, y se debe evitar degradación progresiva.
    
- Existen invariantes: layout repo, nombres docker services, llaves YAML, contrato `/query`, prefijos Redis, colección por RAG.
    
- Operación: reproducible, auditable, sin asumir memoria previa.
    

### 3) Objetivo técnico único del subproyecto

Crear un “paquete” de verificación:

- Checklist operacional
    
- Script de verificación (solo lectura) que valide estructura y archivos esperados
    
- Éxito binario: un comando (humano) produce salida OK/FAIL con lista de diferencias.
    

### 4) Reglas estrictas de implementación

- Permitido: script Python de solo lectura (`scripts/verify_state.py`) que no modifica nada.
    
- Prohibido: autocorrección automática.
    
- Debe fallar explícitamente si falta algo crítico.
    

### 5) Artefactos esperados

- `docs/state_management.md`
    
- `scripts/verify_state.py`
    
- `scripts/state_expected.json` (o YAML) con invariantes
    

### 6) Generación del PROMPT EJECUTABLE EN IDE (CRÍTICO)

**PROMPT EJECUTABLE EN IDE:**

```text
ROL (modelo ligero):
- Crear documentación y un script verificador SOLO LECTURA. No modificar archivos del proyecto.

REGLA CRÍTICA:
El modelo NO debe ejecutar comandos.
El humano ejecutará los comandos manualmente.

CREAR:
- docs/state_management.md
- scripts/state_expected.json
- scripts/verify_state.py

scripts/state_expected.json debe listar:
- required_paths: [lista de archivos/carpetas críticas]
- docker_invariants: nombres de servicios esperados
- api_invariants: endpoint /query schema (descrito textual, o archivos que deben existir)
- config_invariants: llaves mínimas esperadas en YAML ejemplo
- redis_invariants: prefijos de keys documentados

scripts/verify_state.py:
- Lee state_expected.json
- Verifica existencia de required_paths
- Verifica que docker-compose contiene servicios esperados (parseo simple de texto si no se agrega yaml parser)
- Verifica que docs/configuration.md existe
- Imprime:
  - "STATE_OK" si todo cumple
  - "STATE_FAIL" + lista de faltantes/incumplimientos si no

VALIDACIÓN (humano):
- python scripts/verify_state.py
- Debe imprimir STATE_OK cuando todo está correcto.

PUNTO DE ESPERA:
- Confirmación humana del resultado del verificador.
```

### 7) Validación y control de estado

- Validación humana: `STATE_OK`.
    
- Si `STATE_FAIL`: corregir faltantes y repetir hasta OK.
    
- Riesgos típicos: archivo movido, llave YAML renombrada, servicio docker renombrado.
    

### 8) Cierre del metaprompt

Congelar:

- Invariantes y verificador como “puerta” antes de cambios.  
    Habilita:
    
- Evolución futura (UI Vue más completa, auth, TLS real, mejoras PDF) sin perder control ni trazabilidad.