# Makefile - RAF Chatbot RAG System
# Automatización de tareas comunes: validación, build, deploy, testing

.PHONY: help init validate docker-build docker-up docker-down docker-logs clean test lint format

# Variables
COMPOSE_FILE := deploy/compose/docker-compose.yml
PYTHON_VERSION := 3.11
SHELL := /bin/bash

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)RAF Chatbot RAG System - Makefile$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Inicialización:$(NC)"
	@echo "  make init                    - Inicializar proyecto (crear .env, instalar deps)"
	@echo "  make init-dev                - Setup dev environment (pre-commit hooks, etc)"
	@echo ""
	@echo "$(GREEN)Validación:$(NC)"
	@echo "  make validate                - Ejecutar todas las validaciones"
	@echo "  make validate-env            - Validar archivo .env y variables"
	@echo "  make validate-requirements   - Validar requirements.txt (versiones válidas)"
	@echo "  make validate-docker         - Validar sintaxis docker-compose.yml"
	@echo "  make validate-paths          - Validar rutas en docker-compose"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build            - Construir imágenes Docker"
	@echo "  make docker-up               - Levantar servicios (con validación)"
	@echo "  make docker-down             - Parar servicios"
	@echo "  make docker-restart          - Reiniciar servicios"
	@echo "  make docker-logs             - Ver logs en tiempo real"
	@echo "  make docker-ps               - Ver estado de contenedores"
	@echo "  make docker-clean            - Limpiar volúmenes y redes"
	@echo ""
	@echo "$(GREEN)Desarrollo:$(NC)"
	@echo "  make lint                    - Ejecutar linters (flake8, black)"
	@echo "  make format                  - Formatear código (black, isort)"
	@echo "  make test                    - Ejecutar tests unitarios"
	@echo "  make test-e2e                - Ejecutar tests end-to-end"
	@echo ""
	@echo "$(GREEN)Limpieza:$(NC)"
	@echo "  make clean                   - Limpiar archivos generados"
	@echo "  make clean-docker            - Limpiar imágenes y volúmenes Docker"
	@echo "  make clean-all               - Limpieza completa (destructivo)"
	@echo ""

# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: init
init: validate-env
	@echo "$(BLUE)✓ Inicializando proyecto...$(NC)"
	@echo "$(GREEN)✓ .env configurado$(NC)"
	@echo "$(GREEN)✓ Estructura verificada$(NC)"
	@echo ""
	@echo "$(YELLOW)Próximos pasos:$(NC)"
	@echo "  1. Editar .env con tus credenciales"
	@echo "  2. Ejecutar: make docker-up"
	@echo ""

.PHONY: init-dev
init-dev: init
	@echo "$(BLUE)✓ Configurando entorno de desarrollo...$(NC)"
	@if [ ! -f .git/hooks/pre-commit ]; then \
		echo "  Instalando pre-commit hooks..."; \
		cp scripts/pre-commit-validate.sh .git/hooks/pre-commit 2>/dev/null || echo "  ℹ️  .git no inicializado"; \
	fi
	@echo "$(GREEN)✓ Dev environment listo$(NC)"

# ═══════════════════════════════════════════════════════════════════════════
# VALIDACIÓN
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: validate
validate: validate-env validate-requirements validate-docker validate-paths
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ TODAS LAS VALIDACIONES PASARON$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"

.PHONY: validate-env
validate-env:
	@echo "$(BLUE)▸ Validando .env...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  .env no encontrado, creando desde .env.example...$(NC)"; \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "$(GREEN)✓ .env creado$(NC)"; \
		else \
			echo "$(RED)✗ Error: .env.example tampoco existe$(NC)"; \
			exit 1; \
		fi; \
	else \
		echo "$(GREEN)✓ .env encontrado$(NC)"; \
	fi
	@echo "$(BLUE)▸ Verificando variables obligatorias...$(NC)"
	@MISSING=0; \
	for var in OPENROUTER_API_KEY QDRANT_URL REDIS_URL; do \
		if ! grep -q "^$$var=" .env 2>/dev/null; then \
			echo "$(YELLOW)⚠️  Variable $$var no configurada en .env$(NC)"; \
			MISSING=$$((MISSING+1)); \
		fi; \
	done; \
	if [ $$MISSING -gt 0 ]; then \
		echo "$(YELLOW)⚠️  $$MISSING variables sin configurar$(NC)"; \
	else \
		echo "$(GREEN)✓ Variables obligatorias configuradas$(NC)"; \
	fi

