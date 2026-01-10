# 🔹 PROMPT EJECUTABLE 02 — Docker Compose Base

> **Subproyecto**: 2 de 10  
> **Objetivo**: Crear docker-compose.yml con FastAPI, Qdrant, Redis, Nginx + volúmenes  
> **Ruta destino**: `G:\zed_projects\raf_chatbot\`

---

## ROL (modelo ligero)

Actúa como **editor mecánico**: crear archivos exactos y pegar contenido literal. No optimizar ni rediseñar.

---

## ⚠️ REGLA CRÍTICA

```
El modelo NO debe ejecutar comandos.
El humano ejecutará los comandos manualmente.
```

---

## ARCHIVOS A CREAR

| Archivo | Ubicación |
|---------|-----------|
| `docker-compose.yml` | `deploy/compose/docker-compose.yml` |
| `nginx.conf` | `deploy/nginx/nginx.conf` |
| `README.md` | `deploy/nginx/README.md` |

---

## ESPECIFICACIONES DE CONTENIDO

### 1. `deploy/compose/docker-compose.yml`

**Requisitos obligatorios:**

```yaml
version: "3.9"

services:
  qdrant:
    # Imagen oficial de Qdrant
    # Puerto 6333 expuesto solo a red interna (no al host, o solo localhost)
    # Volumen persistente: qdrant_data

  redis:
    # Imagen oficial de Redis
    # Puerto 6379 interno (no exponer al host)
    # Volumen opcional: redis_data

  api:
    # Build desde: services/api (Dockerfile placeholder permitido)
    # env_file: .env
    # Depende de: qdrant, redis
    # Puerto interno 8000

  ingest-worker:
    # Build desde: services/ingest
    # env_file: .env
    # Depende de: redis, qdrant
    # Comando placeholder (puede ser "sleep infinity" o similar inicialmente)

  nginx:
    # Imagen: nginx:alpine
    # Mapea puerto 80:80
    # Proxy hacia servicio api
    # Volumen para nginx.conf

networks:
  rag_network:
    driver: bridge

volumes:
  qdrant_data:
  redis_data:
  sources_data:
  logs_data:
```

**Notas importantes:**
- El archivo `.env` debe referenciarse desde la raíz del proyecto (ajustar path relativo según contexto de build)
- Los volúmenes `sources_data` mapean a `data/sources`
- Todos los servicios deben estar en `rag_network`

---

### 2. `deploy/nginx/nginx.conf`

**Contenido requerido:**

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting básico por IP
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    upstream api_backend {
        server api:8000;
    }

    server {
        listen 80;
        server_name _;

        # Location para API
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://api_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check directo
        location /health {
            proxy_pass http://api_backend/health;
        }
    }
}
```

---

### 3. `deploy/nginx/README.md`

**Contenido:**

```markdown
# Configuración Nginx

## Descripción
Reverse proxy para el API FastAPI con rate limiting básico.

## Rate Limiting
- Zona: `api_limit`
- Rate: 10 requests/segundo por IP
- Burst: 20 requests

## Cómo añadir TLS (futuro)

1. Generar certificados (Let's Encrypt o auto-firmados):
   ```bash
   # Con certbot (ejemplo)
   certbot certonly --standalone -d tu-dominio.com
   ```

2. Modificar `nginx.conf`:
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /etc/nginx/certs/fullchain.pem;
       ssl_certificate_key /etc/nginx/certs/privkey.pem;
       # ... resto de config
   }
   ```

3. Añadir volumen en docker-compose para certs:
   ```yaml
   nginx:
     volumes:
       - ./certs:/etc/nginx/certs:ro
   ```

## Notas
- TLS NO está implementado en MVP
- Para producción, usar certificados válidos
- Considerar HSTS headers cuando se habilite TLS
```

---

## COMANDOS PARA VALIDACIÓN (ejecutar manualmente)

```bash
# 1. Validar sintaxis del docker-compose
docker compose -f deploy/compose/docker-compose.yml config

# 2. Levantar el stack
docker compose -f deploy/compose/docker-compose.yml up -d

# 3. Verificar estado de contenedores
docker compose -f deploy/compose/docker-compose.yml ps

# 4. Ver logs si hay errores
docker compose -f deploy/compose/docker-compose.yml logs
```

---

## ✅ PUNTO DE ESPERA

**Detenerse aquí y confirmar:**

1. [ ] `docker compose config` no arroja errores de sintaxis
2. [ ] Los 5 servicios aparecen definidos (qdrant, redis, api, ingest-worker, nginx)
3. [ ] Los contenedores levantan (aunque api/ingest fallen por falta de código, qdrant/redis/nginx deben estar "Up")

---

## CRITERIO DE ÉXITO

- **Éxito binario**: `docker compose config` valida OK y `docker compose ps` muestra servicios creados.

---

## ERRORES TÍPICOS A EVITAR

| Error | Causa | Solución |
|-------|-------|----------|
| Build context not found | Ruta incorrecta a services/api | Verificar path relativo desde docker-compose.yml |
| Port already in use | Puerto 80 ocupado | Cambiar mapeo a 8080:80 temporalmente |
| nginx: host not found | Nombre de servicio incorrecto | El upstream debe ser `api` (nombre del service) |
| Volume mount error | Path no existe | Crear carpetas data/sources primero |

---

## QUÉ SE CONGELA DESPUÉS DE ESTE SUBPROYECTO

- ✅ Nombres de servicios Docker: `api`, `qdrant`, `redis`, `nginx`, `ingest-worker`
- ✅ Nombres de volúmenes: `qdrant_data`, `redis_data`, `sources_data`, `logs_data`
- ✅ Red: `rag_network`
- ✅ Puerto público: 80 (Nginx)

---

## SIGUIENTE SUBPROYECTO

→ **Subproyecto 3**: Esquema de configuración (YAML/ENV) por cliente y por RAG