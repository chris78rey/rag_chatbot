# Integración LLM (OpenRouter)

## Descripción

El sistema utiliza OpenRouter como proveedor de LLM, permitiendo acceso a múltiples modelos (OpenAI, Anthropic, etc.) a través de una única API.

## Configuración

### Variables de entorno

```bash
OPENROUTER_API_KEY=sk-or-xxx  # API key de OpenRouter
```

Obtener API key en: https://openrouter.ai/keys

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
3. Si ambos fallan, se retorna el mensaje de error configurado

## Templates de Prompts

### Ubicación

```
configs/rags/prompts/
├── system_default.txt    # Prompt de sistema por defecto
└── user_default.txt      # Prompt de usuario por defecto
```

### Variables disponibles en templates

- `{question}`: Pregunta del usuario
- `{context}`: Contexto formateado de los chunks recuperados

### Crear templates personalizados por RAG

1. Crear archivos en `configs/rags/prompts/mi_rag_system.txt`
2. Actualizar `prompting.system_template_path` en el YAML del RAG

## Flujo de Consulta

```
1. Usuario envía pregunta a /query
2. Retrieval en Qdrant → chunks de contexto
3. Cargar templates según config del RAG
4. build_messages(system, user, question, chunks, history)
5. call_with_fallback(primary, fallback, messages, ...)
6. Retornar respuesta generada
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

## Estructura de Llamada

### Request a OpenRouter

```json
{
  "model": "openai/gpt-3.5-turbo",
  "messages": [
    {
      "role": "system",
      "content": "Eres un asistente experto..."
    },
    {
      "role": "user",
      "content": "Contexto: [chunks formateados]...\n\nPregunta: ¿Cuál es tu respuesta?"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

### Response de OpenRouter

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "La respuesta generada por el LLM..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570
  },
  "model": "openai/gpt-3.5-turbo"
}
```

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| OPENROUTER_API_KEY not set | Variable no configurada | Añadir `OPENROUTER_API_KEY` al `.env` |
| 401 Unauthorized | API key inválida | Verificar key en OpenRouter dashboard |
| 429 Rate Limited | Límite de requests alcanzado | Esperar o cambiar a modelo más barato |
| Timeout | Modelo lento o red lenta | Aumentar `timeout_s` o usar modelo más rápido |
| Template not found | Ruta de template incorrecta | Verificar rutas en YAML del RAG |
| No context retrieved | Qdrant no tiene datos | Ejecutar `seed_demo_data.py` |

## Logs y Debugging

### Ver logs del LLM

```bash
# Levantar API con logs
docker compose -f deploy/compose/docker-compose.yml logs -f api

# En logs verás:
# Primary model failed: ... trying fallback...
```

### Test manual de LLM

```bash
# Asegúrate de que OPENROUTER_API_KEY está configurado
export OPENROUTER_API_KEY="tu-api-key"

# Probar endpoint /query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo",
    "question": "What is FastAPI?",
    "top_k": 5
  }'

# Debe retornar una respuesta real, no "NOT_IMPLEMENTED"
```

## Costos Aproximados

### Por 1,000 tokens (input + output)

| Modelo | Costo |
|--------|-------|
| GPT-3.5-turbo | $0.002 |
| Claude Instant | $0.0008 |
| Mistral 7B | $0.00014 |
| Llama 2 13B | $0.0001 |

**Nota**: Revisar precios actuales en https://openrouter.ai/

## Limitaciones Conocidas

1. **Modelos de fallback**: Si ambos fallan, no hay reintento adicional
2. **Historial de sesión**: Actualmente no se soporta (implementar en SP9)
3. **Streaming**: No soportado en MVP (implementar en SP9)
4. **Token counting**: No se cuenta consumo (implementar en SP9)

## Próximos Pasos

- SP9: Observabilidad (logs, métricas, token counting)
- SP9: Sesiones con historial
- SP9: Streaming de respuestas
- SP9: Cost tracking por RAG

---

**Status**: ✅ Subproject 8 Complete  
**Last Updated**: 2025-01-10  
**Next**: Subproject 9 (Observability)