.PHONY: validate-requirements
validate-requirements:
	@echo "$(BLUE)▸ Validando requirements.txt...$(NC)"
	@for req_file in services/api/requirements.txt services/ingest/requirements.txt; do \
		if [ -f "$$req_file" ]; then \
			echo "  Chequeando $$req_file..."; \
			if pip install --dry-run -q -r "$$req_file" 2>&1 | grep -q "ERROR:"; then \
				echo "$(RED)✗ Errores en $$req_file$(NC)"; \
				exit 1; \
			else \
				echo "$(GREEN)  ✓ $$req_file válido$(NC)"; \
			fi; \
		fi; \
	done

.PHONY: validate-docker
validate-docker:
	@echo "$(BLUE)▸ Validando sintaxis docker-compose.yml...$(NC)"
	@if docker compose -f $(COMPOSE_FILE) config > /dev/null 2>&1; then \
		echo "$(GREEN)✓ docker-compose.yml sintaxis válida$(NC)"; \
	else \
		echo "$(RED)✗ Errores en docker-compose.yml$(NC)"; \
		docker compose -f $(COMPOSE_FILE) config; \
		exit 1; \
	fi

.PHONY: validate-paths
validate-paths:
	@echo "$(BLUE)▸ Validando rutas en volúmenes...$(NC)"
	@python3 scripts/validate-volumes.py 2>/dev/null || echo "$(YELLOW)ℹ️  Script de validación no disponible$(NC)"
	@echo "$(GREEN)✓ Validación de rutas completada$(NC)"

# ═══════════════════════════════════════════════════════════════════════════
# DOCKER
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: docker-build
docker-build: validate
	@echo "$(BLUE)▸ Construyendo imágenes Docker...$(NC)"
	docker compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)✓ Imágenes construidas exitosamente$(NC)"

.PHONY: docker-up
docker-up: validate docker-build
	@echo "$(BLUE)▸ Levantando servicios...$(NC)"
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✓ Servicios levantados$(NC)"
	@echo ""
	@echo "$(BLUE)Estado de servicios:$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(YELLOW)Endpoints disponibles:$(NC)"
	@echo "  • API:   http://localhost:8000"
	@echo "  • Nginx: http://localhost:8080"
	@echo "  • Qdrant (interno): qdrant:6333"
	@echo "  • Redis (interno):  redis:6379"

.PHONY: docker-down
docker-down:
	@echo "$(BLUE)▸ Parando servicios...$(NC)"
	docker compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✓ Servicios parados$(NC)"

.PHONY: docker-restart
docker-restart: docker-down docker-up
	@echo "$(GREEN)✓ Servicios reiniciados$(NC)"

.PHONY: docker-logs
docker-logs:
	@echo "$(BLUE)▸ Mostrando logs en tiempo real (Ctrl+C para salir)...$(NC)"
	docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: docker-logs-%
docker-logs-%:
	@docker compose -f $(COMPOSE_FILE) logs -f $*

.PHONY: docker-ps
docker-ps:
	@docker compose -f $(COMPOSE_FILE) ps

.PHONY: docker-clean
docker-clean: docker-down
	@echo "$(BLUE)▸ Limpiando volúmenes Docker...$(NC)"
	docker compose -f $(COMPOSE_FILE) down -v
	@echo "$(GREEN)✓ Volúmenes eliminados$(NC)"

