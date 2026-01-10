"""
Módulo LLM: integración con OpenRouter para llamadas a modelos de lenguaje.

Exports:
- call_chat_completion: Llamada a LLM con reintentos
- call_with_fallback: Llamada con modelo fallback automático
- OpenRouterError: Excepción para errores de OpenRouter
"""

from .openrouter_client import (
    call_chat_completion,
    call_with_fallback,
    OpenRouterError,
)

__all__ = [
    "call_chat_completion",
    "call_with_fallback",
    "OpenRouterError",
]