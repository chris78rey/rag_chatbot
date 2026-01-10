"""
Módulo de embeddings usando OpenAI API.

Usa el modelo text-embedding-3-small que es muy económico:
- $0.02 por 1M tokens (aproximadamente $0.00002 por consulta)

Nota: OpenRouter no tiene endpoint de embeddings, así que usamos
directamente la API de OpenAI. Necesitas OPENAI_API_KEY en .env
(puede ser la misma key si usas OpenAI, o una separada).

Si no tienes key de OpenAI, puedes usar OPENROUTER_API_KEY con
modelos que soporten embeddings vía chat (menos eficiente).
"""
import os
import hashlib
import asyncio
import httpx
from typing import List, Optional
from functools import lru_cache

# URLs de APIs
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"

# Modelo económico de OpenAI
DEFAULT_MODEL = "text-embedding-3-small"  # $0.02/1M tokens, dim=1536
EMBEDDING_DIM = 1536


class EmbeddingError(Exception):
    """Error al generar embeddings."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Cache en memoria para embeddings (evita llamadas repetidas)
_embedding_cache = {}


def get_cache_key(text: str, model: str) -> str:
    """Genera key de cache para un texto."""
    return hashlib.md5(f"{model}:{text}".encode()).hexdigest()


async def get_embedding(
    text: str,
    model: str = DEFAULT_MODEL,
    use_cache: bool = True
) -> List[float]:
    """
    Obtiene embedding para un texto usando OpenAI API.
    
    Args:
        text: Texto a vectorizar
        model: Modelo de embeddings (default: text-embedding-3-small)
        use_cache: Si usar cache en memoria
        
    Returns:
        Vector de embeddings (1536 dimensiones para text-embedding-3-small)
        
    Raises:
        EmbeddingError: Si falla la API
    """
    # Verificar cache
    if use_cache:
        cache_key = get_cache_key(text, model)
        if cache_key in _embedding_cache:
            return _embedding_cache[cache_key]
    
    # Obtener API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY not set. Add it to .env file.\n"
            "Get your key at: https://platform.openai.com/api-keys"
        )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "input": text,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                OPENAI_EMBEDDINGS_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                # Guardar en cache
                if use_cache:
                    _embedding_cache[cache_key] = embedding
                
                return embedding
            
            # Error de API
            error_msg = f"OpenAI API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
            except:
                pass
            
            raise EmbeddingError(error_msg, response.status_code)
            
    except httpx.TimeoutException:
        raise EmbeddingError("Timeout calling OpenAI API", None)
    except httpx.RequestError as e:
        raise EmbeddingError(f"Request error: {str(e)}", None)


async def get_embeddings_batch(
    texts: List[str],
    model: str = DEFAULT_MODEL,
    use_cache: bool = True
) -> List[List[float]]:
    """
    Obtiene embeddings para múltiples textos en un solo request.
    Más eficiente que llamar get_embedding múltiples veces.
    
    Args:
        texts: Lista de textos a vectorizar
        model: Modelo de embeddings
        use_cache: Si usar cache
        
    Returns:
        Lista de vectores de embeddings
    """
    if not texts:
        return []
    
    # Verificar cuáles ya están en cache
    results = [None] * len(texts)
    texts_to_fetch = []
    indices_to_fetch = []
    
    if use_cache:
        for i, text in enumerate(texts):
            cache_key = get_cache_key(text, model)
            if cache_key in _embedding_cache:
                results[i] = _embedding_cache[cache_key]
            else:
                texts_to_fetch.append(text)
                indices_to_fetch.append(i)
    else:
        texts_to_fetch = texts
        indices_to_fetch = list(range(len(texts)))
    
    # Si todos estaban en cache
    if not texts_to_fetch:
        return results
    
    # Obtener API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY not set. Add it to .env file.\n"
            "Get your key at: https://platform.openai.com/api-keys"
        )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # OpenAI acepta hasta 2048 textos por request, pero limitamos a 100 por seguridad
    batch_size = 100
    
    for batch_start in range(0, len(texts_to_fetch), batch_size):
        batch_texts = texts_to_fetch[batch_start:batch_start + batch_size]
        batch_indices = indices_to_fetch[batch_start:batch_start + batch_size]
        
        payload = {
            "model": model,
            "input": batch_texts,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    OPENAI_EMBEDDINGS_URL,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data["data"]:
                        idx = item["index"]
                        embedding = item["embedding"]
                        original_idx = batch_indices[idx]
                        results[original_idx] = embedding
                        
                        # Guardar en cache
                        if use_cache:
                            cache_key = get_cache_key(batch_texts[idx], model)
                            _embedding_cache[cache_key] = embedding
                else:
                    error_msg = f"OpenAI API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
                    except:
                        pass
                    raise EmbeddingError(error_msg, response.status_code)
                    
        except httpx.TimeoutException:
            raise EmbeddingError("Timeout calling OpenAI API", None)
        except httpx.RequestError as e:
            raise EmbeddingError(f"Request error: {str(e)}", None)
    
    return results


def get_embedding_sync(
    text: str,
    model: str = DEFAULT_MODEL,
    use_cache: bool = True
) -> List[float]:
    """
    Versión síncrona de get_embedding (para scripts).
    """
    return asyncio.run(get_embedding(text, model, use_cache))


def get_embeddings_batch_sync(
    texts: List[str],
    model: str = DEFAULT_MODEL,
    use_cache: bool = True
) -> List[List[float]]:
    """
    Versión síncrona de get_embeddings_batch (para scripts).
    """
    return asyncio.run(get_embeddings_batch(texts, model, use_cache))


def clear_cache():
    """Limpia el cache de embeddings en memoria."""
    global _embedding_cache
    _embedding_cache = {}


def get_embedding_dimension(model: str = DEFAULT_MODEL) -> int:
    """
    Retorna la dimensión de embeddings para un modelo.
    """
    dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    return dimensions.get(model, 1536)