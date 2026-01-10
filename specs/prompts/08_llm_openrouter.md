# 🔹 PROMPT EJECUTABLE 08 — Integración OpenRouter (LLM) + Fallback + Prompts por RAG

> **Archivo**: `specs/prompts/08_llm_openrouter.md`  
> **Subproyecto**: 8 de 10  
> **Prerequisitos**: Subproyectos 1-7 completados

---

## ROL DEL MODELO

Actúa como **editor mecánico**:
- Implementar cliente OpenRouter y prompting por plantillas
- No cambiar contratos existentes de `/query`
- No hardcodear modelos: deben venir de configuración

---

## REGLA CRÍTICA

⚠️ **El modelo NO debe ejecutar comandos.**  
⚠️ **El humano ejecutará los comandos manualmente.**

---

## CONTEXTO

- **Proveedor**: OpenRouter (API key por ENV)
- **Estrategia**: Modelo principal barato + fallback si falla
- **Prompts**: Configurables por archivo por RAG (templates)
- **Contexto**: top_k/chunks/tokens por RAG
- **Respuestas**: Deben incluir trazabilidad básica (latency_ms, etc.)

---

## OBJETIVO

Implementar llamada al LLM en `/query` usando contexto de Qdrant + templates por RAG, con fallback automático.

**Éxito binario**: `/query` devuelve `answer` generado; si se fuerza fallo del modelo principal, usa fallback.

---

## ARCHIVOS A CREAR/MODIFICAR

```
services/api/app/llm/
├── __init__.py
└── openrouter_client.py

services/api/app/prompting.py

configs/rags/prompts/
├── system_default.txt
└── user_default.txt

docs/llm.md
```

**Modificar:**
- `services/api/app/routes/query.py` (integrar LLM)
- `services/api/requirements.txt` (añadir httpx si no existe)

---

## CONTENIDO DE ARCHIVOS

### services/api/app/llm/__init__.py

```python
# LLM integration package
from .openrouter_client import call_chat_completion, OpenRouterError
```

### services/api/app/llm/openrouter_client.py

```python
"""
Cliente para OpenRouter API.
Maneja llamadas al LLM con reintentos y fallback.
"""
import os
import time
import httpx
from typing import List, Dict, Any, Optional

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Error en llamada a OpenRouter."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def call_chat_completion(
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: int = 30,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Llama a OpenRouter chat completion.
    
    Args:
        model: Nombre del modelo (ej: "openai/gpt-3.5-turbo")
        messages: Lista de mensajes [{"role": "system/user/assistant", "content": "..."}]
        max_tokens: Máximo de tokens en respuesta
        temperature: Temperatura del modelo
        timeout: Timeout en segundos
        max_retries: Número de reintentos ante error
    
    Returns:
        Dict con keys: content, model, usage, latency_ms
    
    Raises:
        OpenRouterError: Si falla después de reintentos
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY not set in environment")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "rag-onpremise",  # Requerido por OpenRouter
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    last_error = None
    start_time = time.time()
    
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "model": data.get("model", model),
                        "usage": data.get("usage", {}),
                        "latency_ms": latency_ms
                    }
                
                # Error de API
                error_msg = f"OpenRouter API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                
                last_error = OpenRouterError(error_msg, response.status_code)
                
                # No reintentar en errores 4xx (excepto 429)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise last_error
                    
        except httpx.TimeoutException:
            last_error = OpenRouterError(f"Timeout after {timeout}s", None)
        except httpx.RequestError as e:
            last_error = OpenRouterError(f"Request error: {str(e)}", None)
        
        # Esperar antes de reintentar (backoff simple)
        if attempt < max_retries:
            await asyncio.sleep(1 * (attempt + 1))
    
    raise last_error


async def call_with_fallback(
    primary_model: str,
    fallback_model: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: int = 30,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Llama al modelo principal, si falla usa fallback.
    
    Returns:
        Dict con keys: content, model, usage, latency_ms, used_fallback
    """
    try:
        result = await call_chat_completion(
            model=primary_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries
        )
        result["used_fallback"] = False
        return result
        
    except OpenRouterError as e:
        # Log del error (en producción usar logger apropiado)
        print(f"Primary model failed: {e.message}, trying fallback...")
        
        result = await call_chat_completion(
            model=fallback_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries
        )
        result["used_fallback"] = True
        return result


# Import necesario para asyncio.sleep
import asyncio
```

