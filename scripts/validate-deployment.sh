#!/bin/bash
#
# File: scripts/validate-deployment.sh
# Purpose: Validación integral pre-deployment de docker-compose
# Usage: ./scripts/validate-deployment.sh
# Based on: Lessons Learned 001-006
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_COMPOSE_FILE="deploy/compose/docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Counters
ERRORS=0
WARNINGS=0
CHECKS_PASSED=0

# Functions
log_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ==================== VALIDATIONS ====================

validate_env_file() {
    log_header "1. Validando Archivo .env"
    
    if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
        log_warning "Archivo $ENV_FILE no existe"
        
        if [ -f "$PROJECT_ROOT/$ENV_EXAMPLE" ]; then
            log_info "Creando $ENV_FILE desde $ENV_EXAMPLE..."
            cp "$PROJECT_ROOT/$ENV_EXAMPLE" "$PROJECT_ROOT/$ENV_FILE"
            log_success "Archivo $ENV_FILE creado"
        else
            log_error "Archivo $ENV_EXAMPLE tampoco existe"
            return 1
        fi
    else
        log_success "Archivo $ENV_FILE existe"
    fi
    
    # Validar variables obligatorias
    REQUIRED_VARS=("OPENROUTER_API_KEY" "QDRANT_URL" "REDIS_URL" "DEFAULT_RAG")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" "$PROJECT_ROOT/$ENV_FILE"; then
            log_success "Variable $var presente en .env"
        else
            log_warning "Variable $var no encontrada en .env"
        fi
    done
}

validate_docker_compose_syntax() {
    log_header "2. Validando Sintaxis docker-compose.yml"
    
    if [ ! -f "$PROJECT_ROOT/$DOCKER_COMPOSE_FILE" ]; then
        log_error "Archivo $DOCKER_COMPOSE_FILE no existe"
        return 1
    fi
    
    log_info "Validando sintaxis con 'docker compose config'..."
    
    if cd "$PROJECT_ROOT" && docker compose -f "$DOCKER_COMPOSE_FILE" config > /dev/null 2>&1; then
        log_success "Sintaxis docker-compose válida"
    else
        log_error "Sintaxis docker-compose inválida"
        docker compose -f "$DOCKER_COMPOSE_FILE" config
        return 1
    fi
}

validate_requirements_files() {
    log_header "3. Validando requirements.txt"
    
    REQUIREMENTS_FILES=(
        "services/api/requirements.txt"
        "services/ingest/requirements.txt"
    )
    
    for req_file in "${REQUIREMENTS_FILES[@]}"; do
        full_path="$PROJECT_ROOT/$req_file"
        
        if [ ! -f "$full_path" ]; then
            log_warning "Archivo $req_file no existe"
            continue
        fi
        
        log_info "Validando $req_file..."
        
        # Extraer paquetes con versiones
        while IFS= read -r line; do
            if [[ $line =~ ^[a-zA-Z] ]] && [[ $line == *"=="* ]]; then
                pkg=$(echo "$line" | cut -d'=' -f1)
                version=$(echo "$line" | cut -d'=' -f3-)
                
                # Validar con pip index (requiere conexión a PyPI)
                if pip index versions "$pkg" 2>/dev/null | grep -q "$version"; then
                    log_success "$pkg==$version válido"
                else
                    log_warning "$pkg==$version puede no existir (verificar con: pip index versions $pkg)"
                fi
            fi
        done < "$full_path"
    done
}

validate_dockerfiles() {
    log_header "4. Validando Dockerfiles"
    
    DOCKERFILES=(
        "services/api/Dockerfile"
        "services/ingest/Dockerfile"
    )
    
    for dockerfile in "${DOCKERFILES[@]}"; do
        full_path="$PROJECT_ROOT/$dockerfile"
        
        if [ ! -f "$full_path" ]; then
            log_error "Dockerfile no encontrado: $dockerfile"
            return 1
        fi
        
        log_success "Dockerfile existe: $dockerfile"
        
        # Validar que tenga CMD o ENTRYPOINT
        if grep -q -E "^(CMD|ENTRYPOINT)" "$full_path"; then
            log_success "  → Contiene CMD/ENTRYPOINT"
        else
            log_warning "  → No contiene CMD/ENTRYPOINT (puede ser problema)"
        fi
        
        # Verificar que instale requirements.txt
        if grep -q "requirements.txt" "$full_path"; then
            log_success "  → Instala requirements.txt"
        else
            log_warning "  → No menciona requirements.txt"
        fi
    done
}

