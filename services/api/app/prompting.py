"""
Gestión de templates de prompts por RAG.

Funciones:
- load_template(): Cargar template desde archivo
- clear_template_cache(): Limpiar cache
- build_messages(): Construir lista de mensajes para LLM
- format_context(): Formatear chunks para el prompt
"""
import os
from typing import List, Dict, Optional

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
    
    Raises:
        FileNotFoundError: Si el template no existe
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
    global _template_cache
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