### services/api/app/prompting.py

```python
"""
Gestión de templates de prompts por RAG.
"""
import os
from typing import List, Dict, Optional
from functools import lru_cache

# Cache simple para templates (se recarga al reiniciar)
_template_cache: Dict[str, str] = {}


def load_template(path: str, base_dir: str = None) -> str:
    """
    Carga un template desde archivo.
    
    Args:
        path: Ruta relativa al template
        base_dir: Directorio base (default: configs/rags/)
    
    Returns:
        Contenido del template como string
    """
    if base_dir is None:
        base_dir = os.environ.get("RAGS_CONFIG_DIR", "configs/rags")
    
    full_path = os.path.join(base_dir, path)
    
    # Usar cache
    if full_path in _template_cache:
        return _template_cache[full_path]
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            _template_cache[full_path] = content
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Template not found: {full_path}")


def clear_template_cache():
    """Limpia la cache de templates."""
    _template_cache.clear()


def build_messages(
    system_template: str,
    user_template: str,
    question: str,
    context_chunks: List[Dict],
    session_history: Optional[List[Dict]] = None
) -> List[Dict[str, str]]:
    """
    Construye la lista de mensajes para el LLM.
    
    Args:
        system_template: Template del system prompt
        user_template: Template del user prompt
        question: Pregunta del usuario
        context_chunks: Lista de chunks recuperados [{text, source, score}]
        session_history: Historial de conversación [{role, content}]
    
    Returns:
        Lista de mensajes para OpenRouter API
    """
    messages = []
    
    # System message
    system_content = system_template
    messages.append({
        "role": "system",
        "content": system_content
    })
    
    # Historial de sesión (si existe)
    if session_history:
        for turn in session_history:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", "")
            })
    
    # Formatear contexto
    context_text = format_context(context_chunks)
    
    # User message con pregunta y contexto
    user_content = user_template.replace("{question}", question)
    user_content = user_content.replace("{context}", context_text)
    
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    return messages


def format_context(chunks: List[Dict]) -> str:
    """
    Formatea los chunks de contexto para el prompt.
    
    Args:
        chunks: Lista de chunks [{text, source, score}]
    
    Returns:
        String formateado con el contexto
    """
    if not chunks:
        return "[No se encontró contexto relevante]"
    
    formatted_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "desconocido")
        text = chunk.get("text", "")
        score = chunk.get("score", 0)
        
        formatted_parts.append(
            f"[Fuente {i}: {source} (relevancia: {score:.2f})]\n{text}"
        )
    
    return "\n\n---\n\n".join(formatted_parts)
```

### configs/rags/prompts/system_default.txt

```
Eres un asistente experto que responde preguntas basándose ÚNICAMENTE en el contexto proporcionado.

Reglas estrictas:
1. Solo usa información del contexto dado. No inventes ni asumas información.
2. Si el contexto no contiene información suficiente, di: "No tengo información suficiente en los documentos disponibles para responder esta pregunta."
3. Cita las fuentes cuando sea posible.
4. Sé conciso y directo en tus respuestas.
5. Mantén un tono profesional y neutral.
```

### configs/rags/prompts/user_default.txt

```
Contexto disponible:
{context}

---

Pregunta del usuario:
{question}

---

Responde basándote únicamente en el contexto proporcionado arriba.
```

### docs/llm.md

```markdown
# Integración LLM (OpenRouter)

## Descripción

El sistema utiliza OpenRouter como proveedor de LLM, permitiendo acceso a múltiples modelos (OpenAI, Anthropic, etc.) a través de una única API.

## Configuración

### Variables de entorno

```bash
OPENROUTER_API_KEY=sk-or-xxx  # API key de OpenRouter
```

### Configuración en client.yaml

```yaml
llm:
  provider: "openrouter"
  api_key_env_var: "OPENROUTER_API_KEY"
  default_model: "openai/gpt-3.5-turbo"
  fallback_model: "anthropic/claude-instant-v1"
  timeout_s: 30
  max_retries: 2
```

### Configuración por RAG

```yaml
prompting:
  system_template_path: "prompts/system_default.txt"
  user_template_path: "prompts/user_default.txt"
  max_tokens: 1024
  temperature: 0.7
