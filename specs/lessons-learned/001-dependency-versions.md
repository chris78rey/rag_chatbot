# Lección Aprendida 001: Gestión de Versiones de Dependencias en Docker

## 📋 Resumen Ejecutivo
Las versiones especificadas en `requirements.txt` deben validarse contra PyPI antes de construir imágenes Docker. Versiones inexistentes causan fallos de build costosos (tiempo + recursos).

---

## 🔴 Problema

**Síntoma:**
```
ERROR: No matching distribution found for qdrant-client==2.7.0
```

**Contexto:**
- `requirements.txt` especificaba `qdrant-client==2.7.0`
- Build Docker falló en el paso `RUN pip install`
- El error no fue detectado hasta la construcción, no durante la planificación

**Impacto:**
- ⏱️ Retraso de ~3 minutos por intento fallido
- 🔄 Múltiples reintentos necesarios
- 🗂️ Capas Docker intermedias acumuladas

---

## 🔍 Causa Raíz

1. **Especificación manual de versiones** sin validación contra PyPI
2. **Falta de pin de versiones correctas** - qdrant-client máxima disponible: 1.16.2
3. **No existe proceso de validación previo** a build
4. **Documentación desactualizada** o copiada de ejemplo no verificado

**Análisis de Raíz:**
```
Especificación Manual
      ↓
Sin Validación PyPI
      ↓
Versión No Existe
      ↓
Build Fail en Docker Build
      ↓
Ciclo Roto
```

---

## ✅ Solución

### Corto Plazo (Implementado)
Reemplazar versiones inválidas con versiones conocidas:
```
# ❌ ANTES (inválido)
qdrant-client==2.7.0

# ✅ DESPUÉS (válido)
qdrant-client==1.16.2
```

### Largo Plazo (Preventivo)

**Opción 1: Validar Antes de Commit**
```bash
# Script: scripts/validate-requirements.sh
#!/bin/bash
set -e

for file in services/api/requirements.txt services/ingest/requirements.txt; do
    echo "Validating $file..."
    while IFS= read -r line; do
        if [[ $line =~ ^[a-zA-Z] ]] && [[ $line == *"=="* ]]; then
            pkg=$(echo "$line" | cut -d= -f1)
            version=$(echo "$line" | cut -d= -f3)
            
            # Validar contra PyPI
            if ! pip index versions "$pkg" 2>/dev/null | grep -q "$version"; then
                echo "❌ INVALID: $line"
                exit 1
            fi
        fi
    done < "$file"
done

echo "✅ All requirements validated"
```

**Opción 2: Usar Ranges en Lugar de Pins Exactos**
```
# Más flexible, pero requiere testing
fastapi>=0.104.0,<0.105.0
qdrant-client>=1.16.0,<2.0.0
redis>=5.0.0,<6.0.0
```

**Opción 3: Pre-build Check en Docker (Recomendado)**
```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Copiar requirements
COPY requirements.txt .

# PASO 1: Validar sintaxis y disponibilidad
RUN pip install --dry-run -r requirements.txt 2>&1 | tee /tmp/check.log && \
    if grep -q "No matching distribution" /tmp/check.log; then \
        echo "❌ Invalid versions in requirements.txt"; \
        exit 1; \
    fi

# PASO 2: Instalar efectivamente
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🛡️ Principio Preventivo Clave

**"Validar Dependencias en Tiempo de Especificación, No en Build"**

- ✅ Crear script de validación en `scripts/validate-requirements.sh`
- ✅ Ejecutar en CI/CD antes de docker build
- ✅ Documentar proceso en `docs/development.md`
- ✅ Pre-validar con `pip index versions <package>`

---

## 🚨 Señales de Activación (Early Warning)

Cuando veas estos patrones, DETENTE Y VALIDA:

```
🔔 Señal 1: Versiones "nuevas" copiadas de documentación externa
🔔 Señal 2: requirements.txt con versiones ==X.Y.Z sin testeo previo
🔔 Señal 3: Cambios en versiones sin testing local (pip install -r)
🔔 Señal 4: Primera construcción Docker sin validación previa
```

---

## 📝 Snippet Reutilizable

### Pre-commit Hook para Validar requirements.txt

**Archivo:** `scripts/pre-commit-validate.sh`
```bash
#!/bin/bash
# Hook para evitar commits con requirements.txt inválido
# Instalación: cp scripts/pre-commit-validate.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

REQUIREMENTS_FILES=(
    "services/api/requirements.txt"
    "services/ingest/requirements.txt"
)

echo "🔍 Validating requirements.txt files..."

for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$req_file" ]; then
        echo "  Checking: $req_file"
        
        # Test local install
        if ! pip install --dry-run -q -r "$req_file" 2>&1 | grep -q "Successfully"; then
            echo "❌ FAILED: $req_file has invalid packages"
            echo "   Run: pip install -r $req_file (locally first)"
            exit 1
        fi
    fi
done

echo "✅ All requirements.txt validated"
exit 0
```

### Script de Verificación Rápida

**Archivo:** `scripts/check-deps.py`
```python
#!/usr/bin/env python3
"""
Validar versiones de paquetes contra PyPI.
Uso: python scripts/check-deps.py services/api/requirements.txt
"""

import sys
import subprocess
from pathlib import Path

def validate_requirements(req_file: str) -> bool:
    """Validar archivo requirements.txt"""
    path = Path(req_file)
    
    if not path.exists():
        print(f"❌ File not found: {req_file}")
        return False
    
    print(f"🔍 Validating {req_file}...")
    
    # Ejecutar dry-run
    result = subprocess.run(
        ["pip", "install", "--dry-run", "-q", "-r", req_file],
        capture_output=True,
        text=True
    )
    
    if "No matching distribution" in result.stderr or result.returncode != 0:
        print(f"❌ INVALID packages in {req_file}")
        print(result.stderr)
        return False
    
    print(f"✅ {req_file} is valid")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check-deps.py <requirements.txt>")
        sys.exit(1)
    
    valid = validate_requirements(sys.argv[1])
    sys.exit(0 if valid else 1)
```

---

## 📊 Checklist de Implementación

- [ ] Crear `scripts/validate-requirements.sh`
- [ ] Crear `scripts/check-deps.py`
- [ ] Ejecutar validación antes de docker build
- [ ] Añadir verificación a CI/CD pipeline
- [ ] Documentar en `docs/development.md`
- [ ] Entrenar equipo en este proceso

---

## 🔗 Referencias y Links

- PyPI Package Index: https://pypi.org/
- pip install --dry-run: https://pip.pypa.io/en/latest/cli/pip_install/#cmdoption-dry-run
- Poetry (alternativa): https://python-poetry.org/docs/dependency-specification/

---

## Fecha Documentada
**2025-01-10** | Subproyectos 1-2 | raf_chatbot