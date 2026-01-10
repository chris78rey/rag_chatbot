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