```

## Estrategia de Fallback

1. Se intenta con `default_model`
2. Si falla (timeout, error de API, rate limit), se intenta con `fallback_model`
3. Si ambos fallan, se retorna el mensaje de error configurado en `errors.provider_error_message`

## Templates de Prompts

### Ubicación

```
configs/rags/prompts/
├── system_default.txt    # Prompt de sistema por defecto
└── user_default.txt      # Prompt de usuario por defecto
```

### Variables disponibles en user template

- `{question}`: Pregunta del usuario
- `{context}`: Contexto formateado de los chunks recuperados

### Crear templates personalizados por RAG

1. Crear archivos en `configs/rags/prompts/mi_rag_system.txt`
2. Actualizar `prompting.system_template_path` en el YAML del RAG

## Flujo de Consulta

```
1. Usuario envía pregunta
2. Retrieval en Qdrant → chunks
3. Cargar templates según config del RAG
4. build_messages(system, user, question, chunks, history)
5. call_with_fallback(primary, fallback, messages, ...)
6. Retornar respuesta
```

## Modelos Recomendados

### Producción (balance costo/calidad)
- Primary: `openai/gpt-3.5-turbo`
- Fallback: `anthropic/claude-instant-v1`

### Alta calidad
- Primary: `openai/gpt-4`
- Fallback: `anthropic/claude-2`

### Bajo costo
- Primary: `mistralai/mistral-7b-instruct`
- Fallback: `meta-llama/llama-2-13b-chat`

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| OPENROUTER_API_KEY not set | Variable no configurada | Añadir al .env |
| 401 Unauthorized | API key inválida | Verificar key en OpenRouter |
| 429 Rate Limited | Límite de requests | Esperar o cambiar modelo |
| Timeout | Modelo lento | Aumentar timeout_s o usar modelo más rápido |
```

---

## MODIFICAR: services/api/app/routes/query.py

```python
"""
Endpoint principal de consulta RAG.
Integrado con retrieval (Qdrant), cache (Redis), y LLM (OpenRouter).
"""
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse, ContextChunk
from app.retrieval import retrieve_context
from app.cache import get_cached_answer, set_cached_answer, build_cache_key
from app.rate_limit import check_rate_limit
from app.sessions import get_session_history, append_turn
from app.prompting import load_template, build_messages
from app.llm import call_with_fallback, OpenRouterError
from app.config import get_rag_config, get_client_config

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Procesa una consulta RAG completa:
    1. Rate limiting
    2. Check cache
    3. Retrieval de contexto
    4. Build prompts
    5. Call LLM con fallback
    6. Guardar en cache y sesión
    """
    start_time = time.time()
    
    # Cargar configs
    try:
        rag_config = get_rag_config(request.rag_id)
        client_config = get_client_config()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"RAG '{request.rag_id}' not found")
    
    # Rate limiting
    await check_rate_limit(request.rag_id)
    
    # Session ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # Check cache
    cache_key = build_cache_key(
        request.rag_id, 
        request.question,
        request.top_k or rag_config.get("retrieval", {}).get("top_k", 5)
    )
    
    cached = await get_cached_answer(cache_key)
    if cached:
        return QueryResponse(
            rag_id=request.rag_id,
            answer=cached["answer"],
            context_chunks=[ContextChunk(**c) for c in cached["context_chunks"]],
            latency_ms=int((time.time() - start_time) * 1000),
            cache_hit=True,
            session_id=session_id
        )
    
    # Retrieval
    top_k = request.top_k or rag_config.get("retrieval", {}).get("top_k", 5)
    context_chunks = await retrieve_context(request.rag_id, request.question, top_k)
    
    # Si no hay contexto
    if not context_chunks:
        no_context_msg = rag_config.get("errors", {}).get(
            "no_context_message",
            "No encontré información relevante para responder tu pregunta."
        )
        return QueryResponse(
            rag_id=request.rag_id,
            answer=no_context_msg,
            context_chunks=[],
            latency_ms=int((time.time() - start_time) * 1000),
            cache_hit=False,
            session_id=session_id
        )
    
    # Build prompts
    prompting_config = rag_config.get("prompting", {})
    system_template = load_template(
        prompting_config.get("system_template_path", "prompts/system_default.txt")
    )
    user_template = load_template(
        prompting_config.get("user_template_path", "prompts/user_default.txt")
    )
    
    # Get session history
    session_history = await get_session_history(session_id) if client_config.get("sessions", {}).get("enabled") else []
    
    # Build messages
    messages = build_messages(
        system_template=system_template,
        user_template=user_template,
        question=request.question,
        context_chunks=[{"text": c.text, "source": c.source, "score": c.score} for c in context_chunks],
        session_history=session_history
    )
    
    # Call LLM
    llm_config = client_config.get("llm", {})
    try:
        llm_response = await call_with_fallback(
            primary_model=llm_config.get("default_model", "openai/gpt-3.5-turbo"),
            fallback_model=llm_config.get("fallback_model", "anthropic/claude-instant-v1"),
            messages=messages,
            max_tokens=prompting_config.get("max_tokens", 1024),
            temperature=prompting_config.get("temperature", 0.7),
            timeout=llm_config.get("timeout_s", 30),
            max_retries=llm_config.get("max_retries", 2)
        )
        answer = llm_response["content"]
    except OpenRouterError as e:
        # Usar mensaje de error configurado
        answer = rag_config.get("errors", {}).get(
            "provider_error_message",
            "El servicio está temporalmente no disponible. Intenta de nuevo."
        )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Guardar en cache
    cache_ttl = rag_config.get("cache", {}).get("ttl_seconds", 300)
    if rag_config.get("cache", {}).get("enabled", True):
        await set_cached_answer(
            cache_key,
            {
                "answer": answer,
                "context_chunks": [c.dict() for c in context_chunks]
            },
            ttl=cache_ttl
        )
    
    # Guardar en sesión
    if client_config.get("sessions", {}).get("enabled"):
        await append_turn(session_id, request.question, answer)
    
    return QueryResponse(
        rag_id=request.rag_id,
        answer=answer,
        context_chunks=context_chunks,
        latency_ms=latency_ms,
        cache_hit=False,
        session_id=session_id
    )
```

