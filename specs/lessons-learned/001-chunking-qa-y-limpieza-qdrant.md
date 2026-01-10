# 🧠 Lección Aprendida 001: Chunking Q&A y Limpieza de Colección en Qdrant para Recuperación Precisa en RAG

---

## 🟢 Problema Detectado

El sistema RAG no recuperaba respuestas correctas, incluso cuando la pregunta existía literalmente en el documento fuente. Las consultas devolvían "No tengo información suficiente..." o chunks irrelevantes.

---

## 🔍 Causa Raíz

1. **Chunking inadecuado:**  
   El script de ingesta dividía el documento en líneas o bloques fijos, fragmentando preguntas y respuestas, o separando bullets y listas, lo que hacía que los embeddings no representaran el contexto completo de cada Q&A.

2. **Ruido en Qdrant:**  
   Al re-ingestar sin limpiar la colección, coexistían chunks viejos y nuevos, generando ruido y dificultando la recuperación semántica.

---

## 🛠️ Solución Aplicada

### 1. Chunking Q&A Multilínea

Se implementó una función de chunking que:
- Detecta líneas que empiezan con `"pregunta:"` (ignorando comillas y espacios).
- Agrupa esa línea y todas las siguientes (incluyendo bullets y saltos de línea) hasta la próxima `"pregunta:"` o el final del archivo.
- Así, cada chunk contiene la pregunta y toda su respuesta, sin importar cuántas líneas ocupe.

**Snippet reutilizable:**

```python
import re

def chunk_by_qa_blocks(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.split('\n')]
    chunks = []
    current_chunk = []

    def is_pregunta_line(line: str) -> bool:
        return bool(re.match(r'^\s*["\']?\s*pregunta:', line.strip(), re.IGNORECASE))

    for line in lines:
        if is_pregunta_line(line):
            if current_chunk:
                chunk = "\n".join([l for l in current_chunk if l.strip()])
                if chunk:
                    chunks.append(chunk)
                current_chunk = []
            current_chunk.append(line)
        else:
            if current_chunk:
                current_chunk.append(line)
    if current_chunk:
        chunk = "\n".join([l for l in current_chunk if l.strip()])
        if chunk:
            chunks.append(chunk)
    return chunks
```

### 2. Limpieza de Colección en Qdrant

Antes de re-ingestar, se eliminó la colección `default` para evitar duplicados y ruido:

```bash
docker exec api python -c "from qdrant_client import QdrantClient; QdrantClient(url='http://qdrant:6333').delete_collection('default')"
```

---

## 🧩 Principio Preventivo Clave

**Siempre alinear el chunking con la estructura lógica del documento fuente.**  
En Q&A, cada chunk debe contener la pregunta y toda su respuesta, nunca fragmentos arbitrarios.

**Antes de re-ingestar datos en una base vectorial, limpiar la colección para evitar ruido y duplicidad.**

---

## 🚦 Señal de Activación para Evitar Errores Futuros

- Si una consulta literal no recupera la respuesta esperada, revisar:
  - ¿El chunking agrupa correctamente pregunta y respuesta?
  - ¿La colección de Qdrant contiene solo los datos actuales?
- Si el número de chunks tras la ingesta no coincide con el número de bloques Q&A esperados, revisar el script de chunking.
- Si tras una re-ingesta masiva las respuestas empeoran, limpiar la colección antes de re-ingestar.

---

## ✅ Resumen de la Mejora

- Chunking Q&A robusto = recuperación precisa.
- Limpieza de colección = embeddings relevantes y sin ruido.
- El sistema ahora responde correctamente a preguntas literales y variantes, incluso con respuestas multilínea o con bullets.

---