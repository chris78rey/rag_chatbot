# 🔹 PROMPT EJECUTABLE 12 — Config Loader + Procesador PDF

> **Archivo**: `specs/prompts/12_config_loader_pdf.md`  
> **Subproyecto**: 12 de 13 (adicional)  
> **Prerequisitos**: Subproyectos 1-11 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Implementar cargador de configuración YAML en runtime
- Implementar procesador real de PDFs usando PyPDF2/pdfplumber
- No cambiar contratos existentes
- No rediseñar arquitectura

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- Los archivos YAML de configuración ya existen (Subproyecto 3)
- El worker de ingestión necesita leer PDFs reales
- La API necesita cargar configs de cliente y RAG en runtime
- Actualmente todo usa valores hardcodeados o placeholders

---

## OBJETIVO

1. Implementar `config.py` que carga y valida YAML en runtime
2. Implementar procesador PDF real en el worker
3. Integrar config loader en toda la aplicación

**Éxito binario**: 
- La API carga configuración desde YAML al iniciar
- El worker procesa PDFs reales y extrae texto

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/config.py           # CREAR
services/ingest/pdf_processor.py     # CREAR
services/ingest/worker.py            # MODIFICAR
services/api/app/main.py             # MODIFICAR
services/api/requirements.txt        # MODIFICAR
services/ingest/requirements.txt     # CREAR
```

---

## CONTENIDO DE ARCHIVOS

### services/api/app/config.py

```python
"""
Cargador de configuración YAML para cliente y RAGs.

Carga:
- configs/client/client.yaml -> configuración global
- configs/rags/<rag_id>.yaml -> configuración por RAG

Implementa caché en memoria con recarga opcional.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import threading

# Lock para thread-safety en recarga
_config_lock = threading.Lock()

# Cache de configuraciones
_client_config: Optional[Dict[str, Any]] = None
_rag_configs: Dict[str, Dict[str, Any]] = {}

# Rutas base
CONFIG_BASE_DIR = os.environ.get("CONFIG_DIR", "configs")
CLIENT_CONFIG_PATH = os.environ.get(
    "CLIENT_CONFIG_PATH", 
    os.path.join(CONFIG_BASE_DIR, "client", "client.yaml")
)
RAGS_CONFIG_DIR = os.environ.get(
    "RAGS_CONFIG_DIR",
    os.path.join(CONFIG_BASE_DIR, "rags")
)


class ConfigError(Exception):
    """Error en carga o validación de configuración."""
    pass


def load_yaml_file(path: str) -> Dict[str, Any]:
    """
    Carga un archivo YAML.
    
    Args:
        path: Ruta al archivo YAML
    
    Returns:
        Dict con contenido del YAML
    
    Raises:
        ConfigError: Si el archivo no existe o es inválido
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")