---

## MODIFICAR: services/api/requirements.txt

Añadir si no existe:

```
httpx==0.26.0
```

---

## COMANDOS DE VALIDACIÓN

El humano debe ejecutar manualmente:

```bash
# 1. Verificar que OPENROUTER_API_KEY está configurado
echo $OPENROUTER_API_KEY

# 2. Rebuild del servicio API
docker compose -f deploy/compose/docker-compose.yml build api

# 3. Reiniciar
docker compose -f deploy/compose/docker-compose.yml up -d api

# 4. Probar consulta real
curl -X POST http://localhost/api/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "example_rag", "question": "¿Qué información tienes?"}'

# 5. Verificar que answer NO es "NOT_IMPLEMENTED"

# 6. Simular fallo del modelo principal (temporalmente):
# - Cambiar default_model a "modelo/invalido" en client.yaml
# - Reiniciar API
# - Hacer consulta
# - Verificar que usa fallback (ver logs)
# - Restaurar modelo correcto
```

---

## PUNTO DE ESPERA

⏸️ **DETENERSE AQUÍ**

Solicitar confirmación humana de:
- [ ] `/query` devuelve `answer` generado (no "NOT_IMPLEMENTED")
- [ ] Los templates se cargan correctamente
- [ ] El fallback funciona cuando se simula fallo del modelo principal
- [ ] Latency_ms refleja el tiempo real de llamada al LLM

---

## ERRORES TÍPICOS

| Error | Causa | Solución |
|-------|-------|----------|
| OPENROUTER_API_KEY not set | Variable no en .env | Añadir al archivo .env |
| Template not found | Path incorrecto | Verificar rutas en rag.yaml |
| 401 en OpenRouter | API key inválida | Regenerar key |
| Timeout frecuentes | Modelo lento | Usar modelo más rápido o aumentar timeout |

---

## LO QUE SE CONGELA

✅ Interfaz cliente OpenRouter (`call_chat_completion`, `call_with_fallback`)  
✅ Rutas de templates: `configs/rags/prompts/`  
✅ Variables en templates: `{question}`, `{context}`  
✅ Estrategia de fallback

---

## SIGUIENTE SUBPROYECTO

➡️ **Subproyecto 9**: Observabilidad mínima (logs estructurados + métricas)