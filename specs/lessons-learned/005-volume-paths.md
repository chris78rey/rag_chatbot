# 📚 Lección Aprendida #005 — Rutas Relativas en Volúmenes Docker

## 🎯 Problema
En `docker-compose.yml`, los volúmenes con rutas relativas pueden no resolverse correctamente dependiendo de dónde se ejecute el comando `docker compose`. Esto causa que los contenedores no puedan acceder a los datos esperados.

**Manifestación:**
```yaml
# ❌ PROBLEMÁTICO
volumes:
  - ../../deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  - ../../.env:/workspace/.env
```

## 🔍 Causa Raíz

1. Docker Compose resuelve rutas relativas **desde la ubicación del archivo `docker-compose.yml`**, no desde el directorio actual de ejecución
2. Cuando se ejecuta desde diferentes ubicaciones, las rutas pueden estar incorrectas
3. En entornos CI/CD o scripts automatizados, el contexto de ejecución puede variar
4. Rutas con `..` son frágiles y difíciles de mantener cuando la estructura cambia

## ✅ Solución

### Opción 1: Rutas Absolutas Usando Variables (RECOMENDADO)
```yaml
# ✅ CORRECTO
services:
  nginx:
    volumes:
      - ${PWD}/deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ${PWD}/.env:/workspace/.env:ro
```

### Opción 2: Usar `.env.docker` para Variables
```bash
# .env.docker (en la raíz del proyecto)
PROJECT_ROOT=.
NGINX_CONFIG_PATH=./deploy/nginx/nginx.conf
ENV_FILE_PATH=./.env
```

```yaml
# docker-compose.yml
services:
  nginx:
    volumes:
      - ${NGINX_CONFIG_PATH}:/etc/nginx/nginx.conf:ro
  api:
    env_file:
      - ${ENV_FILE_PATH}
```

### Opción 3: Usar volúmenes nombrados para datos persistentes
```yaml
# ✅ MEJOR PARA DATOS
volumes:
  sources_data:
  qdrant_data:
  redis_data:

services:
  ingest-worker:
    volumes:
      - sources_data:/workspace/data/sources
  qdrant:
    volumes:
      - qdrant_data:/qdrant/storage
```

## 🛡️ Principio Preventivo Clave

**"Mantén las rutas de volúmenes predecibles y agnósticas del contexto de ejecución"**

- Usa `${PWD}` o variables de entorno, no rutas relativas con `..`
- Documentar la estructura esperada de volúmenes
- Preferir volúmenes nombrados para datos persistentes
- Usar archivos de configuración para paths dinámicos

## 🚨 Señal de Activación

Detectarás este problema cuando:
- ❌ Los contenedores fallan con errores de "archivo no encontrado"
- ❌ Los volúmenes están vacíos cuando deberían tener contenido
- ❌ El comportamiento cambia según dónde ejecutes `docker compose up`
- ❌ Los scripts de CI/CD fallan pero funciona localmente
- ❌ Ves mensajes como `failed to resolve mount source path`

## 💾 Snippet Reutilizable: Validador de Rutas

```python
# scripts/validate_volumes.py
import os
import re
from pathlib import Path
import yaml

def validate_docker_compose_paths(compose_file: str) -> list[str]:
    """
    Valida que las rutas en docker-compose.yml sean accesibles.
    
    Args:
        compose_file: Ruta al docker-compose.yml
        
    Returns:
        Lista de errores encontrados
    """
    errors = []
    project_root = Path(compose_file).parent.parent.parent
    
    with open(compose_file, 'r') as f:
        compose = yaml.safe_load(f)
    
    for service_name, service in compose.get('services', {}).items():
        volumes = service.get('volumes', [])
        
        for volume in volumes:
            if isinstance(volume, str) and ':' in volume:
                host_path = volume.split(':')[0]
                
                # Detectar rutas relativas problemáticas
                if host_path.startswith('../../'):
                    errors.append(
                        f"⚠️  {service_name}: Ruta relativa problemática: {host_path}"
                    )
                
                # Validar que la ruta existe (si no usa variable)
                if not host_path.startswith('${'):
                    full_path = project_root / host_path
                    if not full_path.exists():
                        errors.append(
                            f"❌ {service_name}: Ruta no existe: {full_path}"
                        )
    
    return errors

if __name__ == '__main__':
    compose_path = 'deploy/compose/docker-compose.yml'
    errors = validate_docker_compose_paths(compose_path)
    
    if errors:
        print("Errores encontrados:")
        for error in errors:
            print(f"  {error}")
        exit(1)
    else:
        print("✅ Todas las rutas de volúmenes son válidas")
```

## 📋 Checklist

- [ ] ¿Usas `${PWD}` o variables de entorno en lugar de rutas relativas?
- [ ] ¿Los datos importantes están en volúmenes nombrados, no en montajes de host?
- [ ] ¿Has documentado la estructura esperada de volúmenes?
- [ ] ¿Ejecutaste `docker compose config` para verificar las rutas resueltas?
- [ ] ¿Tienes un script que valida los paths antes de levantar contenedores?

## 🔗 Referencias
- [Docker Compose Volume Documentation](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [Docker Bind Mounts](https://docs.docker.com/storage/bind-mounts/)