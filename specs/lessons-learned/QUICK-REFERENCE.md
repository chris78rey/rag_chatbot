# ⚡ Quick Reference — Lecciones Aprendidas

**Propósito**: Acceso rápido a soluciones cuando encuentres errores.

---

## 🔍 Diagnosticar Problema → Encontrar Solución

### Error: "No matching distribution found for X==Y"
**→ Ver Lección 001**
```bash
# Acción rápida:
pip index versions PACKAGE_NAME
# Usar versión que aparece en output
```
**Checklist:**
- [ ] Validar versión con `pip index versions`
- [ ] Actualizar requirements.txt
- [ ] Ejecutar `docker compose build` nuevamente

---

### Error: "dependency failed to start: container X is unhealthy"
**→ Ver Lección 002**
```bash
# Acción rápida:
docker run --rm IMAGE_NAME which TOOL
# Si no existe, remover healthcheck
```
**Checklist:**
- [ ] Verificar qué herramienta usa el healthcheck
- [ ] Cambiar a `service_started` en lugar de `service_healthy`
- [ ] Ejecutar `docker compose up -d` nuevamente

---

### Error: "ports are not available: exposing port TCP"
**→ Ver Lección 003**
```bash
# Acción rápida:
lsof -i :PORT_NUMBER
# Si está en uso, cambiar a otro puerto
```
**Checklist:**
- [ ] Verificar qué usa el puerto con `lsof` o `netstat`
- [ ] Cambiar a puerto en rango 8000-8999
- [ ] Actualizar docker-compose.yml
- [ ] Ejecutar `docker compose up -d` nuevamente

---

### Error: "env file ... not found"
**→ Ver Lección 004**
```bash
# Acción rápida:
cp .env.example .env
# O ejecutar:
make init
```
**Checklist:**
- [ ] Crear .env desde .env.example
- [ ] Actualizar valores según tu entorno
- [ ] Verificar variables obligatorias:
  - `OPENROUTER_API_KEY`
  - `QDRANT_URL`
  - `REDIS_URL`

---

### Error: "Dockerfile not found for context"
**→ Ver Lección 006**
```bash
# Acción rápida:
# Crear archivo services/SERVICE/Dockerfile
# Ver template en 006-dockerfile-patterns.md
```
**Checklist:**
- [ ] Crear Dockerfile en directorio correcto
- [ ] Incluir `pip install -r requirements.txt`
- [ ] Definir `CMD` o `ENTRYPOINT`
- [ ] Ejecutar `docker compose build` nuevamente

---

### Volúmenes no montan correctamente en CI/CD
**→ Ver Lección 005**
```yaml
# CAMBIAR ESTO:
volumes:
  - ../../deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro

# A ESTO:
volumes:
  - ${PWD}/deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
```
**Checklist:**
- [ ] Reemplazar rutas relativas con `${PWD}`
- [ ] Usar volúmenes nombrados para datos persistentes
- [ ] Probar en diferentes directorios
- [ ] Ejecutar `docker compose config` para verificar

---

## 🛠️ Herramientas Rápidas

### Validar TODO antes de desplegar
```bash
make validate
# O ejecutar script directamente:
./scripts/validate-deployment.sh
```

### Ver estado de servicios
```bash
make docker-ps
# O:
docker compose -f deploy/compose/docker-compose.yml ps
```

### Ver logs en tiempo real
```bash
make docker-logs
# O específico:
make docker-logs-api
docker compose logs -f api
```

### Levantar servicios correctamente
```bash
make docker-up
# Esto ejecuta validación primero automáticamente
```

### Parar todo limpiamente
```bash
make docker-down
# Para borrar volúmenes también:
make docker-clean
```

---

## 📋 Checklist Pre-Push

- [ ] Ejecuté `make validate` (sin errores críticos)
- [ ] Probé cambios localmente con `make docker-up`
- [ ] Verifiqué con `curl http://localhost:8000/health`
- [ ] Revisé logs: `make docker-logs`
- [ ] Actualicé documentación si cambié algo importante
- [ ] No commiteé archivos sensibles (.env, secrets, etc)

---

## 🚨 Señales de Alerta (DETENTE Y LEER LECCIÓN)

| Señal | Lección | Acción |
|-------|---------|--------|
| Versión `==X.Y.Z` que nunca usaste antes | 001 | Validar con `pip index versions` |
| `curl: command not found` en logs | 002 | Cambiar a `service_started` |
| Puerto < 1024 en docker-compose | 003 | Usar rango 8000-8999 |
| Primera vez usando proyecto | 004 | Ejecutar `make init` |
| Paths con `../../` en volúmenes | 005 | Cambiar a `${PWD}` |
| Dockerfile no existe | 006 | Copiar template de 006 |

---

## 🎯 Comando Mágico (Soluciona 80% de problemas)

```bash
# Ejecutar en orden:
make clean              # Limpiar caché
make init               # Inicializar .env
make validate           # Validar configuración
make docker-up          # Levantar servicios
curl http://localhost:8000/health  # Verificar
```

Si esto falla, lee la salida de error y busca en tabla arriba.

---

## 📖 Ir a Documentación Completa

| Tema | Archivo |
|------|---------|
| Versiones de dependencias | `001-dependency-versions.md` |
| Healthchecks | `002-healthchecks.md` |
| Puertos | `003-port-management.md` |
| Configuración .env | `004-env-configuration.md` |
| Volúmenes | `005-volume-paths.md` |
| Dockerfiles | `006-dockerfile-patterns.md` |
| Resumen ejecutivo | `SUMMARY.md` |
| Comparación código | `BEFORE-AFTER-COMPARISON.md` |
| Índice completo | `README.md` |

---

## 💡 Recordatorios Clave

1. **Siempre validar antes de dockerizar**
   - Versiones de paquetes ✅
   - Archivo .env existe ✅
   - Puertos disponibles ✅

2. **Conocer lo que usas**
   - ¿Qué imagen estoy usando?
   - ¿Qué herramientas incluye?
   - ¿Qué necesita para iniciarse?

3. **Documentar lo que cambies**
   - Especialmente si resuelves un problema nuevo
   - Crea lección aprendida #7, #8, etc

4. **Ejecuta `make validate` = Ahorra 20 minutos**
   - Pre-detect 80% de errores
   - Feedback inmediato
   - Confianza en despliegue

---

**Última Actualización**: 2025-01-10  
**Para Problema No Listado**: Lee `README.md` → encuentra lección → aplica solución