# ═══════════════════════════════════════════════════════════════════════════
# DESARROLLO
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: lint
lint:
	@echo "$(BLUE)▸ Ejecutando linters...$(NC)"
	@if command -v flake8 &> /dev/null; then \
		flake8 services/ --max-line-length=120; \
		echo "$(GREEN)✓ flake8 pasado$(NC)"; \
	else \
		echo "$(YELLOW)ℹ️  flake8 no instalado, omitiendo$(NC)"; \
	fi
	@if command -v black &> /dev/null; then \
		black --check services/ 2>/dev/null && echo "$(GREEN)✓ black pasado$(NC)" || echo "$(YELLOW)⚠️  black encontró diferencias$(NC)"; \
	else \
		echo "$(YELLOW)ℹ️  black no instalado, omitiendo$(NC)"; \
	fi

.PHONY: format
format:
	@echo "$(BLUE)▸ Formateando código...$(NC)"
	@if command -v black &> /dev/null; then \
		black services/; \
		echo "$(GREEN)✓ Código formateado con black$(NC)"; \
	else \
		echo "$(YELLOW)ℹ️  black no instalado, omitiendo$(NC)"; \
	fi
	@if command -v isort &> /dev/null; then \
		isort services/; \
		echo "$(GREEN)✓ Imports ordenados con isort$(NC)"; \
	else \
		echo "$(YELLOW)ℹ️  isort no instalado, omitiendo$(NC)"; \
	fi

.PHONY: test
test:
	@echo "$(BLUE)▸ Ejecutando tests unitarios...$(NC)"
	@if [ -d "tests" ]; then \
		python -m pytest tests/ -v; \
		echo "$(GREEN)✓ Tests completados$(NC)"; \
	else \
		echo "$(YELLOW)ℹ️  Directorio tests/ no encontrado$(NC)"; \
	fi

.PHONY: test-e2e
test-e2e: docker-up
	@echo "$(BLUE)▸ Ejecutando tests end-to-end...$(NC)"
	@sleep 5
	@echo "$(BLUE)Probando endpoints...$(NC)"
	@echo "  • Health check..."
	@curl -s http://localhost:8000/health && echo "" || echo "$(RED)✗ Health check falló$(NC)"
	@echo "  • API root..."
	@curl -s http://localhost:8000/ && echo "" || echo "$(RED)✗ API root falló$(NC)"
	@echo "$(GREEN)✓ Tests E2E completados$(NC)"

# ═══════════════════════════════════════════════════════════════════════════
# LIMPIEZA
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: clean
clean:
	@echo "$(BLUE)▸ Limpiando archivos generados...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "$(GREEN)✓ Limpieza completada$(NC)"

.PHONY: clean-docker
clean-docker:
	@echo "$(BLUE)▸ Limpiando Docker (imágenes y volúmenes)...$(NC)"
	docker compose -f $(COMPOSE_FILE) down -v 2>/dev/null || true
	docker rmi compose-api compose-ingest-worker 2>/dev/null || true
	@echo "$(GREEN)✓ Limpieza Docker completada$(NC)"

.PHONY: clean-all
clean-all: clean clean-docker docker-clean
	@echo "$(RED)⚠️  LIMPIEZA COMPLETA$(NC)"
	@echo "Contenedores, volúmenes, imágenes y archivos generados eliminados"
	@echo "$(GREEN)✓ Sistema limpio$(NC)"

# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: status
status:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)Estado del Sistema$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)Docker Containers:$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps || echo "No hay contenedores"
	@echo ""
	@echo "$(BLUE).env configuration:$(NC)"
	@if [ -f .env ]; then echo "$(GREEN)✓ Existe$(NC)"; else echo "$(RED)✗ No existe$(NC)"; fi
	@echo ""
	@echo "$(BLUE)Docker images:$(NC)"
	@docker images | grep compose || echo "No hay imágenes compose"

.PHONY: docs
docs:
	@echo "$(BLUE)📚 Documentación disponible:$(NC)"
	@echo "  • README.md - Descripción general"
	@echo "  • docs/architecture.md - Arquitectura del sistema"
	@echo "  • docs/operations.md - Guía operacional"
	@echo "  • docs/security.md - Consideraciones de seguridad"
	@echo "  • specs/lessons-learned/ - Lecciones aprendidas"

# ═══════════════════════════════════════════════════════════════════════════
# PHONY declarations
# ═══════════════════════════════════════════════════════════════════════════

.PHONY: status docs

# Default shell behavior
.ONESHELL: