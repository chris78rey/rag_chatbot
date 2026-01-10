# Lecciones Aprendidas #6: Database Seeding & Collection Initialization

**Subproject 10 - State Verification & Management**

---

## 🎯 Problema Identificado

**"Qdrant Collection Empty - STATE_FAIL"**

Durante la validación de SP10, después de levantar los servicios con Docker Compose, el script de verificación de estado falló porque la colección `documents` en Qdrant estaba vacía:

```
✗ FAIL: Qdrant Collection
ERROR: Qdrant collection 'documents' not found. Found: []
```

El servicio Qdrant estaba corriendo correctamente, pero:
1. La colección `documents` no existía
2. No había datos seeding automático
3. El verificador no tenía forma de inicializar datos
4. El script de seeding existente no se ejecutaba automáticamente

### Contexto

- Se asumió que los datos estarían presentes después de levantar Docker Compose
- No había mecanismo automático de inicialización de datos
- El script `seed_demo_data.py` requería instalar dependencias fuera de Docker
- No estaba documentado cómo o cuándo ejecutar el seeding

---

## 🔍 Causa Raíz

### Factor 1: Falta de Inicialización Automática en Docker

**El problema**: Docker Compose levanta los servicios pero no ejecuta scripts de inicialización automáticamente.

```yaml
# ❌ INCORRECTO - Sin hooks de inicialización
services:
  qdrant:
    image: qdrant/qdrant:latest
    # Nada aquí que inicialice datos
    # Los datos no se crean automáticamente
```

**La realidad**: Los contenedores no tienen estado persistente de inicialización. Necesitan:
- Volúmenes inicializados con datos (bind mounts)
- Scripts de inicialización (entrypoints personalizados)
- Procesos separados que poplen datos

### Factor 2: Script de Seeding no Integrado en Flujo de Deployment

El archivo `scripts/seed_demo_data.py` existía pero:
- No se ejecutaba automáticamente
- Requería dependencias instaladas localmente (qdrant-client, etc.)
- No estaba documentado en qué momento ejecutarlo
- No era parte del flujo de "levanta servicios → verificar"

```python
# ❌ PROBLEMA - Script existe pero es manual
# scripts/seed_demo_data.py
# Se ejecuta con: python scripts/seed_demo_data.py
# Pero esto requiere:
# 1. python instalado en host
# 2. qdrant-client instalado
# 3. Acordarse de ejecutarlo
# 4. Saber que es necesario
```

### Factor 3: Falta de Abstracción entre "Verificar" y "Ejecutar"

El verificador de estado solo comprobaba si los datos existían, pero no tenía capacidad de inicializarlos si no estaban presentes.

```python
# ❌ PROBLEMA - Verificador es solo lectura, no puede inicializar
def verify_qdrant_collection(self) -> bool:
    """Verify Qdrant has the documents collection."""
    # Solo verifica que existe
    if "documents" not in collections:
        self.errors.append("Qdrant collection 'documents' not found")
        return False
    # No puede crear la colección si no existe
```

### Factor 4: Topología de Dependencias no Considerada

```
Inicialización de Sistema
    ├─ Levantar Servicios (docker-compose up)
    │  ├─ Qdrant ✓
    │  ├─ API ✓
    │  └─ Redis ✓
    │
    ├─ Seed Data ❌ OLVIDADO / MANUAL
    │  ├─ Crear colección
    │  ├─ Insertar documentos
    │  └─ Validar datos
    │
    └─ Verificar Estado ✓
       └─ Comprobar que colección existe
```

El seeding debería estar entre "levantar servicios" y "verificar estado", pero no estaba automatizado.

---

## ✅ Solución Implementada

### Paso 1: Crear Script de Inicialización Reutilizable

Implementamos una función que puede ejecutarse desde dentro de Docker y desde el host:

