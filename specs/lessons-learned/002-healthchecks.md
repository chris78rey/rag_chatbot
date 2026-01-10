# Lección Aprendida: Healthchecks en Docker Compose

## 📋 Problema

Al intentar levantar los servicios Docker (Subproyecto 2), los healthchecks fallaban:
- Qdrant: `test: ["CMD", "curl", "-f", "http://localhost:6333/health"]` → **FALLÓ** (curl no disponible)
- Redis: `test: ["CMD", "redis-cli", "ping"]` → **FALLÓ** (redis-cli no en PATH)
- API: `test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]` → **FALLÓ** (wget no disponible)

Los contenedores no se iniciaban porque dependían de healthchecks que nunca pasaban.

---

## 🔍 Causa Raíz

### 1. **Herramientas no disponibles en imágenes base**
- `qdrant/qdrant:latest` no incluye `curl` ni `wget`
- `redis:7-alpine` no incluye `redis-cli` de forma accesible en healthcheck
- Asumimos que herramientas estándar estarían disponibles (incorrecto)

### 2. **Falta de validación antes del despliegue**
- No se verificó si las imágenes oficiales tenían las herramientas necesarias
- No se testeo el healthcheck localmente antes de usarlo

### 3. **Overhead innecesario en imágenes lean**
- Las imágenes `alpine` de propósito específico eliminan herramientas para mantener tamaño pequeño
- Qdrant es una imagen especializada, no una imagen general

---

## ✅ Soluciones Implementadas

### **Solución 1: Remover healthchecks problemáticos**
```yaml
# ANTES (FALLA)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
  interval: 10s
  timeout: 5s
  retries: 5

# DESPUÉS (OK)
# Sin healthcheck - usar service_started en lugar de service_healthy
```

### **Solución 2: Usar `service_started` en lugar de `service_healthy`**
```yaml
# ANTES
depends_on:
  qdrant:
    condition: service_healthy
  redis:
    condition: service_healthy

# DESPUÉS
depends_on:
  qdrant:
    condition: service_started
  redis:
    condition: service_started
```

### **Solución 3: Healthcheck alternativo con herramientas integradas**
```yaml
# Usando python (disponible en cualquier imagen Python 3.x)
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

## 🛡️ Principios Preventivos Clave

### **Principio 1: Conocer la imagen base**
Antes de usar cualquier herramienta en un healthcheck, verificar qué incluye:
```bash
# Validar qué está disponible en la imagen
docker run --rm qdrant/qdrant:latest which curl    # Resultado: not found
docker run --rm qdrant/qdrant:latest which wget    # Resultado: not found
docker run --rm redis:7-alpine which redis-cli     # Resultado: /usr/local/bin/redis-cli
```

### **Principio 2: Usar herramientas incluidas en la imagen**
- **Python images** → usar `python -c` con `urllib`
- **Node images** → usar `node -e` con `fetch`
- **Go images** → escribir pequeño script Go
- **Minimal images** → sin healthcheck (usar `service_started`)

### **Principio 3: Validar antes de deployar**
```bash
# Testear el healthcheck localmente
docker run --rm qdrant/qdrant:latest sh -c "curl http://localhost:6333/health"
# Si falla, usar alternativa
```

### **Principio 4: Degradación elegante**
Si no hay forma de hacer healthcheck confiable:
- Usar `service_started` (esperar a que inicie el proceso)
- Agregar logs que muestren cuando está listo
- Documentar el tiempo aproximado de startup

---

## 🚨 Señales de Activación

### **Señal 1: Error `dependency failed to start: container X is unhealthy`**
- **Acción inmediata**: Revisar qué herramienta usa el healthcheck
- **Verificación**: `docker run --rm <image> which <tool>`
- **Si no existe**: Cambiar a `service_started` o reescribir healthcheck

### **Señal 2: Timeout en levantamiento de servicios**
- Indica healthcheck que nunca pasa
- **Debug**: `docker logs <container>` para ver si algo está roto
- **Fallback**: Remover healthcheck y usar `service_started`

### **Señal 3: Cambio de versión de imagen base**
- Cuando actualizamos `redis:7-alpine` → `redis:8-alpine`
- **Validar**: Confirmar que herramientas sigan siendo válidas
- **Retest**: Ejecutar todo el stack nuevamente

---

## 💡 Snippet Reutilizable: Script de Validación de Healthchecks

```bash
#!/bin/bash
# File: scripts/validate-healthchecks.sh
# Purpose: Validar que todas las herramientas de healthcheck están disponibles

set -e

IMAGES=(
  "qdrant/qdrant:latest:curl"
  "redis:7-alpine:redis-cli"
  "python:3.11-slim:python"
)

echo "🔍 Validando disponibilidad de herramientas en imágenes..."

for entry in "${IMAGES[@]}"; do
  IFS=: read -r image tool <<< "$entry"
  
  echo -n "  ▸ $image:$tool ... "
  
  if docker run --rm "$image" which "$tool" &>/dev/null; then
    echo "✅ OK"
  else
    echo "❌ NO ENCONTRADO"
    echo "    Recomendación: Usar service_started o escribir healthcheck alternativo"
  fi
done

echo ""
echo "✅ Validación completada"
```

---

## 📊 Matriz de Decisión: ¿Qué tipo de healthcheck usar?

| Imagen | Herramienta Recomendada | Fallback |
|--------|------------------------|---------| 
| `qdrant/qdrant` | Remover (usar `service_started`) | N/A |
| `redis:7-alpine` | `redis-cli ping` | Remover |
| `python:3.x` | `python -c "urllib.request..."` | `service_started` |
| `node:xx` | `node -e "fetch('http://...')"` | `service_started` |
| `nginx:alpine` | Remover (muy rápido startup) | N/A |

---

## 🔄 Aplicación al Proyecto

**Archivo afectado**: `deploy/compose/docker-compose.yml`

**Cambio final**:
```yaml
# ✅ Configuración correcta
depends_on:
  qdrant:
    condition: service_started  # NO service_healthy
  redis:
    condition: service_started  # NO service_healthy
# Sin healthcheck en imágenes que no lo soporten
```

---

## 📚 Referencias

- [Docker Compose Healthcheck Documentation](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Qdrant Docker Image](https://hub.docker.com/r/qdrant/qdrant)
- [Redis Docker Image](https://hub.docker.com/_/redis)

---

## ✏️ Checklist para próximos subproyectos

- [ ] Antes de agregar healthcheck, validar herramienta con `docker run ... which <tool>`
- [ ] Documentar por qué se eligió ese healthcheck (o por qué se removió)
- [ ] Testear localmente: `docker-compose up -d` debe levantar sin errores
- [ ] Agregar script de validación en CI/CD si aplica