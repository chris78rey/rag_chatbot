# Integración con Qdrant

## Descripción

Qdrant es la base de datos vectorial usada para almacenar y buscar embeddings de los chunks de documentos. Proporciona búsqueda rápida de similitud usando distancia coseno.

## Arquitectura

- **Una colección por RAG**: Cada `rag_id` tiene su propia colección llamada `{rag_id}_collection`
- **Distancia**: Coseno (COSINE) para similitud semántica
- **Dimensión**: Configurable por RAG (default: 1536 para OpenAI ada-002)
- **Indexación**: Automática al upsert

## Payload por Chunk

Cada punto en Qdrant contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `source_path` | string | Ruta del archivo fuente (ej: `docs/policy.pdf`) |
| `page` | int | Número de página (para PDFs, default: 0) |
| `chunk_index` | int | Índice del chunk dentro del documento |
| `text` | string | Contenido textual del chunk |

### Ejemplo de Payload

```json
{
  "source_path": "docs/employee_handbook.pdf",
  "page": 5,
  "chunk_index": 12,
  "text": "Los empleados tienen derecho a 15 días de vacaciones anuales remuneradas..."
}
```

## Operaciones Disponibles

### Cliente (`qdrant_client.py`)

- **`get_client()`**: Obtener instancia singleton del cliente Qdrant
- **`ensure_collection(name, dim)`**: Crear colección si no existe
- **`upsert_chunks(collection, chunks, vectors)`**: Insertar/actualizar puntos
- **`search(collection, vector, top_k)`**: Buscar similares por vector
- **`delete_collection(name)`**: Eliminar colección (usado para reindex)

### Retrieval (`retrieval.py`)

- **`get_embedding(text)`**: Generar embedding para texto (placeholder)
- **`retrieve_context(rag_id, question, top_k)`**: Buscar contexto relevante para pregunta

## Configuración

### Variables de Entorno

```bash
QDRANT_URL="http://localhost:6333"      # URL del servidor Qdrant
QDRANT_API_KEY=""                       # API key opcional
EMBEDDING_MODEL="text-embedding-ada-002" # Modelo de embeddings
```

### Parámetros por RAG (YAML)

```yaml
rags:
  policies:
    embeddings:
      model_name: "text-embedding-ada-002"
      dimension: 1536
      batch_size: 32
      normalize: true
    collection:
      name: "policies_collection"
    retrieval:
      top_k: 5
      score_threshold: 0.7
```

## Flujo de Operaciones

### 1. Ingestión (Worker)

```
Archivo fuente
    ↓
Lee contenido (read_source)
    ↓
Divide en chunks (chunk_text_simple)
    ↓
Genera embeddings (generate_embeddings_dummy)
    ↓
Crea puntos Qdrant con payload
    ↓
Upsert a colección (qdrant_client.upsert_chunks)
```

### 2. Consulta (Query)

```
Pregunta del usuario
    ↓
Genera embedding (retrieval.get_embedding)
    ↓
Busca similares (qdrant_client.search)
    ↓
Retorna top-K chunks
    ↓
Arma respuesta con contexto
```

## Testing y Validación

### Poblar Datos de Demo

```bash
python scripts/seed_demo_data.py
```

Esto crea:
- Colección `demo_collection`
- 7 chunks de ejemplo
- Vectores determinísticos para testing

### Verificar Colecciones en Qdrant

```bash
# Ver todas las colecciones
curl http://localhost:6333/collections

# Ver info de una colección
curl http://localhost:6333/collections/demo_collection
```

### Probar Endpoint /query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo",
    "question": "¿Qué es FastAPI?",
    "top_k": 5
  }'
```

### Respuesta Esperada

```json
{
  "rag_id": "demo",
  "answer": "NOT_IMPLEMENTED - Contexto recuperado, falta integración LLM",
  "context_chunks": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "source": "docs/fastapi.txt",
      "text": "FastAPI es un framework web moderno y rápido para construir APIs con Python.",
      "score": 0.92
    }
  ],
  "latency_ms": 145,
  "cache_hit": false,
  "session_id": "sess_abc123"
}
```

## Errores Típicos

| Error | Causa | Solución |
|-------|-------|----------|
| `Connection refused` | Qdrant no levantado | Ejecutar `docker compose up -d qdrant` |
| `Collection not found` | Colección no creada | Ejecutar `seed_demo_data.py` o ingestar documentos |
| `Dimension mismatch` | Vector de dimensión incorrecta | Verificar `embeddings.dimension` en YAML |
| `Empty context_chunks` | Colección vacía o rag_id incorrecto | Verificar nombre de colección = `{rag_id}_collection` |
| `No such file` | Ruta de documento inválida | Verificar ruta en `data/sources/` |

## Características Congeladas

✅ **Estructura de payload**: `source_path`, `page`, `chunk_index`, `text`  
✅ **Naming de colecciones**: `{rag_id}_collection`  
✅ **Interfaz del cliente Qdrant**: métodos públicos  
✅ **Distancia de similitud**: COSINE  

## Próximos Pasos

### Subproject 7 (Actual)
- ✅ Cliente Qdrant implementado
- ✅ Retrieval de contexto implementado
- ✅ Endpoint /query funcional
- ✅ Datos de demo disponibles

### Subproject 8 (Futuro)
- Integración con LLM (OpenRouter)
- Generación de respuestas reales
- Cache de respuestas en Redis
- Rate limiting por RAG

## Dependencias

```python
qdrant-client>=2.0.0
```

Ya está incluido en `services/api/requirements.txt`

## Notas Importantes

1. **Embeddings dummy**: Actualmente usa pseudo-aleatorios determinísticos. En producción, implementar llamada real a API de embeddings.

2. **Dimensión fija**: Por defecto 1536 para OpenAI ada-002. Cambiar en config YAML según modelo.

3. **Performance**: 
   - Batch size configurable (default: 32)
   - Normalización de vectores recomendada
   - Score threshold configurable para filtrado

4. **Escalabilidad**: Una colección por RAG permite gestión independiente e indexación paralela.

5. **Persistencia**: Todos los datos se guardan en el volumen `qdrant_data` del docker-compose.

---

**Estado**: ✅ Subproject 7 COMPLETADO  
**Última actualización**: 2025-01-10  
**Próximo**: Subproject 8 (LLM Integration)