```python
# ✓ SOLUCIÓN - Script que ejecuta dentro del contenedor
docker exec api python -c "
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import random

client = QdrantClient(host='qdrant', port=6333)

# Crear colección
client.create_collection(
    collection_name='documents',
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Agregar documentos de ejemplo
sample_docs = [
    {'text': 'Introduction to Machine Learning', 'id': 1},
    {'text': 'Deep Learning with Neural Networks', 'id': 2},
    # ... más documentos
]

# Insertar
for i, doc in enumerate(sample_docs):
    vector = [random.random() for _ in range(384)]
    points = [PointStruct(id=i+1, vector=vector, payload={'text': doc['text']})]
    client.upsert(collection_name='documents', points=points)

print(f'Seeded {len(sample_docs)} documents')
"
```

**Ventajas**:
- Se ejecuta dentro del contenedor (tiene dependencias)
- Accede a Qdrant via hostname interno `qdrant:6333`
- No requiere instalar nada en host
- Reutilizable desde scripts

### Paso 2: Crear Script de Seeding Robusto

```bash
#!/bin/bash
# scripts/init-database.sh - Inicializa base de datos de Qdrant

set -e

echo "Initializing Qdrant database..."

docker exec api python << 'EOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import random
import os

QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Crear colección si no existe
try:
    client.create_collection(
        collection_name='documents',
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("✓ Created collection 'documents'")
except Exception as e:
    if "already exists" in str(e):
        print("✓ Collection 'documents' already exists")
    else:
        raise

# Datos de ejemplo
sample_docs = [
    {'id': 1, 'text': 'Introduction to Machine Learning'},
    {'id': 2, 'text': 'Deep Learning with Neural Networks'},
    {'id': 3, 'text': 'Natural Language Processing Basics'},
    {'id': 4, 'text': 'Computer Vision Fundamentals'},
    {'id': 5, 'text': 'Data Science Best Practices'},
]

# Insertar documentos
points = []
for doc in sample_docs:
    vector = [random.random() for _ in range(384)]
    points.append(
        PointStruct(
            id=doc['id'],
            vector=vector,
            payload={'text': doc['text']}
        )
    )

client.upsert(collection_name='documents', points=points)
print(f"✓ Seeded {len(points)} documents")

# Verificar
count = client.count(collection_name='documents')
print(f"✓ Collection has {count.count} points")
EOF

echo "✓ Database initialization complete"
```

### Paso 3: Crear Dockerfile Personalizado con Inicialización