def get_client_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Obtiene la configuración del cliente.
    
    Args:
        force_reload: Si True, recarga desde disco
    
    Returns:
        Dict con configuración del cliente
    """
    global _client_config
    
    with _config_lock:
        if _client_config is None or force_reload:
            # Intentar cargar client.yaml, si no existe usar .example
            config_path = CLIENT_CONFIG_PATH
            if not os.path.exists(config_path):
                example_path = config_path + ".example"
                if os.path.exists(example_path):
                    config_path = example_path
                else:
                    raise ConfigError(f"No client config found at {CLIENT_CONFIG_PATH}")
            
            _client_config = load_yaml_file(config_path)
            _apply_env_overrides(_client_config)
        
        return _client_config


def get_rag_config(rag_id: str, force_reload: bool = False) -> Dict[str, Any]:
    """
    Obtiene la configuración de un RAG específico.
    
    Args:
        rag_id: ID del RAG
        force_reload: Si True, recarga desde disco
    
    Returns:
        Dict con configuración del RAG
    
    Raises:
        ConfigError: Si el RAG no existe
    """
    global _rag_configs
    
    with _config_lock:
        if rag_id not in _rag_configs or force_reload:
            rag_path = os.path.join(RAGS_CONFIG_DIR, f"{rag_id}.yaml")
            
            if not os.path.exists(rag_path):
                raise ConfigError(f"RAG config not found: {rag_id}")
            
            _rag_configs[rag_id] = load_yaml_file(rag_path)
        
        return _rag_configs[rag_id]


def list_available_rags() -> list:
    """
    Lista todos los RAGs disponibles.
    
    Returns:
        Lista de rag_ids
    """
    rags = []
    rags_dir = Path(RAGS_CONFIG_DIR)
    
    if rags_dir.exists():
        for file in rags_dir.glob("*.yaml"):
            if not file.name.startswith("_"):  # Ignorar archivos que empiecen con _
                rags.append(file.stem)
    
    return sorted(rags)


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """
    Aplica overrides desde variables de entorno.
    
    Convención: RAG_<SECTION>_<KEY>=value
    Ejemplo: RAG_QDRANT_URL=http://localhost:6333
    """
    env_prefix = "RAG_"
    
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            parts = key[len(env_prefix):].lower().split("_", 1)
            if len(parts) == 2:
                section, subkey = parts
                if section in config and isinstance(config[section], dict):
                    # Intentar convertir a tipo apropiado
                    config[section][subkey] = _convert_value(value)


def _convert_value(value: str) -> Any:
    """Convierte string a tipo apropiado."""
    # Booleanos
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    
    # Números
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


def reload_all_configs() -> None:
    """Recarga todas las configuraciones desde disco."""
    global _client_config, _rag_configs
    
    with _config_lock:
        _client_config = None
        _rag_configs = {}
    
    # Forzar recarga
    get_client_config(force_reload=True)


def validate_rag_config(config: Dict[str, Any]) -> list:
    """
    Valida que un config de RAG tenga campos requeridos.
    
    Returns:
        Lista de errores (vacía si todo OK)
    """
    errors = []
    required_fields = ["rag_id", "collection_name"]
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validar embeddings
    if "embeddings" in config:
        emb = config["embeddings"]
        if "dim" not in emb:
            errors.append("embeddings.dim is required")
    
    return errors


# Helpers para acceso rápido a config común
def get_qdrant_url() -> str:
    """Obtiene URL de Qdrant desde config."""
    config = get_client_config()
    return config.get("qdrant", {}).get("url", "http://localhost:6333")


def get_redis_url() -> str:
    """Obtiene URL de Redis desde config."""
    config = get_client_config()
    return config.get("redis", {}).get("url", "redis://localhost:6379/0")


def get_llm_config() -> Dict[str, Any]:
    """Obtiene configuración de LLM."""
    config = get_client_config()
    return config.get("llm", {})


def get_cache_config() -> Dict[str, Any]:
    """Obtiene configuración de caché."""
    config = get_client_config()
    return config.get("cache", {"enabled": True, "ttl_seconds": 300})


def get_session_config() -> Dict[str, Any]:
    """Obtiene configuración de sesiones."""
    config = get_client_config()
    return config.get("sessions", {"enabled": True, "ttl_seconds": 1800})
```

---

### services/ingest/pdf_processor.py

```python
"""
Procesador de archivos PDF.

Extrae texto de PDFs usando PyPDF2 (básico) o pdfplumber (mejor para tablas).
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Intentar importar pdfplumber primero (mejor calidad)
try:
    import pdfplumber
    PDF_BACKEND = "pdfplumber"
except ImportError:
    pdfplumber = None
    PDF_BACKEND = None

# Fallback a PyPDF2
try:
    import PyPDF2
    if PDF_BACKEND is None:
        PDF_BACKEND = "pypdf2"
except ImportError:
    PyPDF2 = None

if PDF_BACKEND is None:
    raise ImportError("Se requiere pdfplumber o PyPDF2. Instalar: pip install pdfplumber")


@dataclass
class PDFPage:
    """Representa una página extraída de un PDF."""
    page_number: int
    text: str
    metadata: Dict[str, Any]


@dataclass 
class PDFDocument:
    """Representa un documento PDF procesado."""
    path: str
    filename: str
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict[str, Any]
    
    @property
    def full_text(self) -> str:
        """Retorna todo el texto concatenado."""
        return "\n\n".join(page.text for page in self.pages if page.text)


class PDFProcessorError(Exception):
    """Error en procesamiento de PDF."""
    pass


def extract_text_pdfplumber(path: str) -> PDFDocument:
    """
    Extrae texto usando pdfplumber (mejor para tablas y layouts complejos).
    """
    pages = []
    metadata = {}
    
    try:
        with pdfplumber.open(path) as pdf:
            metadata = {
                "total_pages": len(pdf.pages),
                "metadata": pdf.metadata or {}
            }
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # Limpiar texto
                text = _clean_text(text)
                
                pages.append(PDFPage(
                    page_number=i + 1,
                    text=text,
                    metadata={
                        "width": page.width,
                        "height": page.height
                    }
                ))
    except Exception as e:
        raise PDFProcessorError(f"Error processing PDF with pdfplumber: {e}")
    
    return PDFDocument(
        path=path,
        filename=Path(path).name,
        total_pages=len(pages),
        pages=pages,
        metadata=metadata
    )


