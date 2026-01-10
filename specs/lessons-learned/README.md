# 📚 Lecciones Aprendidas — RAF Chatbot RAG System

## 📋 Descripción General

Este directorio documenta las lecciones aprendidas durante la construcción del sistema RAG on-premise. Cada documento analiza un problema específico encontrado durante el desarrollo, identifica su causa raíz, proporciona una solución y establece principios preventivos para evitar errores similares en el futuro.

**Propósito:**
- 🔍 Capturar errores y aciertos para aprendizaje del equipo
- 🛡️ Prevenir regresión de bugs conocidos
- 📈 Mejorar continuamente procesos de desarrollo y deployment
- 🔄 Crear snippets reutilizables para problemas recurrentes

---

## 📑 Índice de Lecciones

### 1. **Gestión de Versiones de Dependencias** (`001-dependency-versions.md`)
   - **Problema**: Especificación de versiones que no existen en PyPI
   - **Ejemplo**: `qdrant-client==2.7.0` nunca fue publicada
   - **Impacto**: Build Docker fallan silenciosamente
   - **Solución**: Validar con `pip index versions` antes de usar
   - **Principio**: "Validar Dependencias en Tiempo de Especificación, No en Build"

### 2. **Healthchecks en Docker Compose** (`002-healthchecks.md`)
   - **Problema**: Herramientas no disponibles en imágenes base (curl, wget, redis-cli)
   - **Ejemplo**: `curl: command not found` en contenedor qdrant
   - **Impacto**: Servicios no pasan healthchecks y no inician
   - **Solución**: Usar `service_started` en lugar de `service_healthy` cuando las herramientas no existan
   - **Principio**: "Conocer la imagen base antes de usarla"

### 3. **Gestión de Puertos en Docker Compose** (`003-port-management.md`)
   - **Problema**: Puerto 80 ocupado en el host
   - **Ejemplo**: `ports are not available: exposing port TCP 127.0.0.1:80`
   - **Impacto**: No se pueden levantar contenedores con puerto específico
   - **Solución**: Usar puerto alternativo (8080) o no exponer internamente
   - **Principio**: "Nunca usar puertos < 1024 en dev sin validar disponibilidad"

### 4. **Configuración de Archivo .env** (`004-env-configuration.md`)
   - **Problema**: Archivo `.env` no existe pero docker-compose lo requiere
   - **Ejemplo**: `env file ... not found`
   - **Impacto**: docker-compose config falla antes de validar sintaxis
   - **Solución**: Crear `.env` automáticamente desde `.env.example`
   - **Principio**: "Environment First Validation"

### 5. **Rutas Relativas en Volúmenes Docker** (`005-volume-paths.md`)
   - **Problema**: Rutas con `../../` son frágiles y dependen del contexto
   - **Ejemplo**: Volúmenes no montan correctamente en diferentes directorios
   - **Impacto**: Datos inconsistentes entre ejecuciones locales y CI/CD
   - **Solución**: Usar `${PWD}` o volúmenes nombrados
   - **Principio**: "Mantén rutas de volúmenes agnósticas del contexto"

### 6. **Dockerfiles y Patrones de Construcción** (`006-dockerfile-patterns.md`)
   - **Problema**: Falta de Dockerfiles en servicios + versiones inválidas en requirements.txt
   - **Ejemplo**: Build context not found + could not find version
   - **Impacto**: Imposible construir imágenes Docker
   - **Solución**: Crear Dockerfiles parametrizados y validados
   - **Principio**: "Dockerfile es código de infraestructura, trata como tal"

---

## 🎯 Estructura de Cada Documento

Cada lección aprendida sigue esta estructura:

```
## 📋 Resumen Ejecutivo
(1-2 líneas del problema)

## 🔴 Problema
(Síntoma exacto, contexto, impacto)

## 🔍 Causa Raíz
(Por qué pasó realmente)

## ✅ Solución
(Antes/Después, opciones implementadas)

## 🛡️ Principio Preventivo Clave
(Regla general que previene este error)

## 🚨 Señal de Activación
(Cómo detectar este error futuro)

## 📝 Snippet Reutilizable
(Código/script que resuelve el problema)

## 📊 Impacto / Checklist
```