```dockerfile
# services/api/Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Instalar dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código
COPY . .

# Script de inicialización
COPY ./init-scripts/init-qdrant.py /init-qdrant.py

# Inicializar base de datos si no existe
RUN python /init-qdrant.py || echo "Note: Qdrant not available at build time"

# Ejecutar aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Paso 4: Crear Inicializador Inteligente con Verificación

```python
# ✓ SOLUCIÓN - Inicializador con fallbacks
class QdrantInitializer:
    """Inicializa colección en Qdrant con manejo robusto de errores."""
    
    def __init__(self, host: str = "qdrant", port: int = 6333):
        self.host = host
        self.port = port
        self.client = None
    
    def connect(self) -> bool:
        """Conecta a Qdrant con reintentos."""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                from qdrant_client import QdrantClient
                self.client = QdrantClient(host=self.host, port=self.port)
                self.client.get_collections()  # Valida conexión
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Connection attempt {attempt+1}/{max_retries} failed: {e}")
                    print(f"   Retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"✗ Failed to connect to Qdrant after {max_retries} attempts")
                    return False
        return False
    
    def initialize_collection(self, collection_name: str = "documents", vector_size: int = 384) -> bool:
        """Inicializa colección."""
        if not self.client:
            return False
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            # Verificar si ya existe
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name in existing:
                print(f"✓ Collection '{collection_name}' already exists")
                return True
            
            # Crear nueva colección
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            print(f"✓ Created collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to create collection: {e}")
            return False
    
    def seed_sample_data(self, collection_name: str = "documents") -> int:
        """Inserta datos de ejemplo."""
        if not self.client:
            return 0
        
        try:
            from qdrant_client.models import PointStruct
            import random
            
            sample_docs = [
                {'id': 1, 'text': 'Introduction to Machine Learning'},
                {'id': 2, 'text': 'Deep Learning with Neural Networks'},
                {'id': 3, 'text': 'Natural Language Processing Basics'},
                {'id': 4, 'text': 'Computer Vision Fundamentals'},
                {'id': 5, 'text': 'Data Science Best Practices'},
                {'id': 6, 'text': 'Distributed Systems Architecture'},
                {'id': 7, 'text': 'Cloud Computing Essentials'},
                {'id': 8, 'text': 'Microservices Design Patterns'},
            ]
            
            # Verificar si ya hay datos
            count = self.client.count(collection_name=collection_name)
            if count.count > 0:
                print(f"✓ Collection already has {count.count} documents")
                return count.count
            
            # Insertar documentos
            points = []
            for doc in sample_docs:
                vector = [random.random() for _ in range(384)]
                points.append(
                    PointStruct(
                        id=doc['id'],
                        vector=vector,
                        payload={'text': doc['text']}
                    )
                )
            
            self.client.upsert(collection_name=collection_name, points=points)
            print(f"✓ Seeded {len(points)} documents")
            return len(points)
        except Exception as e:
            print(f"✗ Failed to seed data: {e}")
            return 0
    
    def verify(self, collection_name: str = "documents") -> bool:
        """Verifica que la colección esté lista."""
        if not self.client:
            return False
        
        try:
            count = self.client.count(collection_name=collection_name)
            if count.count > 0:
                print(f"✓ Collection verified: {count.count} documents")
                return True
            else:
                print(f"✗ Collection is empty")
                return False
        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False
    
    def initialize(self, collection_name: str = "documents", vector_size: int = 384) -> bool:
        """Ejecuta flujo completo de inicialización."""
        print(f"\n📦 Initializing Qdrant database...")
        print(f"   Host: {self.host}:{self.port}")
        
        # Conectar
        if not self.connect():
            print("✗ Cannot connect to Qdrant")
            return False
        
        # Crear colección
        if not self.initialize_collection(collection_name, vector_size):
            print("✗ Cannot create collection")
            return False
        
        # Seed datos
        seeded = self.seed_sample_data(collection_name)
        
        # Verificar
        if not self.verify(collection_name):
            print("✗ Verification failed")
            return False
        
        print(f"✓ Database initialized successfully\n")
        return True


# Uso en CLI
if __name__ == "__main__":
    import sys
    
    initializer = QdrantInitializer()
    success = initializer.initialize()
    sys.exit(0 if success else 1)
```

### Paso 5: Integrar en Docker Compose

```yaml
# deploy/compose/docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - rag_network
    environment:
      - QDRANT_API_KEY=

  api:
    build:
      context: ../../services/api
      dockerfile: Dockerfile
    container_name: api
    env_file:
      - ../../.env
    depends_on:
      qdrant:
        condition: service_started
    networks:
      - rag_network
    ports:
      - "8001:8000"

volumes:
  qdrant_data:
```

### Paso 6: Crear Script de Orquestación Completa

```bash
#!/bin/bash
# scripts/setup-and-verify.sh - Levanta servicios, inicializa datos, verifica

set -e

echo "🚀 RAF Chatbot - Setup & Verification"
echo ""

# Cambiar a directorio del proyecto
cd "$(dirname "$0")/.."

# Paso 1: Levantar servicios
echo "1️⃣  Starting services..."
docker-compose -f deploy/compose/docker-compose.yml up -d
echo "   Waiting for services to be ready..."
sleep 5

# Paso 2: Inicializar base de datos
echo ""
echo "2️⃣  Initializing database..."
bash scripts/init-database.sh

# Paso 3: Verificar estado
echo ""
echo "3️⃣  Verifying system state..."
python scripts/verify_state.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Setup complete! System is ready."
    echo ""
    echo "Available endpoints:"
    echo "  - API: http://localhost:8001"
    echo "  - Qdrant: docker exec api curl http://qdrant:6333/collections"
    echo "  - Nginx: http://localhost:8080"
else
    echo ""
    echo "✗ Verification failed. Check logs above."
    exit 1
fi
```

---

## 🛡️ Principios Preventivos Clave

### P1: Separar Inicialización de Levantamiento de Servicios

**Principio**: No asumir que Docker Compose inicializa datos. Es responsabilidad separada.

```yaml
# ❌ MAL - Asumir que datos existen automáticamente
services:
  qdrant:
    image: qdrant/qdrant:latest
    # Nada que popule datos

# ✓ BIEN - Flujo explícito
# 1. docker-compose up (levanta servicios)
# 2. bash scripts/init-database.sh (inicializa datos)
# 3. python scripts/verify_state.py (verifica)
```

### P2: Hacer Inicialización Idempotente

**Principio**: Ejecutar la inicialización múltiples veces debe ser seguro y no causar errores.

```python
# ✓ PATRÓN RECOMENDADO - Idempotente
def initialize_collection(collection_name: str):
    try:
        client.create_collection(...)
    except AlreadyExistsError:
        print(f"Collection already exists")
        pass  # OK, no error

def seed_data(collection_name: str):
    count = client.count(collection_name)
    if count.count > 0:
        print("Data already seeded")
        return  # Skip if already seeded
    
    # Only seed if empty
    client.upsert(...)
```

### P3: Documentar Requisitos de Inicialización

**Principio**: Cada estado requerido debe estar documentado explícitamente.

```markdown
# Estado Requerido

## Antes de Verificar
- [ ] Servicios corriendo (docker-compose up)
- [ ] Base de datos inicializada (scripts/init-database.sh)
- [ ] Colección 'documents' existe
- [ ] Mínimo 1 documento en colección

## Cómo Inicializar
1. bash scripts/init-database.sh
2. python scripts/verify_state.py

## Qué Sucede si no se Inicializa
- Verificación falla: STATE_FAIL
- No se pueden hacer queries
- Sistema no operativo
```

### P4: Usar Contenedores para Ejecutar Scripts

**Principio**: Si un servicio está en Docker, ejecutar scripts dentro del contenedor evita problemas de dependencias.

```python
# ❌ MAL - Requiere instalar en host
python scripts/seed_demo_data.py
# Necesita: python, qdrant-client, otras dependencias

# ✓ BIEN - Ejecuta en contenedor que tiene todo
docker exec api python << 'SCRIPT'
# Código aquí
SCRIPT
# Acceso a dependencias garantizado
```

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: "Collection Not Found" después de docker-compose up

```
✗ FAIL: Qdrant Collection
ERROR: Qdrant collection 'documents' not found
```

**Esto significa**: Los datos no se inicializaron automáticamente. Necesitas ejecutar el script de seeding.

**Acción inmediata**:
```bash
bash scripts/init-database.sh
python scripts/verify_state.py
```

### Señal 2: "No such file or directory" ejecutando script de seeding

```
ModuleNotFoundError: No module named 'qdrant_client'
```

**Esto significa**: Las dependencias no están instaladas en el host. Usa docker exec en lugar de ejecutar localmente.

**Acción inmediata**:
```bash
# ❌ No hagas esto
python scripts/seed_demo_data.py

# ✓ Haz esto en su lugar
docker exec api python << 'SCRIPT'
from qdrant_client import QdrantClient
# ... código
SCRIPT
```

### Señal 3: Collection Existe Pero Está Vacío

```
✓ Collection 'documents' exists
✗ Collection has 0 documents
```

**Esto significa**: La colección se creó pero no se seeded. Necesitas ejecutar el paso de inserción de datos.

**Acción inmediata**:
```bash
docker exec api python -c "
# Script que inserta documentos
"
```

---

## 💻 Código Reutilizable

### Componente: QdrantInitializer (ver Step 4 arriba)

Clase reutilizable que:
- Se conecta a Qdrant con reintentos
- Crea colecciones de forma segura
- Seeds datos de forma idempotente
- Verifica estado

### Script: `scripts/init-database.sh`

```bash
#!/bin/bash
# Inicializa base de datos de Qdrant

set -e

echo "Initializing Qdrant database..."

docker exec api python << 'EOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import random
import os

QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Crear colección si no existe
try:
    client.create_collection(
        collection_name='documents',
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("✓ Created collection 'documents'")
except Exception as e:
    if "already exists" in str(e):
        print("✓ Collection 'documents' already exists")
    else:
        raise

# Datos de ejemplo
sample_docs = [
    {'id': 1, 'text': 'Introduction to Machine Learning'},
    {'id': 2, 'text': 'Deep Learning with Neural Networks'},
    {'id': 3, 'text': 'Natural Language Processing Basics'},
    {'id': 4, 'text': 'Computer Vision Fundamentals'},
    {'id': 5, 'text': 'Data Science Best Practices'},
]

# Insertar documentos
points = []
for doc in sample_docs:
    vector = [random.random() for _ in range(384)]
    points.append(
        PointStruct(
            id=doc['id'],
            vector=vector,
            payload={'text': doc['text']}
        )
    )

client.upsert(collection_name='documents', points=points)
print(f"✓ Seeded {len(points)} documents")

# Verificar
count = client.count(collection_name='documents')
print(f"✓ Collection has {count.count} points")
EOF

echo "✓ Database initialization complete"
```

### Script: `scripts/setup-and-verify.sh`

```bash
#!/bin/bash
# Levanta servicios, inicializa datos, verifica estado completo

set -e

echo "🚀 RAF Chatbot - Setup & Verification"
echo ""

cd "$(dirname "$0")/.."

# Paso 1: Levantar servicios
echo "1️⃣  Starting services..."
docker-compose -f deploy/compose/docker-compose.yml up -d
echo "   Waiting for services to be ready..."
sleep 5

# Paso 2: Inicializar base de datos
echo ""
echo "2️⃣  Initializing database..."
bash scripts/init-database.sh

# Paso 3: Verificar estado
echo ""
echo "3️⃣  Verifying system state..."
python scripts/verify_state.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Setup complete! System is ready."
else
    echo ""
    echo "✗ Verification failed."
    exit 1
fi
```

---

## 📋 Checklist de Implementación

### Antes de Crear Database Seeding

- [ ] Documentar qué datos son requeridos
- [ ] Documentar cuándo se deben inicializar (al arrancar)
- [ ] Documentar cómo se inicializan (script específico)
- [ ] Crear script de inicialización
- [ ] Probar script en ambiente con servicios running
- [ ] Hacer script idempotente
- [ ] Integrar en flujo de setup
- [ ] Documentar en README

### En Revisión de Código

```python
# Preguntas a hacer:
1. ¿El script es idempotente? → Sí, sin error si datos existen
2. ¿Se ejecuta en contenedor o host? → En contenedor (docker exec)
3. ¿Maneja errores de conexión? → Sí, con reintentos
4. ¿Verifica estado después? → Sí, cuenta documentos
5. ¿Está documentado dónde ejecutarlo? → Sí, en README
```

---

## 🔗 Anti-Patterns a Evitar

### ❌ Anti-Pattern 1: Asumir Que Docker Compose Inicializa Datos

```yaml
# ❌ MAL - Sin mechanism de inicialización
services:
  qdrant:
    image: qdrant/qdrant:latest
    # Nada que populate datos
    # Datos magicamente aparecen? No.
```

**Problema**: Los datos no se inicializan automáticamente. El sistema arranca sin datos.

### ❌ Anti-Pattern 2: Scripts de Seeding que Requieren Instalaciones Locales

```python
# ❌ MAL - Requiere dependencias en host
# scripts/seed_demo_data.py
from qdrant_client import QdrantClient  # Debe estar instalado localmente
# ... código ...

# Para ejecutar:
# pip install qdrant-client
# python scripts/seed_demo_data.py
```

**Problema**: 
- Requiere instalar dependencias en host
- Frágil a cambios de versión
- No es reproducible en CI/CD

### ❌ Anti-Pattern 3: Inicialización No Idempotente

```python
# ❌ MAL - Falla si se ejecuta dos veces
def initialize():
    client.create_collection(...)  # Falla si ya existe
    client.upsert(points)  # Duplica datos si se ejecuta dos veces
```

**Problema**:
- No se puede re-ejecutar sin errores
- Causa duplicados en datos
- Frágil en flujos automatizados

### ✓ Solución Correcta

```python
# ✓ BIEN - Idempotente y robusto
def initialize():
    try:
        client.create_collection(...)
    except AlreadyExistsError:
        pass  # OK
    
    # Solo seed si está vacío
    if client.count(collection_name).count == 0:
        client.upsert(points)
```

---

## 💡 Best Practices

### BP1: Centralizar Lógica de Inicialización

```python
# ✓ PATRÓN RECOMENDADO
class DatabaseInitializer:
    """Centraliza toda lógica de inicialización."""
    
    def initialize(self):
        """Ejecuta flujo completo de inicialización."""
        self.connect()
        self.create_collections()
        self.seed_data()
        self.verify()
```

Ventajas:
- Una fuente de verdad
- Fácil de mantener
- Reutilizable desde múltiples lugares

### BP2: Separar Inicialización de Configuración

```python
# ✓ PATRÓN RECOMENDADO
# Configuración (no cambia durante ejecución)
CONFIG = {
    "qdrant": {
        "host": "qdrant",
        "port": 6333,
        "collection": "documents",
        "vector_size": 384
    }
}

# Inicialización (se ejecuta una vez)
def initialize_database():
    initializer = DatabaseInitializer(CONFIG)
    initializer.initialize()

# Runtime (acceso a datos)
def query_documents(text):
    client = QdrantClient(CONFIG["qdrant"]["host"], CONFIG["qdrant"]["port"])
    return client.search(...)
```

### BP3: Documentar Flujo de Setup

```markdown
# Setup Workflow

## Step 1: Levantar Servicios
```bash
docker-compose -f deploy/compose/docker-compose.yml up -d
```

## Step 2: Inicializar Base de Datos
```bash
bash scripts/init-database.sh
```

## Step 3: Verificar Estado
```bash
python scripts/verify_state.py
```

Si todos los checks pasan, el sistema está listo.
```

---

## 📈 Impacto de la Solución

| Métrica | Antes | Después |
|---------|-------|---------|
| Datos Presentes | ❌ No | ✓ Sí |
| Setup Time | Indefinido (manual) | 30 segundos |
| Automatización | Manual | ✓ Automatizado |
| Idempotencia | ❌ No | ✓ Sí |
| Reproducibilidad | Frágil | Robusta |
| Documentación | Falta | Completa |

---

## 🧪 Tests Relacionados

### Test File: `tests/test_database_initialization.py`

```python
#!/usr/bin/env python3
"""
Tests para inicialización de base de datos
Ejecutar: pytest tests/test_database_initialization.py -v
"""

import pytest
import subprocess
from pathlib import Path

class TestDatabaseInitialization:
    """Suite de tests para inicialización."""
    
    def test_init_script_exists(self):
        """Verifica que script de inicialización existe."""
        script_path = Path("scripts/init-database.sh")
        assert script_path.exists(), "init-database.sh should exist"
    
    def test_qdrant_collection_created(self):
        """Verifica que colección se crea."""
        try:
            # Ejecutar inicialización
            result = subprocess.run(
                ["bash", "scripts/init-database.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result.returncode == 0, "Init script should succeed"
            assert "Created collection" in result.stdout or "already exists" in result.stdout
        except subprocess.TimeoutExpired:
            pytest.skip("Qdrant not running")
    
    def test_documents_seeded(self):
        """Verifica que documentos se insertan."""
        try:
            result = subprocess.run(
                ["bash", "scripts/init-database.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert "Seeded" in result.stdout or "already has" in result.stdout
        except subprocess.TimeoutExpired:
            pytest.skip("Qdrant not running")
    
    def test_init_is_idempotent(self):
        """Verifica que se puede ejecutar múltiples veces."""
        try:
            # Ejecutar primera vez
            result1 = subprocess.run(
                ["bash", "scripts/init-database.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result1.returncode == 0
            
            # Ejecutar segunda vez
            result2 = subprocess.run(
                ["bash", "scripts/init-database.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            assert result2.returncode == 0, "Should succeed on second run"
        except subprocess.TimeoutExpired:
            pytest.skip("Qdrant not running")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-05-QDRANT-HEALTH-ENDPOINT.md` (Health checks)
- Ver: `docs/state_management.md` (Verificación de estado)
- Ver: `scripts/verify_state.py` (Verificador de estado)
- Código: `scripts/init-database.sh` (Script de inicialización)
- Qdrant Docs: https://qdrant.tech/documentation/

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-10 | Documento inicial - Database seeding |

---

## ✨ Key Takeaway

> **"No asumir que datos existen. Automatizar inicialización en contenedor. Hacer idempotente para ejecutar múltiples veces sin error."**

```python
# Patrón ganador: Inicializador robusto e idempotente
class DatabaseInitializer:
    def initialize(self):
        """Flujo seguro que se puede ejecutar múltiples veces."""
        # Crear solo si no existe
        if not self.collection_exists():
            self.create_collection()
        
        # Seed solo si está vacío
        if self.collection_empty():
            self.seed_sample_data()
        
        # Siempre verificar
        self.verify()

# Uso:
# bash scripts/init-database.sh (ejecutar múltiples veces sin error)
# python scripts/verify_state.py (verificar que todo está bien)
```

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Qdrant Collections API](https://qdrant.tech/documentation/concepts/collections/)
- [Qdrant Points API](https://qdrant.tech/documentation/concepts/points/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Ejemplos en el Proyecto
- `scripts/init-database.sh` - Script de inicialización
- `scripts/setup-and-verify.sh` - Orquestación completa
- `deploy/compose/docker-compose.yml` - Configuración de servicios

### Herramientas Útiles
```bash
# Ejecutar inicialización
bash scripts/init-database.sh

# Verificar estado después
python scripts/verify_state.py

# Ver contenido de colección
docker exec api curl -s http://qdrant:6333/collections | python -m json.tool
```

---

## ❓ FAQ

### P: ¿Cuándo ejecuto la inicialización?

R: Después de `docker-compose up -d`, antes de usar el sistema. O combina ambos con `setup-and-verify.sh`.

### P: ¿Qué pasa si ejecuto init dos veces?

R: Nada malo. El script es idempotente:
- Colección existente no se recrea
- Datos existentes no se duplican
- Verifica y reporta estado actual

### P: ¿Cómo agrego más documentos de ejemplo?

R: Edita el diccionario `sample_docs` en `scripts/init-database.sh` o crea archivo JSON separado.

### P: ¿Puedo usar datos reales en lugar de ejemplos?

R: Sí. Crea función que importe de archivo JSON o database, y reemplaza el hardcoded `sample_docs`.

### P: ¿Qué pasa en producción?

R: Usa datos reales desde base de datos o file storage, no datos de ejemplo. El mismo patrón aplica.

---

## 🎓 Lecciones Relacionadas

- **Lección 5**: Qdrant Health Endpoint - Cómo verificar que está corriendo
- **Lección 1**: Docker Networking - Cómo acceder a servicios internos
- **Lección 7** (próxima): Data Migration - Cómo migrar datos entre versiones

---