def extract_text_pypdf2(path: str) -> PDFDocument:
    """
    Extrae texto usando PyPDF2 (básico pero confiable).
    """
    pages = []
    metadata = {}
    
    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            metadata = {
                "total_pages": len(reader.pages),
                "metadata": dict(reader.metadata) if reader.metadata else {}
            }
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = _clean_text(text)
                
                pages.append(PDFPage(
                    page_number=i + 1,
                    text=text,
                    metadata={}
                ))
    except Exception as e:
        raise PDFProcessorError(f"Error processing PDF with PyPDF2: {e}")
    
    return PDFDocument(
        path=path,
        filename=Path(path).name,
        total_pages=len(pages),
        pages=pages,
        metadata=metadata
    )


def extract_text(path: str, backend: Optional[str] = None) -> PDFDocument:
    """
    Extrae texto de un PDF usando el backend disponible.
    
    Args:
        path: Ruta al archivo PDF
        backend: "pdfplumber", "pypdf2" o None (auto)
    
    Returns:
        PDFDocument con texto extraído
    """
    if not os.path.exists(path):
        raise PDFProcessorError(f"File not found: {path}")
    
    # Seleccionar backend
    use_backend = backend or PDF_BACKEND
    
    if use_backend == "pdfplumber" and pdfplumber:
        return extract_text_pdfplumber(path)
    elif use_backend == "pypdf2" and PyPDF2:
        return extract_text_pypdf2(path)
    else:
        raise PDFProcessorError(f"Backend not available: {use_backend}")


def _clean_text(text: str) -> str:
    """
    Limpia texto extraído de PDF.
    
    - Normaliza espacios
    - Elimina caracteres de control
    - Mantiene saltos de línea significativos
    """
    if not text:
        return ""
    
    # Reemplazar múltiples espacios por uno
    import re
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Reemplazar múltiples saltos de línea por máximo 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Eliminar espacios al inicio/final de líneas
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def get_pdf_info(path: str) -> Dict[str, Any]:
    """
    Obtiene información básica de un PDF sin extraer todo el texto.
    """
    if PDF_BACKEND == "pdfplumber" and pdfplumber:
        with pdfplumber.open(path) as pdf:
            return {
                "total_pages": len(pdf.pages),
                "metadata": pdf.metadata or {},
                "backend": "pdfplumber"
            }
    elif PyPDF2:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return {
                "total_pages": len(reader.pages),
                "metadata": dict(reader.metadata) if reader.metadata else {},
                "backend": "pypdf2"
            }
    
    raise PDFProcessorError("No PDF backend available")


# Información del backend activo
def get_backend_info() -> Dict[str, Any]:
    """Retorna información sobre el backend de PDF activo."""
    return {
        "active_backend": PDF_BACKEND,
        "pdfplumber_available": pdfplumber is not None,
        "pypdf2_available": PyPDF2 is not None
    }
```

---

### services/ingest/requirements.txt

```
# Dependencias del servicio de ingestión

# Redis client
redis>=4.5.0

# PDF processing (instalar al menos uno)
pdfplumber>=0.10.0
PyPDF2>=3.0.0

# Qdrant client
qdrant-client>=1.7.0

# YAML config
pyyaml>=6.0

# HTTP client (para embeddings)
httpx>=0.26.0