---

## 🔍 Cómo Usar Este Directorio

### Para Desarrolladores
1. Lee la lección relevante antes de trabajar con esa tecnología
2. Utiliza los snippets reutilizables en tus propios scripts
3. Implementa el checklist antes de hacer merge

### Para Arquitectos
1. Revisa los principios preventivos para tomar decisiones de diseño
2. Usa las señales de activación en procesos de review
3. Agrega validaciones automáticas basadas en lecciones

### Para DevOps/SRE
1. Implementa scripts de validación en CI/CD
2. Crea dashboards basados en señales de activación
3. Documenta procedimientos operacionales según las lecciones

---

## 📊 Estadísticas de Lecciones

| Categoría | Count | Severidad | Estado |
|-----------|-------|-----------|--------|
| Dependency Management | 1 | Alta | ✅ Resuelto |
| Container Health | 1 | Alta | ✅ Resuelto |
| Port Management | 1 | Media | ✅ Resuelto |
| Configuration | 1 | Media | ✅ Resuelto |
| Volumes | 1 | Media | ✅ Resuelto |
| Docker | 1 | Alta | ✅ Resuelto |
| **Total** | **6** | - | **6/6** |

---

## 🔄 Ciclo de Vida de una Lección

```
1. ERROR ENCONTRADO
   ↓
2. ANÁLISIS DE CAUSA RAÍZ
   ↓
3. SOLUCIÓN IMPLEMENTADA
   ↓
4. DOCUMENTACIÓN (lección)
   ↓
5. VALIDACIÓN AUTOMATIZADA (scripts/tests)
   ↓
6. ENTRENAMIENTO DEL EQUIPO
   ↓
7. MONITOREO (señales de activación)
```

---

## 📈 Próximas Lecciones Esperadas

Cuando avances a los siguientes subproyectos:

- **Subproyecto 3**: Configuración YAML/ENV
  - Versionado de configs
  - Secrets management
  - Schema validation

- **Subproyecto 4-5**: Ingestión y API
  - Rate limiting
  - Cache strategy
  - Error handling patterns

- **Subproyecto 6-7**: Observability
  - Logging best practices
  - Metrics design
  - Alerting rules

- **Subproyecto 8-10**: LLM, Estado, Tests
  - Prompt engineering
  - State management
  - Test strategy

---

## 🚀 Cómo Contribuir Nuevas Lecciones

Cuando encuentres un problema importante:

1. **Crea un archivo** con número secuencial: `NNN-tema-corto.md`
2. **Sigue la estructura** estándar (ver arriba)
3. **Incluye snippets** reutilizables si aplica
4. **Actualiza este README** con la nueva lección
5. **Implementa validaciones** automáticas en CI/CD

---

## 🔗 Conexiones Entre Lecciones

```
001 (Versions)
  ↓
  └─→ 006 (Dockerfiles) ← 002 (Healthchecks)
      ↓
      └─→ 005 (Volumes) ← 003 (Ports)
          ↓
          └─→ 004 (Env Config)
```

Las lecciones se construyen unas sobre otras. Resolver 001 requiere 006, que necesita validación de 002, etc.

---

## 📚 Referencias Externas

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [12 Factor App](https://12factor.net/) - Configuración (factor III)
- [SRE Book](https://sre.google/books/) - Lessons Learned (capítulo 21)
- [Python Packaging Guide](https://packaging.python.org/)

---

## ✏️ Metadata

- **Proyecto**: raf_chatbot (RAG On-Premise)
- **Inicio**: Subproyectos 1-2
- **Propósito**: Documentación técnica de calidad
- **Audiencia**: Desarrolladores, Arquitectos, DevOps
- **Última Actualización**: 2025-01-10
- **Responsable**: Engineering Team

---

## 📝 Notas

> "Las lecciones aprendidas documentadas son la diferencia entre un equipo que aprende de sus errores y uno que los repite."

Mantén este directorio actualizado. Es la brújula del proyecto.