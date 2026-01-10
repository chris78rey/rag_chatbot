# Lección Aprendida: Gestión de Puertos en Docker Compose

## 📋 Resumen Ejecutivo
Error al intentar exponer puerto 80 de Nginx porque ya estaba en uso en el host.

---

## 🔴 Problema
```
Error response from daemon: ports are not available: exposing port TCP 127.0.0.1:80 -> 127.0.0.1:0: 
listen tcp4 127.0.0.1:80: bind: Intento de acceso a un socket no permitido por sus permisos de acceso.
```

Los contenedores fallaban al intentar iniciar porque:
1. Puerto 80 ya estaba en uso en el host
2. Intentos posteriores fallaban porque Qdrant aún estaba corriendo
3. Sin limpiar volúmenes, el docker-compose.yml no se regeneraba correctamente

---

## 🎯 Causa Raíz

| Nivel | Descripción |
|-------|------------|
| **Inmediato** | Puerto 80 ocupado por otro proceso en el host |
| **Systémico** | No hay validación previa de disponibilidad de puertos |
| **Preventivo** | No existe documentación de qué puertos debe usar cada servicio |

---

## ✅ Solución Implementada

### Antes (Falla)
```yaml
nginx:
  ports:
    - "80:80"  # Puerto del host ocupado
```

### Después (Éxito)
```yaml
nginx:
  ports:
    - "8080:80"  # Usar puerto alternativo en el host
```

---

## 🛡️ Principio Preventivo Clave

**"Nunca usar puertos menores a 1024 en desarrollo local sin validar que están disponibles."**

### Reglas:
1. **Puertos < 1024**: Requieren privilegios de admin. Evitar en dev.
2. **Puertos 1024-49151**: Rango seguro para aplicaciones.
3. **Puertos 49152-65535**: Rango dinámico (efímero), evitar para servicios fijos.
4. **Convención del proyecto**: Usar rango 8000-8999 para servicios en dev.

---

## 🚨 Señal de Activación (Cómo Detectar Futuro)

### Señal 1: Verificación Automática Pre-deployment
```bash
# Antes de docker compose up, validar puertos
docker compose config | grep -A 2 "ports:" | grep ":" | cut -d: -f2 | sort | uniq
```

### Señal 2: Documentación de Mapeo
Crear archivo `PORT_MAP.md` en la raíz del proyecto:
```
# Puerto Mappings

| Servicio | Puerto Host | Puerto Container | Propósito |
|----------|------------|------------------|-----------|
| Nginx | 8080 | 80 | Reverse proxy |
| FastAPI | (interno) | 8000 | API |
| Qdrant | (interno) | 6333 | Vector DB |
| Redis | (interno) | 6379 | Cache/Queue |
```

### Señal 3: Health Check Script
```bash
#!/bin/bash
# check_ports.sh - Ejecutar antes de docker compose up

PORTS=(8080 8000 6333 6379)
USED_PORTS=()

for port in "${PORTS[@]}"; do
  if lsof -i :$port >/dev/null 2>&1; then
    USED_PORTS+=($port)
  fi
done

if [ ${#USED_PORTS[@]} -gt 0 ]; then
  echo "⚠️ Puertos en uso: ${USED_PORTS[@]}"
  exit 1
else
  echo "✅ Todos los puertos disponibles"
  exit 0
fi
```

---

## 📦 Snippet Reutilizable: Docker Compose Port Manager

```yaml
# docker-compose.yml - VERSIÓN SEGURA CON VALIDACIÓN

version: "3.9"

services:
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      # Mapeo claro: HOST:CONTAINER
      # Puerto 8080 es la puerta de entrada pública
      - "8080:80"
    environment:
      - PORT_MAPPING="8080->80"

  api:
    image: my-api:latest
    container_name: api
    expose:
      # Port 8000 SOLO para comunicación interna
      # NO exponemos al host
      - "8000"
    environment:
      - INTERNAL_PORT=8000

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    # MEJOR: No exponer puertos internos al host
    # Acceder solo via nombre de servicio (qdrant:6333)
    environment:
      - QDRANT_API_PORT=6333

  redis:
    image: redis:7-alpine
    container_name: redis
    # Sin expose: Solo accesible por nombre de servicio
    environment:
      - REDIS_PORT=6379
```

### Script Auxiliar para Debugging
```bash
#!/bin/bash
# show_docker_ports.sh

echo "🔍 Puertos Docker Actuales:"
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo -e "\n🔍 Puertos Escuchando en Host:"
netstat -tlnp 2>/dev/null | grep LISTEN || lsof -i -P -n | grep LISTEN

echo -e "\n🔍 Configuración en docker-compose.yml:"
docker compose config | grep -B 3 "ports:" || echo "Ninguno"
```

---

## 📊 Comparativa: Antes vs Después

| Aspecto | ❌ Antes | ✅ Después |
|---------|---------|-----------|
| Puerto Nginx | 80 (falla) | 8080 (éxito) |
| Exposición Qdrant | localhost:6333 | Interno solo |
| Exposición Redis | localhost:6379 | Interno solo |
| Documentación | Ninguna | PORT_MAP.md |
| Validación | Manual/error | Script automático |
| Startup Time | 2-3 min (debug) | <1 min |

---

## 🔗 Referencias Relacionadas

- **Lección 001**: Versionado de dependencias
- **Lección 002**: Health checks
- **Docker Docs**: [Port publishing](https://docs.docker.com/config/containers/container-networking/)

---

## 📝 Acciones Inmediatas

- [ ] Crear `scripts/check_ports.sh` y agregarlo al pre-deployment
- [ ] Documentar mapeo de puertos en `PORT_MAP.md`
- [ ] Actualizar `docker-compose.yml` para no exponer servicios internos
- [ ] Añadir validación de puertos al CI/CD