# Utilidades
python-dotenv>=1.0.0
```

---

### services/ingest/worker.py (MODIFICAR - versión completa)

```python
"""
Worker de ingestión que consume jobs de la cola Redis.

Procesa PDFs y TXTs reales, genera embeddings y hace upsert a Qdrant.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import redis
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Imports locales
from pdf_processor import extract_text, PDFProcessorError


# Configuración desde environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "https://api.openai.com/v1/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# Queue keys
QUEUE_KEY = "rag:ingest:queue"
JOB_STATUS_PREFIX = "rag:job:"


def get_redis_client():
    """Obtiene cliente Redis."""
    return redis.from_url(REDIS_URL, decode_responses=True)


def get_qdrant_client():
    """Obtiene cliente Qdrant."""
    return QdrantClient(url=QDRANT_URL)


def update_job_status(redis_client, job_id: str, status: str, meta: dict = None):
    """Actualiza estado de un job en Redis."""
    redis_client.set(f"{JOB_STATUS_PREFIX}{job_id}:status", status)
    if meta:
        redis_client.set(f"{JOB_STATUS_PREFIX}{job_id}:meta", json.dumps(meta))
    # TTL de 24 horas para estado de jobs
    redis_client.expire(f"{JOB_STATUS_PREFIX}{job_id}:status", 86400)
    if meta:
        redis_client.expire(f"{JOB_STATUS_PREFIX}{job_id}:meta", 86400)


def read_source(path: str, source_type: str) -> str:
    """
    Lee contenido de un archivo fuente.
    
    Args:
        path: Ruta al archivo
        source_type: "pdf" o "txt"
    
    Returns:
        Texto extraído
    """
    if source_type == "pdf":
        doc = extract_text(path)
        return doc.full_text
    else:
        # TXT u otros formatos de texto plano
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()


def chunk_text(
    text: str, 
    chunk_size: int = 500, 
    chunk_overlap: int = 50,
    splitter: str = "recursive"
) -> List[Dict[str, Any]]:
    """
    Divide texto en chunks.
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño máximo de cada chunk
        chunk_overlap: Solapamiento entre chunks
        splitter: Tipo de splitter ("recursive", "character")
    
    Returns:
        Lista de dicts con {text, start_char, end_char}
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    
    if splitter == "recursive":
        # Splitter recursivo: intenta dividir por párrafos, luego oraciones, luego caracteres
        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks = _recursive_split(text, separators, chunk_size, chunk_overlap)
    else:
        # Splitter simple por caracteres
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text.strip(),
                    "start_char": start,
                    "end_char": min(end, len(text))
                })
            
            start = end - chunk_overlap
    
    return chunks


def _recursive_split(
    text: str, 
    separators: List[str], 
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict[str, Any]]:
    """Implementación de splitter recursivo."""
    chunks = []
    
    if len(text) <= chunk_size:
        if text.strip():
            return [{"text": text.strip(), "start_char": 0, "end_char": len(text)}]
        return []
    
    # Encontrar el mejor separador
    separator = separators[0] if separators else ""
    
    if separator:
        parts = text.split(separator)
    else:
        # Sin separador, dividir por tamaño
        parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
    
    current_chunk = ""
    current_start = 0
    char_pos = 0
    
    for part in parts:
        if len(current_chunk) + len(part) + len(separator) <= chunk_size:
            if current_chunk:
                current_chunk += separator
            current_chunk += part
        else:
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "start_char": current_start,
                    "end_char": char_pos
                })
            current_start = max(0, char_pos - chunk_overlap)
            current_chunk = part
        
        char_pos += len(part) + len(separator)
    
    # Último chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "start_char": current_start,
            "end_char": len(text)
        })
    
    return chunks


def generate_embeddings_api(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings usando API externa (OpenAI compatible).
    
    Requiere OPENAI_API_KEY o OPENROUTER_API_KEY en environment.
    """
    import httpx
    
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY or OPENROUTER_API_KEY required for embeddings")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Procesar en batches
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        payload = {
            "model": EMBEDDING_MODEL,
            "input": batch
        }
        
        with httpx.Client(timeout=60) as client:
            response = client.post(EMBEDDING_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            batch_embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_embeddings)
    
    return all_embeddings


def generate_embeddings_dummy(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings dummy para testing.
    Usar solo si no hay API de embeddings disponible.
    """
    import hashlib
    import random
    
    vectors = []
    for text in texts:
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        random.seed(hash_val)
        vectors.append([random.uniform(-1, 1) for _ in range(EMBEDDING_DIM)])
    return vectors


def generate_embeddings(texts: List[str], use_api: bool = True) -> List[List[float]]:
    """
    Genera embeddings para una lista de textos.
    
    Args:
        texts: Lista de textos
        use_api: Si True, usa API; si False, usa dummy
    """
    if not texts:
        return []
    
    if use_api:
        try:
            return generate_embeddings_api(texts)
        except Exception as e:
            print(f"[Worker] Warning: API embeddings failed ({e}), using dummy")
            return generate_embeddings_dummy(texts)
    else:
        return generate_embeddings_dummy(texts)


def ensure_collection(qdrant_client: QdrantClient, collection_name: str, vector_dim: int):
    """Crea colección si no existe."""
    collections = qdrant_client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if not exists:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim,
                distance=models.Distance.COSINE
            )
        )
        print(f"[Worker] Created collection: {collection_name}")


def upsert_chunks(
    qdrant_client: QdrantClient,
    collection_name: str,
    chunks: List[Dict],
    vectors: List[List[float]],
    source_path: str
) -> int:
    """
    Inserta chunks en Qdrant.
    
    Returns:
        Número de puntos insertados
    """
    points = []
    
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point_id = str(uuid.uuid4())
        
        points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "text": chunk["text"],
                "source_path": source_path,
                "chunk_index": i,
                "start_char": chunk.get("start_char", 0),
                "end_char": chunk.get("end_char", 0)
            }
        ))
    
    if points:
        qdrant_client.upsert(collection_name=collection_name, points=points)
    
    return len(points)


def move_file(source: Path, dest_dir: Path) -> Path:
    """Mueve archivo a directorio destino."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / source.name
    
    # Si ya existe, añadir timestamp
    if dest.exists():
        timestamp = int(time.time())
        dest = dest_dir / f"{source.stem}_{timestamp}{source.suffix}"
    
    source.rename(dest)
    return dest


def process_job(job: dict) -> bool:
    """
    Procesa un job de ingestión.
    
    1. Leer archivo (PDF o TXT)
    2. Dividir en chunks
    3. Generar embeddings
    4. Upsert a Qdrant
    5. Mover archivo a processed/failed
    """
    job_id = job["job_id"]
    rag_id = job["rag_id"]
    source_path = Path(job["source_path"])
    source_type = job.get("source_type", "txt").lower()
    options = job.get("options", {})
    
    redis_client = get_redis_client()
    qdrant_client = get_qdrant_client()
    
    update_job_status(redis_client, job_id, "processing")
    print(f"[Worker] Processing job {job_id}: {source_path}")
    
    try:
        # 1. Verificar que el archivo existe
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # 2. Leer archivo
        print(f"[Worker] Reading {source_type.upper()}: {source_path}")
        text = read_source(str(source_path), source_type)
        print(f"[Worker] Extracted {len(text)} characters")
        
        if not text.strip():
            raise ValueError("No text extracted from file")
        
        # 3. Chunking
        # TODO: Cargar config de chunking desde RAG config
        chunk_size = options.get("chunk_size", 500)
        chunk_overlap = options.get("chunk_overlap", 50)
        
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        print(f"[Worker] Created {len(chunks)} chunks")
        
        if not chunks:
            raise ValueError("No chunks created from text")
        
        # 4. Generar embeddings
        print(f"[Worker] Generating embeddings...")
        use_api = os.getenv("USE_EMBEDDING_API", "true").lower() == "true"
        chunk_texts = [c["text"] for c in chunks]
        vectors = generate_embeddings(chunk_texts, use_api=use_api)
        print(f"[Worker] Generated {len(vectors)} embeddings")
        
        # 5. Asegurar colección existe
        collection_name = f"{rag_id}_collection"
        ensure_collection(qdrant_client, collection_name, EMBEDDING_DIM)
        
        # 6. Upsert a Qdrant
        print(f"[Worker] Upserting to Qdrant...")
        num_inserted = upsert_chunks(
            qdrant_client,
            collection_name,
            chunks,
            vectors,
            str(source_path)
        )
        print(f"[Worker] Inserted {num_inserted} points")
        
        # 7. Mover archivo a processed
        processed_dir = source_path.parent.parent / "processed"
        new_path = move_file(source_path, processed_dir)
        print(f"[Worker] Moved to {new_path}")
        
        # 8. Actualizar estado
        update_job_status(redis_client, job_id, "done", {
            "chunks": len(chunks),
            "collection": collection_name,
            "processed_path": str(new_path)
        })
        
        print(f"[Worker] ✅ Job {job_id} completed successfully")
        return True
        
    except Exception as e:
        print(f"[Worker] ❌ Job {job_id} failed: {e}")
        
        update_job_status(redis_client, job_id, "failed", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        # Mover a failed
        try:
            if source_path.exists():
                failed_dir = source_path.parent.parent / "failed"
                move_file(source_path, failed_dir)
        except Exception as move_error:
            print(f"[Worker] Could not move to failed: {move_error}")
        
        return False


def run_worker():
    """Loop principal del worker."""
    print("=" * 60)
    print("[Worker] Starting ingest worker...")
    print(f"[Worker] Redis: {REDIS_URL}")
    print(f"[Worker] Qdrant: {QDRANT_URL}")
    print(f"[Worker] Embedding model: {EMBEDDING_MODEL}")
    print(f"[Worker] Embedding dim: {EMBEDDING_DIM}")
    print("=" * 60)
    
    redis_client = get_redis_client()
    
    # Verificar conexión
    try:
        redis_client.ping()
        print("[Worker] ✅ Redis connected")
    except Exception as e:
        print(f"[Worker] ❌ Redis connection failed: {e}")
        return
    
    try:
        qdrant = get_qdrant_client()
        qdrant.get_collections()
        print("[Worker] ✅ Qdrant connected")
    except Exception as e:
        print(f"[Worker] ❌ Qdrant connection failed: {e}")
        return
    
    print(f"[Worker] Listening on queue: {QUEUE_KEY}")
    print("-" * 60)
    
    while True:
        try:
            # Esperar job (blocking con timeout)
            result = redis_client.brpop(QUEUE_KEY, timeout=5)
            
            if result:
                _, job_data = result
                job = json.loads(job_data)
                print(f"\n[Worker] 📥 Job received: {job.get('job_id', 'unknown')}")
                process_job(job)
                print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n[Worker] Stopped by user")
            break
        except json.JSONDecodeError as e:
            print(f"[Worker] Invalid job JSON: {e}")
        except Exception as e:
            print(f"[Worker] Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
```

---

### Modificar services/api/requirements.txt

Añadir:

```
# Configuración
pyyaml>=6.0
```

---

### Modificar services/api/app/main.py

```python
"""
FastAPI main application.
Con carga de configuración al inicio.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import health, query, metrics
from app.config import get_client_config, reload_all_configs, list_available_rags
from app.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja startup y shutdown de la aplicación."""
    # Startup
    print("=" * 60)
    print("[API] Starting RAG On-Premise API...")
    
    try:
        config = get_client_config()
        print(f"[API] ✅ Config loaded")
        print(f"[API]    - Qdrant: {config.get('qdrant', {}).get('url', 'not set')}")
        print(f"[API]    - Redis: {config.get('redis', {}).get('url', 'not set')}")
        print(f"[API]    - LLM Provider: {config.get('llm', {}).get('provider', 'not set')}")
    except Exception as e:
        print(f"[API] ⚠️ Config load warning: {e}")
    
    rags = list_available_rags()
    print(f"[API] Available RAGs: {rags if rags else 'none'}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("[API] Shutting down...")
    await close_redis()


app = FastAPI(
    title="RAG On-Premise API",
    description="API de consultas RAG multi-tenant",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(health.router, tags=["Health"])
app.include_router(query.router, tags=["Query"])
app.include_router(metrics.router, tags=["Metrics"])


@app.get("/config/reload", tags=["Config"])
async def reload_config():
    """Recarga configuración desde disco (admin)."""
    reload_all_configs()
    return {"status": "reloaded"}


@app.get("/config/rags", tags=["Config"])
async def list_rags():
    """Lista RAGs disponibles."""
    return {"rags": list_available_rags()}
```

---

## VALIDACIÓN (humano ejecuta)

```bash
# 1. Crear un client.yaml real (copiar de example)
cp configs/client/client.yaml.example configs/client/client.yaml

# 2. Crear un RAG de prueba
cp configs/rags/example_rag.yaml configs/rags/test_rag.yaml

# 3. Rebuild servicios
docker compose -f deploy/compose/docker-compose.yml build api ingest-worker

# 4. Reiniciar
docker compose -f deploy/compose/docker-compose.yml up -d

# 5. Verificar que la API carga config
docker compose logs api | grep "Config loaded"

# 6. Listar RAGs disponibles
curl http://localhost/api/config/rags

# 7. Probar con un PDF real
# Colocar un PDF en data/sources/test_rag/incoming/
# Ejecutar CLI de ingestión
python -m services.ingest.cli submit --rag test_rag

# 8. Ver logs del worker
docker compose logs -f ingest-worker
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] La API carga configuración desde YAML al iniciar
- [ ] `/config/rags` lista los RAGs disponibles
- [ ] El worker procesa PDFs reales y extrae texto
- [ ] Los chunks se insertan en Qdrant correctamente

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| Config file not found | No existe client.yaml | Copiar de .example |
| No PDF backend | Falta pdfplumber/PyPDF2 | pip install pdfplumber |
| Embedding API failed | API key no configurada | Setear OPENAI_API_KEY |
| Empty text from PDF | PDF es imagen/escaneado | Necesita OCR (no MVP) |

---

## LO QUE SE CONGELA

✅ Cargador de configuración YAML  
✅ Procesador de PDFs  
✅ Integración de config en toda la app

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 13**: Tests básicos end-to-end