validate_port_availability() {
    log_header "5. Validando Disponibilidad de Puertos"
    
    # Extraer puertos del docker-compose
    PORTS=$(cd "$PROJECT_ROOT" && docker compose -f "$DOCKER_COMPOSE_FILE" config 2>/dev/null | grep -A1 "ports:" | grep ":" | grep -oE "[0-9]+:" | cut -d: -f1 | sort -u)
    
    if [ -z "$PORTS" ]; then
        log_info "No hay puertos expuestos al host en docker-compose"
        log_success "Validación de puertos: OK (sin puertos expuestos)"
        return 0
    fi
    
    for port in $PORTS; do
        if command -v lsof &> /dev/null; then
            if lsof -i :$port &> /dev/null; then
                log_warning "Puerto $port puede estar en uso"
            else
                log_success "Puerto $port disponible"
            fi
        else
            log_info "lsof no disponible, saltando verificación de puerto $port"
        fi
    done
}

validate_volume_paths() {
    log_header "6. Validando Rutas de Volúmenes"
    
    cd "$PROJECT_ROOT"
    
    # Extraer rutas de volúmenes del docker-compose
    VOLUME_PATHS=$(docker compose -f "$DOCKER_COMPOSE_FILE" config 2>/dev/null | grep -E "^\s+- " | grep ":" | cut -d: -f1 | sed 's/^[[:space:]]*- //' | sort -u)
    
    for path in $VOLUME_PATHS; do
        # Ignorar volúmenes nombrados (no empiezan con /)
        if [[ ! $path =~ ^/ ]] && [[ ! $path =~ \$ ]]; then
            # Es un volumen nombrado
            log_success "Volumen nombrado: $path"
        else
            # Es una ruta
            if [ -e "$path" ] || [[ $path =~ \$ ]]; then
                log_success "Ruta válida/variable: $path"
            else
                log_warning "Ruta puede no existir: $path"
            fi
        fi
    done
}

validate_directory_structure() {
    log_header "7. Validando Estructura de Directorios"
    
    REQUIRED_DIRS=(
        "docs"
        "deploy/compose"
        "deploy/nginx"
        "configs/client"
        "configs/rags"
        "data/sources"
        "data/backups"
        "services/api"
        "services/ingest"
        "scripts"
    )
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        full_path="$PROJECT_ROOT/$dir"
        
        if [ -d "$full_path" ]; then
            log_success "Directorio existe: $dir"
        else
            log_error "Directorio no existe: $dir"
            return 1
        fi
    done
}

validate_documentation() {
    log_header "8. Validando Documentación"
    
    REQUIRED_DOCS=(
        "README.md"
        "docs/architecture.md"
        "docs/operations.md"
        "docs/security.md"
    )
    
    for doc in "${REQUIRED_DOCS[@]}"; do
        full_path="$PROJECT_ROOT/$doc"
        
        if [ -f "$full_path" ]; then
            log_success "Documentación existe: $doc"
        else
            log_warning "Documentación no existe: $doc"
        fi
    done
}

# ==================== MAIN ====================

main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║   RAF CHATBOT - Validación Pre-Deployment             ║
║   Docker Compose + Configuración + Infraestructura    ║
╚═══════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Ejecutar todas las validaciones
    validate_env_file || true
    validate_docker_compose_syntax || true
    validate_requirements_files || true
    validate_dockerfiles || true
    validate_port_availability || true
    validate_volume_paths || true
    validate_directory_structure || true
    validate_documentation || true
    
    # Resumen final
    log_header "Resumen de Validación"
    
    echo -e "\n${GREEN}✅ Checks Pasados: $CHECKS_PASSED${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Advertencias: $WARNINGS${NC}"
    fi
    
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}❌ Errores Críticos: $ERRORS${NC}"
        echo -e "\n${RED}Validación FALLIDA - Corrija los errores antes de proceder${NC}\n"
        return 1
    else
        echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ VALIDACIÓN EXITOSA - Listo para desplegar${NC}"
        echo -e "${GREEN}═══════════════════════════════════════${NC}\n"
        
        # Próximos pasos
        echo -e "${BLUE}Próximos pasos:${NC}"
        echo "  1. docker compose -f $DOCKER_COMPOSE_FILE up -d"
        echo "  2. docker compose -f $DOCKER_COMPOSE_FILE ps"
        echo "  3. curl http://localhost:8080/health"
        echo ""
        return 0
    fi
}

# Ejecutar main si el script fue llamado directamente (no sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi