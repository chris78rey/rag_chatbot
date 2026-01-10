# Lecciones Aprendidas 04 - LLM Fallback Pattern

## 🎯 Problema Identificado

**Subproyecto 8 (LLM Integration with OpenRouter)**

Necesidad de integración con servicio externo (OpenRouter API) que puede fallar por:
- Timeout del servicio
- Modelo primary no disponible
- Rate limiting
- Error de autenticación
- Respuesta malformada

Sin fallback, cualquier fallo del LLM primary = fallo total del servicio.

```
Request → Primary LLM (falla) → Error 500 ❌
```

---

## 🔍 Causa Raíz

### 1. Dependencia de Servicio Externo

```python
# ❌ INCORRECTO - Sin fallback
async def call_llm(model: str, messages: list):
    """Llamada directa sin protección."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={"model": model, "messages": messages},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        response.raise_for_status()  # ❌ Si falla → excepción no manejada
        return response.json()
```

### 2. Fallos Potenciales

```
OpenRouter API (Externo)
        ↓
   Puede fallar por:
   - Modelo primary no available (429)
   - Timeout (540s de espera)
   - API key inválida (401)
   - Rate limit (429)
   - Server error (500)
   
   Sin fallback:
   ❌ Toda la request falla
   ❌ Usuario ve error
   ❌ Mala experiencia
```

### 3. Cadena de Dependencias

```
User Request
    ↓
Query Endpoint
    ↓
Retrieval (Qdrant) ← OK generalmente
    ↓
LLM Call (OpenRouter) ← POINT OF FAILURE
    ↓
Return Response
```

---

## ✅ Solución Implementada

### Paso 1: Estructura de Primary + Fallback

```python
# services/api/app/llm/openrouter_client.py
"""
Cliente OpenRouter con soporte para fallback automático.
"""

import httpx
import asyncio
from typing import Optional, Dict, List

class OpenRouterError(Exception):
    """Error específico de OpenRouter."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")

async def call_chat_completion(
    model: str,
    messages: List[Dict],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 30,
) -> Dict:
    """
    Llamada individual a modelo LLM.
    
    Args:
        model: ID del modelo (ej: "openai/gpt-3.5-turbo")
        messages: Lista de mensajes
        max_tokens: Tokens máximos
        temperature: Temperatura de respuesta
        timeout: Timeout en segundos
        
    Returns:
        Respuesta del LLM
        
    Raises:
        OpenRouterError: Si falla la llamada
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError(401, "OPENROUTER_API_KEY no configurada")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            
            if response.status_code == 429:
                raise OpenRouterError(429, "Rate limited - intenta más tarde")
            if response.status_code == 401:
                raise OpenRouterError(401, "API key inválida")
            if response.status_code >= 500:
                raise OpenRouterError(500, "OpenRouter server error")
            
            response.raise_for_status()
            
            data = response.json()
            # Extraer contenido
            content = data["choices"][0]["message"]["content"]
            
            return {"content": content, "model": model}
            
    except httpx.TimeoutException:
        raise OpenRouterError(504, "Timeout - servicio muy lento")
    except httpx.RequestError as e:
        raise OpenRouterError(500, f"Network error: {str(e)}")
    except (KeyError, IndexError) as e:
        raise OpenRouterError(500, f"Respuesta malformada: {str(e)}")


async def call_with_fallback(
    primary_model: str,
    fallback_model: str,
    messages: List[Dict],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 30,
    max_retries: int = 2,
) -> Dict:
    """
    Llamada con fallback automático.
    
    Flujo:
    1. Intentar primary_model
    2. Si falla, intentar fallback_model
    3. Si ambas fallan, retornar respuesta cached o error
    
    Args:
        primary_model: Modelo preferido (ej: "openai/gpt-3.5-turbo")
        fallback_model: Modelo fallback (ej: "anthropic/claude-instant-v1")
        messages: Lista de mensajes
        max_tokens: Tokens máximos
        temperature: Temperatura
        timeout: Timeout en segundos
        max_retries: Intentos antes de fallar
        
    Returns:
        Respuesta del LLM (primary o fallback)
        
    Raises:
        OpenRouterError: Si ambos modelos fallan
    """
    
    logger.info(f"LLM call: primary={primary_model}, fallback={fallback_model}")
    
    # Intentar primary
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: {primary_model}")
            result = await call_chat_completion(
                primary_model, messages, max_tokens, temperature, timeout
            )
            logger.info(f"✓ Éxito con primary model: {primary_model}")
            return result
            
        except OpenRouterError as e:
            logger.warning(f"✗ Primary model failed: {e.message} (attempt {attempt + 1})")
            
            # Si es error 401, no vale la pena reintentar
            if e.status_code == 401:
                break
            
            # Esperar un poco antes de reintentar
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Backoff simple
    
    # Intentar fallback
    logger.info(f"Intentando fallback model: {fallback_model}")
    
    for attempt in range(max_retries):
        try:
            result = await call_chat_completion(
                fallback_model, messages, max_tokens, temperature, timeout
            )
            logger.info(f"✓ Éxito con fallback model: {fallback_model}")
            return result
            
        except OpenRouterError as e:
            logger.warning(f"✗ Fallback model failed: {e.message} (attempt {attempt + 1})")
            
            if e.status_code == 401:
                break
            
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
    
    # Ambos fallaron
    logger.error(f"✗ Ambos modelos fallaron: {primary_model} y {fallback_model}")
    raise OpenRouterError(500, "Ambos primary y fallback models fallaron")
```

### Paso 2: Usar en Query Endpoint

```python
# services/api/app/routes/query.py
from app.llm import call_with_fallback, OpenRouterError
from app.observability import get_metrics, Timer

@router.post("/query")
async def query_rag(request: QueryRequest):
    """Endpoint con LLM fallback."""
    
    metrics = get_metrics()
    metrics.inc_requests()
    
    with Timer() as timer:
        try:
            # ... retrieval code ...
            
            # LLM call con fallback
            try:
                llm_response = await call_with_fallback(
                    primary_model="openai/gpt-3.5-turbo",
                    fallback_model="anthropic/claude-instant-v1",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    timeout=30,
                    max_retries=2,
                )
                answer = llm_response["content"]
                
            except OpenRouterError as e:
                # ✓ Fallback graceful: retornar mensaje de error
                metrics.inc_errors()
                answer = f"No se pudo generar respuesta: {e.message}"
                logger.error(f"LLM error: {e}")
            
            return QueryResponse(
                rag_id=request.rag_id,
                answer=answer,
                context_chunks=context_chunks,
                latency_ms=int(timer.elapsed_ms),
                cache_hit=False,
                session_id=session_id,
            )
            
        except Exception as e:
            metrics.inc_errors()
            raise HTTPException(status_code=500, detail=str(e))
```

### Paso 3: Configuración de Modelos

```yaml
# configs/client.yaml
llm:
  primary_model: "openai/gpt-3.5-turbo"
  fallback_model: "anthropic/claude-instant-v1"
  
  # Modelos ordenados por preferencia
  model_preference:
    - "openai/gpt-4"           # Mejor calidad, más caro
    - "openai/gpt-3.5-turbo"   # Buen balance
    - "anthropic/claude-3"     # Alternativa
    - "anthropic/claude-instant-v1"  # Fallback rápido
  
  # Configuración de timeouts
  timeouts:
    primary_fast: 15  # Timeout agresivo para primary
    fallback_patient: 45  # Más tiempo para fallback
```

---

## 🛡️ Principios Preventivos Clave

### P1: Diferencia entre Error y Fallo Graceful

```
❌ ERROR (BAD)
────────────
Request → LLM falla → Excepción no manejada → Error 500

✓ FALLO GRACEFUL (GOOD)
──────────────────────
Request → Primary LLM falla → Fallback LLM → Éxito
Request → Ambos LLM fallan → Respuesta default → Éxito parcial
```

### P2: Jerarquía de Tolerancia

```python
# Nivel 1: Primary model (mejor calidad)
try:
    result = await call_llm("openai/gpt-4", messages)  # Premium
except:
    # Nivel 2: Fallback model (buena calidad)
    try:
        result = await call_llm("anthropic/claude-3", messages)  # Good
    except:
        # Nivel 3: Ultra fallback (rápido pero básico)
        try:
            result = await call_llm("openai/text-davinci-003", messages)  # Fast
        except:
            # Nivel 4: Respuesta cacheada o template
            result = DEFAULT_RESPONSE  # Graceful degradation
```

### P3: Retry Strategy

```python
# Exponential backoff
async def call_with_exponential_backoff(
    model: str,
    messages: List,
    max_retries: int = 3,
    base_delay: float = 0.5,
):
    """Reintentos con backoff exponencial."""
    
    for attempt in range(max_retries):
        try:
            return await call_chat_completion(model, messages)
        except OpenRouterError as e:
            # No reintentar si es auth error
            if e.status_code == 401:
                raise
            
            # No reintentar si es último intento
            if attempt == max_retries - 1:
                raise
            
            # Esperar cada vez más tiempo
            delay = base_delay * (2 ** attempt)  # 0.5s, 1s, 2s, 4s, ...
            logger.info(f"Retry in {delay}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
```

### P4: Circuit Breaker Pattern

```python
# Evitar bombardear servicio que está down
from datetime import datetime, timedelta

class CircuitBreaker:
    """Patrón circuit breaker para servicio externo."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # segundos
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Registrar llamada exitosa."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Registrar fallo."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker OPEN: {self.failure_count} failures")
    
    def can_call(self) -> bool:
        """Verificar si se puede hacer llamada."""
        
        # Si está abierto, verificar timeout
        if self.is_open:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed > self.timeout:
                # Intentar recuperar (half-open)
                self.is_open = False
                self.failure_count = 0
                logger.info("Circuit breaker half-open: retrying...")
                return True
            return False
        
        return True

# Uso
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

async def safe_call_llm(model: str, messages: list):
    """Llamada con circuit breaker."""
    
    if not breaker.can_call():
        raise OpenRouterError(503, "Servicio temporalmente no disponible")
    
    try:
        result = await call_chat_completion(model, messages)
        breaker.record_success()
        return result
    except OpenRouterError as e:
        breaker.record_failure()
        raise
```

### P5: Timeouts Diferenciados

```python
# No todos los errores son iguales
class TimeoutStrategy:
    """Estrategia de timeouts según modelo."""
    
    FAST_MODELS = {
        "openai/text-davinci-003": 10,  # Generalmente rápido
    }
    
    SLOW_MODELS = {
        "openai/gpt-4": 60,  # Puede tomar tiempo
        "anthropic/claude-3": 45,
    }
    
    @classmethod
    def get_timeout(cls, model: str, is_fallback: bool = False) -> float:
        """Obtener timeout apropiado para modelo."""
        
        # Fallback puede esperar más
        if is_fallback:
            return cls.SLOW_MODELS.get(model, 45)
        else:
            # Primary es más agresivo
            return cls.FAST_MODELS.get(model, 30)

# Uso
timeout = TimeoutStrategy.get_timeout("openai/gpt-4", is_fallback=False)
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: Muchas Respuestas de Error

```python
# En monitoring/logs:
# ERROR: [LLM] Both primary and fallback failed
# ERROR: [LLM] Both primary and fallback failed
# ERROR: [LLM] Both primary and fallback failed
# (repetido 100 veces)

# = Ambos modelos están down → Necesitar un 3er fallback
```

### Señal 2: Latencias Altas en Fallback

```python
# Métricas:
# avg_latency: 45s
# p95_latency: 120s
# requests usando fallback: 80%

# = Primary está lento → Considerar umbral menor antes de fallback
```

### Señal 3: Rate Limiting Frecuente

```
ERROR: Rate limited - intenta más tarde (429)
ERROR: Rate limited - intenta más tarde (429)
ERROR: Rate limited - intenta más tarde (429)

# = Necesitar rate limiting en cliente (no bombardear)
```

### Señal 4: Auth Failures

```
ERROR: API key inválida (401)
ERROR: API key inválida (401)

# = Verificar OPENROUTER_API_KEY en .env
```

---

## 💻 Código Reutilizable

### Clase: Fallback Manager

```python
# services/api/app/llm/fallback_manager.py
"""
Manager para estrategias de fallback.
Reutilizable para cualquier servicio externo.
"""

import asyncio
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Configuración de un modelo."""
    name: str
    timeout: float
    retry_count: int
    priority: int  # Menor = más prioritario

class FallbackManager:
    """Gestor de estrategias de fallback."""
    
    def __init__(self, models: List[ModelConfig]):
        """
        Args:
            models: Lista de modelos ordenados por preferencia
        """
        self.models = sorted(models, key=lambda m: m.priority)
        self.call_history = {}
    
    async def call_with_fallback(
        self,
        call_func: Callable[[str, Any], Any],
        data: Any,
    ) -> Dict:
        """
        Llamar función con fallback automático.
        
        Args:
            call_func: Función async que toma (model_name, data)
            data: Datos a pasar a call_func
            
        Returns:
            Resultado con info de qué modelo se usó
        """
        
        last_error = None
        
        for model_config in self.models:
            try:
                logger.info(f"Trying {model_config.name} (priority {model_config.priority})")
                
                for attempt in range(model_config.retry_count):
                    try:
                        result = await asyncio.wait_for(
                            call_func(model_config.name, data),
                            timeout=model_config.timeout,
                        )
                        
                        logger.info(f"✓ Success with {model_config.name}")
                        self.call_history[model_config.name] = "success"
                        
                        return {
                            "result": result,
                            "model": model_config.name,
                            "fallback": False,
                        }
                        
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Timeout on {model_config.name} "
                            f"(attempt {attempt + 1}/{model_config.retry_count})"
                        )
                        if attempt < model_config.retry_count - 1:
                            await asyncio.sleep(1)
                        last_error = "timeout"
                        
                    except Exception as e:
                        logger.warning(f"Error on {model_config.name}: {str(e)}")
                        last_error = str(e)
                        raise
                        
            except Exception as e:
                logger.warning(f"✗ Failed with {model_config.name}: {str(e)}")
                self.call_history[model_config.name] = f"failed: {e}"
                continue
        
        # Todos los modelos fallaron
        error_msg = f"All models failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

# Uso:
models = [
    ModelConfig("openai/gpt-4", timeout=30, retry_count=2, priority=1),
    ModelConfig("openai/gpt-3.5-turbo", timeout=30, retry_count=2, priority=2),
    ModelConfig("anthropic/claude-3", timeout=45, retry_count=1, priority=3),
]

manager = FallbackManager(models)

async def call_llm_func(model: str, messages: list):
    # Implementación
    pass

result = await manager.call_with_fallback(call_llm_func, messages)
# result = {
#     "result": {...},
#     "model": "openai/gpt-4",
#     "fallback": False,
# }
```

### Script de Testing: `tests/test_llm_fallback.py`

```python
#!/usr/bin/env python3
"""
Tests para fallback en LLM.
Ejecutar: pytest tests/test_llm_fallback.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.llm import call_with_fallback, OpenRouterError

class TestLLMFallback:
    """Suite de tests para fallback strategy."""
    
    @pytest.mark.asyncio
    async def test_primary_success(self):
        """Test que si primary funciona, se usa primary."""
        
        with patch('app.llm.call_chat_completion') as mock_call:
            # Primary funciona
            mock_call.side_effect = [
                {"content": "Respuesta primaria", "model": "gpt-4"}
            ]
            
            result = await call_with_fallback(
                primary_model="openai/gpt-4",
                fallback_model="anthropic/claude-3",
                messages=[],
            )
            
            assert result["model"] == "openai/gpt-4"
            assert "Respuesta primaria" in result["content"]
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Test que si primary falla, se usa fallback."""
        
        with patch('app.llm.call_chat_completion') as mock_call:
            # Primary falla, fallback funciona
            mock_call.side_effect = [
                OpenRouterError(500, "Primary failed"),
                {"content": "Respuesta fallback", "model": "claude-3"},
            ]
            
            result = await call_with_fallback(
                primary_model="openai/gpt-4",
                fallback_model="anthropic/claude-3",
                messages=[],
            )
            
            assert result["model"] == "anthropic/claude-3"
            assert "Respuesta fallback" in result["content"]
    
    @pytest.mark.asyncio
    async def test_both_fail_raises_error(self):
        """Test que si ambos fallan, se lanza excepción."""
        
        with patch('app.llm.call_chat_completion') as mock_call:
            # Ambos fallan
            mock_call.side_effect = [
                OpenRouterError(500, "Primary failed"),
                OpenRouterError(503, "Fallback also failed"),
            ]
            
            with pytest.raises(OpenRouterError):
                await call_with_fallback(
                    primary_model="openai/gpt-4",
                    fallback_model="anthropic/claude-3",
                    messages=[],
                )
    
    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Test que no se reintenta en error de auth."""
        
        with patch('app.llm.call_chat_completion') as mock_call:
            # Auth error (401) - no debe reintentar
            mock_call.side_effect = [
                OpenRouterError(401, "Invalid API key"),
            ]
            
            with pytest.raises(OpenRouterError) as exc_info:
                await call_with_fallback(
                    primary_model="openai/gpt-4",
                    fallback_model="anthropic/claude-3",
                    messages=[],
                    max_retries=3,  # No importa, debe fallar inmediatamente
                )
            
            # Solo debe haber intentado una vez
            assert mock_call.call_count == 1
            assert exc_info.value.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 📋 Checklist de Implementación

### Antes de integrar LLM externo

- [ ] Definir primary y fallback models
- [ ] Establecer timeouts apropiados (primary < fallback)
- [ ] Implementar circuit breaker
- [ ] Implementar retry logic con backoff
- [ ] Logging detallado de intentos
- [ ] Tests que simulan fallos de primary
- [ ] Tests que simulan fallos de fallback
- [ ] Tests de ambos failing
- [ ] Load testing con ambos modelos
- [ ] Configurar alertas en fallback frecuente

### En revisión de código

```python
# Preguntas:
1. ¿Hay try/except alrededor de LLM call? → Sí ✓
2. ¿Hay retry logic? → Sí ✓
3. ¿Hay fallback model? → Sí ✓
4. ¿Se registran errores en logging? → Sí ✓
5. ¿Se registran en métricas? → Sí ✓
6. ¿Hay timeout? → Sí ✓
7. ¿Se maneja respuesta gracefully? → Sí ✓
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-01-DOCKER-NETWORKING.md` (puertos)
- Ver: `LESSONS-LEARNED-02-ROUTER-INTEGRATION.md` (routers)
- Ver: `LESSONS-LEARNED-03-THREAD-SAFETY.md` (métricas compartidas)

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - LLM fallback |

---

## ✨ Key Takeaway

> **"Nunca asumir que servicio externo estará disponible. Implementar primary + fallback + circuit breaker + timeouts diferenciados. Graceful degradation > Error total."**

```python
# Patrón ganador
async def call_llm_safely(messages: list, metrics):
    metrics.inc_requests()
    
    try:
        # Intentar primary
        return await call_with_fallback(
            primary_model="openai/gpt-4",
            fallback_model="anthropic/claude-3",
            messages=messages,
            timeout=30,
            max_retries=2,
        )
    except OpenRouterError as e:
        # Graceful degradation
        metrics.inc_errors()
        logger.error(f"LLM failed: {e.message}")
        return {"content": "No se pudo generar respuesta ahora"}
```

---