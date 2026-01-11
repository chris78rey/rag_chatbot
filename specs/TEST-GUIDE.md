# 🧪 RAF CHATBOT - GUÍA COMPLETA DE PRUEBAS

## 📍 RUTA DEL PROYECTO
```
G:\zed_projects\raf_chatbot
```

---

## ✅ OPCIÓN 1: PRUEBA RÁPIDA (2 minutos)

### Paso 1: Levanta los servicios
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose up -d
```

**Resultado esperado:**
```
✔ Network compose_rag_network  Created
✔ Container redis              Started
✔ Container qdrant             Started
✔ Container ingest-worker      Started
✔ Container api                Started
✔ Container nginx              Started
```

### Paso 2: Verifica que están corriendo
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose ps
```

**Resultado esperado:** Todos los contenedores con estado `Up`

### Paso 3: Ejecuta el verificador
```bash
cd G:\zed_projects\raf_chatbot
python scripts/verify_state.py
```

**Resultado esperado:**
```
============================================================
FINAL STATUS: STATE_OK
============================================================
```

### Paso 4: Apaga todo
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose down
```

---

## 🔍 OPCIÓN 2: PRUEBAS DETALLADAS (5 minutos)

Ejecuta estos comandos **en orden** en PowerShell o CMD:

### 1️⃣ Levanta los contenedores
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose up -d
```

### 2️⃣ Espera 10 segundos y verifica estado
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose ps
```

### 3️⃣ Prueba API Health
```bash
curl http://localhost:8001/health
```

**Resultado esperado:**
```json
{"status":"healthy"}
```

### 4️⃣ Prueba Qdrant Health
```bash
curl http://localhost:6333/readyz
```

**Resultado esperado:**
```
all shards are ready
```

### 5️⃣ Prueba Métricas
```bash
curl http://localhost:8001/metrics
```

**Resultado esperado:**
```json
{"requests_total":0,"errors_total":0,"cache_hits_total":0,"rate_limited_total":0,"avg_latency_ms":0.0,"p95_latency_ms":0.0,"latency_samples":0}
```

### 6️⃣ Inicializa Base de Datos
```bash
cd G:\zed_projects\raf_chatbot
docker-compose -f deploy/compose/docker-compose.yml exec -T api python -c "from qdrant_client import QdrantClient; client = QdrantClient('qdrant', port=6333); client.recreate_collection(collection_name='documents', vectors_config={'size': 384, 'distance': 'Cosine'}); client.upsert(collection_name='documents', points=[{'id': 1, 'vector': [0.1]*384, 'payload': {'text': 'Sample doc 1'}}, {'id': 2, 'vector': [0.2]*384, 'payload': {'text': 'Sample doc 2'}}, {'id': 3, 'vector': [0.3]*384, 'payload': {'text': 'Sample doc 3'}}]); print('Database initialized with 3 sample documents')"
```

**Resultado esperado:**
```
Database initialized with 3 sample documents
```

### 7️⃣ Verifica que hay datos
```bash
cd G:\zed_projects\raf_chatbot
docker-compose -f deploy/compose/docker-compose.yml exec -T api python -c "from qdrant_client import QdrantClient; client = QdrantClient('qdrant', port=6333); print('Collections:', client.get_collections())"
```

**Resultado esperado:**
```
Collections: collections=[CollectionDescription(name='documents')]
```

### 8️⃣ Ejecuta Verificador Completo
```bash
cd G:\zed_projects\raf_chatbot
python scripts/verify_state.py
```

**Resultado esperado:**
```
============================================================
STATE VERIFICATION REPORT
============================================================
✓ PASS: API Health
✓ PASS: API Endpoints
✓ PASS: Metrics Availability
✓ PASS: Qdrant Health
✓ PASS: Qdrant Collection
✓ PASS: System Constraints

------------------------------------------------------------

============================================================
FINAL STATUS: STATE_OK
============================================================
```

### 9️⃣ Apaga todo
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose down
```

---

## 🐛 TROUBLESHOOTING

### ❌ Error: "docker-compose: command not found"
**Solución:** Asegúrate que Docker Desktop está instalado y corriendo

### ❌ Error: "Connection refused" en curl
**Solución:** Espera 15 segundos después de `docker-compose up -d`

### ❌ Error: "Port 8001 already in use"
**Solución:** Ejecuta:
```bash
cd G:\zed_projects\raf_chatbot\deploy\compose
docker-compose down
```

### ❌ Error en verify_state.py: "ModuleNotFoundError"
**Solución:** Instala dependencias:
```bash
cd G:\zed_projects\raf_chatbot
pip install -r requirements.txt
```

---

## 📊 CHEQUEO DE PUNTOS CRÍTICOS

| Punto | Comando | Resultado Esperado |
|-------|---------|-------------------|
| **API Running** | `curl http://localhost:8001/health` | `{"status":"healthy"}` |
| **Qdrant Running** | `curl http://localhost:6333/readyz` | `all shards are ready` |
| **Métricas** | `curl http://localhost:8001/metrics` | JSON con métricas |
| **Base de Datos** | `docker-compose exec -T api python -c "..."` | `Database initialized...` |
| **Estado General** | `python scripts/verify_state.py` | `STATE_OK` |

---

## 🎯 PRÓXIMOS PASOS

Una vez que **STATE_OK** esté confirmado, puedes:

1. **Hacer pruebas manuales** contra la API en `http://localhost:8001`
2. **Revisar logs** con: `docker-compose logs -f api`
3. **Ejecutar tests** (si existen): `pytest tests/`
4. **Integrar en CI/CD** usando `verify_state.py`

---

## 📝 NOTAS

- ✅ Todos los servicios se levantan con **docker-compose up -d**
- ✅ La base de datos se inicializa automáticamente con el comando de Qdrant
- ✅ El verificador (`verify_state.py`) es **read-only** y no modifica nada
- ✅ Los puertos usados son: `8001` (API), `8080` (Nginx), `6333` (Qdrant)
- ⚠️ Recuerda hacer `docker-compose down` cuando termines para liberar recursos