# Seguridad

## Exposición por Nginx
- Todo el tráfico externo pasa por Nginx
- API no expuesta directamente

## TLS
- No implementado en MVP
- Recomendación: usar proxy externo o configurar certs en Nginx

## Rate Limiting
- Configurado en Nginx por IP
- Rate limit adicional por RAG en la API

## Autenticación
- No implementada en MVP
- Recomendación para producción: API keys o JWT

## Recomendaciones de Red Local
- Desplegar en red privada
- No exponer puertos de Qdrant/Redis externamente
- Usar firewall para limitar acceso