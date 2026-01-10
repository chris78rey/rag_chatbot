# 🔹 PROMPT EJECUTABLE — Subproyecto 4 de 10

## CLI de Ingestión (carpetas → colas Redis → worker)

---

## ROL DEL MODELO

Actúa como **editor mecánico**: crear documentación + esqueletos de archivos Python con docstrings. No implementar lógica real.

---

## REGLA CRÍTICA

> ⚠️ **El modelo NO debe ejecutar comandos.**  
> **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO DEL SISTEMA

- Ingestión no debe bloquear consultas.
- Ingestión se ejecuta por CLI obligatoria (comandos).
- Worker procesa tareas pesadas: lectura PDF, chunking, embeddings, upsert a Qdrant.
- Redis hace de broker (cola) y también caché/estado.
- PDFs deben "entenderse bien" (mejor loader + extracción robusta; sin OCR en MVP).

---

## OBJETIVO

Definir comandos, estructura de carpetas de fuentes por RAG y contrato de mensajes en la cola.

**Éxito binario:** existe `services/ingest/cli.md` + `services/ingest/queue_contract.md` + estructura de fuentes documentada.

---

## ARCHIVOS A CREAR/MODIFICAR

```
data/sources/README.md
services/ingest/README.md
services/ingest/cli.md
services/ingest/queue_contract.md
services/ingest/app.py
services/ingest/worker.py
services/ingest/cli.py
```

---

## CONTENIDO OBLIGATORIO

### `data/sources/README.md`

Debe documentar:
- **Estructura de carpetas:**
  ```
  data/sources/<rag_id>/
  ├── incoming/    # Archivos pendientes de procesar
  ├── processed/   # Archivos ya procesados exitosamente
  └── failed/      # Archivos que fallaron en el procesamiento
  ```
- **Regla:** Solo la CLI mueve/gestiona archivos entre carpetas
- **Formatos soportados:** PDF, TXT (otros en futuro)

---

### `services/ingest/queue_contract.md`

Debe definir:

1. **Cola Redis:**
   - Key name: `rag:ingest:queue`
   - Tipo: LIST (LPUSH/BRPOP)

2. **Mensaje JSON:**
   ```json
   {
     "job_id": "uuid-v4",
     "rag_id": "string",
     "source_path": "data/sources/<rag_id>/incoming/archivo.pdf",
     "source_type": "pdf|txt",
     "submitted_at": "ISO8601 timestamp",
     "options": {
       "reindex": false
     }
   }
   ```

3. **Estados por job:**
   - Key pattern: `rag:job:<job_id>:status`
   - Valores posibles: `queued`, `processing`, `done`, `failed`
   - Metadata adicional en: `rag:job:<job_id>:meta` (JSON con error_message, processed_at, etc.)

---

### `services/ingest/cli.md`

Comandos propuestos (documentados):

1. **Submit (encolar archivos):**
   ```bash
   python -m services.ingest.cli submit --rag <rag_id> --path data/sources/<rag_id>/incoming
   ```
   - Escanea carpeta `incoming`
   - Encola cada archivo como job
   - Imprime job_ids generados

2. **Reindex (reindexar RAG completo):**
   ```bash
   python -m services.ingest.cli reindex --rag <rag_id>
   ```
   - Borra colección en Qdrant y recrea
   - Encola todos los archivos de `processed` con `reindex=true`

3. **Status (consultar estado de job):**
   ```bash
   python -m services.ingest.cli status --job <job_id>
   ```
   - Consulta Redis y muestra estado actual

4. **List (listar jobs pendientes):**
   ```bash
   python -m services.ingest.cli list --rag <rag_id>
   ```
   - Muestra jobs en cola para ese RAG

**Nota:** El worker consume la cola de forma independiente y escribe logs a stdout/stderr.

---

### `services/ingest/README.md`

Debe incluir:
- Propósito del servicio de ingestión
- Arquitectura: CLI → Redis Queue → Worker → Qdrant
- Dependencias requeridas
- Cómo ejecutar el worker
- Referencia a `cli.md` y `queue_contract.md`

---

### Archivos Python (solo esqueletos con docstrings)

#### `services/ingest/app.py`
```python
"""
Módulo principal del servicio de ingestión.

Responsabilidades:
- Inicializar conexiones (Redis, Qdrant)
- Cargar configuración del cliente y RAGs
- Punto de entrada común para CLI y Worker

Funciones esperadas:
- init_app() -> AppContext
- get_rag_config(rag_id: str) -> RagConfig
- get_redis_client() -> Redis
- get_qdrant_client() -> QdrantClient
"""

# TODO: Implementar en subproyectos posteriores
```

#### `services/ingest/worker.py`
```python
"""
Worker de ingestión que consume jobs de la cola Redis.

Responsabilidades:
- Escuchar cola rag:ingest:queue (BRPOP)
- Procesar cada job:
  1. Actualizar estado a 'processing'
  2. Leer archivo según source_type (PDF/TXT)
  3. Aplicar chunking según config del RAG
  4. Generar embeddings
  5. Upsert chunks a Qdrant
  6. Mover archivo a 'processed' o 'failed'
  7. Actualizar estado a 'done' o 'failed'

Funciones esperadas:
- run_worker() -> None (loop infinito)
- process_job(job: dict) -> bool
- read_source(path: str, source_type: str) -> str
- chunk_text(text: str, rag_config: RagConfig) -> list[str]
- generate_embeddings(chunks: list[str], rag_config: RagConfig) -> list[list[float]]
- upsert_to_qdrant(rag_id: str, chunks: list, embeddings: list) -> None
- move_file(source: str, destination_dir: str) -> None
- update_job_status(job_id: str, status: str, meta: dict = None) -> None
"""

# TODO: Implementar en subproyectos posteriores
```

#### `services/ingest/cli.py`
```python
"""
CLI para gestión de ingestión de documentos.

Comandos:
- submit: Encola archivos de una carpeta para procesamiento
- reindex: Reindexar completamente un RAG
- status: Consultar estado de un job específico
- list: Listar jobs pendientes de un RAG

Uso:
    python -m services.ingest.cli <comando> [opciones]

Funciones esperadas:
- main() -> None (entry point con argparse/click)
- cmd_submit(rag_id: str, path: str) -> None
- cmd_reindex(rag_id: str) -> None
- cmd_status(job_id: str) -> None
- cmd_list(rag_id: str) -> None
- enqueue_file(rag_id: str, file_path: str, options: dict) -> str (job_id)
"""

# TODO: Implementar en subproyectos posteriores

if __name__ == "__main__":
    # main()
    pass
```

---

## VALIDACIÓN (humano ejecuta)

1. Verificar que existen todos los archivos listados
2. Revisar coherencia entre:
   - Rutas documentadas en `data/sources/README.md`
   - Contrato de cola en `queue_contract.md`
   - Comandos CLI en `cli.md`
3. Confirmar que los docstrings describen responsabilidades claras

---

## PUNTO DE ESPERA

⏸️ **DETENERSE** y solicitar confirmación humana de que:
- [ ] El contrato de cola está completo y coherente
- [ ] Los comandos CLI cubren los casos de uso necesarios
- [ ] La estructura de carpetas incoming/processed/failed es clara

---

## QUÉ SE CONGELA AL COMPLETAR

- ✅ Contrato de mensajes en cola Redis
- ✅ Rutas de fuentes por RAG: `data/sources/<rag_id>/`
- ✅ Comandos CLI documentados

## QUÉ SE HABILITA PARA EL SIGUIENTE SUBPROYECTO

- ➡️ Implementar API de consulta y servicio FastAPI (Subproyecto 5)