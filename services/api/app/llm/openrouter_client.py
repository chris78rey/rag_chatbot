"""
Cliente para OpenRouter API.
Maneja llamadas al LLM con reintentos y fallback.
"""
import os
import time
import asyncio
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
        "HTTP-Referer": "raf-onpremise",  # Requerido por OpenRouter
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