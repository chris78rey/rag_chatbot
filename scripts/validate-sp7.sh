#!/bin/bash

# Validación de Subproject 7: Vector Retrieval & Ranking
# Script para verificar que todos los archivos y componentes están en lugar

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   VALIDACIÓN SUBPROJECT 7: Vector Retrieval & Ranking         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
CHECKS_PASSED=0
CHECKS_FAILED=0

# Función para verificar archivo
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $description"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌${NC} $description (NOT FOUND: $file)"
        ((CHECKS_FAILED++))
    fi
}

# Función para verificar directorio
check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $description"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌${NC} $description (NOT FOUND: $dir)"
        ((CHECKS_FAILED++))
    fi
}

# Función para verificar función en archivo
check_function() {
    local file=$1
    local function=$2
    
    if grep -q "def $function\|async def $function" "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} Function: $function()"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌${NC} Function: $function() NOT FOUND in $file"
        ((CHECKS_FAILED++))
    fi
}

echo "📂 Verificando estructura de directorios..."
check_dir "services/api/app" "Directorio app/"
check_dir "services/api/app/routes" "Directorio routes/"
echo ""

echo "📄 Verificando archivos del módulo app..."
check_file "services/api/app/__init__.py" "Módulo init"
check_file "services/api/app/qdrant_client.py" "Cliente Qdrant"
check_file "services/api/app/retrieval.py" "Módulo retrieval"
check_file "services/api/app/models.py" "Modelos Pydantic"
check_file "services/api/app/routes/__init__.py" "Routes init"
check_file "services/api/app/routes/query.py" "Endpoint query"
echo ""

echo "📄 Verificando archivos de soporte..."
check_file "services/api/app/README.md" "README del módulo app"
check_file "scripts/seed_demo_data.py" "Script de datos demo"
check_file "docs/qdrant.md" "Documentación Qdrant"
check_file "tests/test_retrieval.py" "Test suite"
echo ""

echo "📋 Verificando funciones en qdrant_client.py..."
check_function "services/api/app/qdrant_client.py" "get_client"
check_function "services/api/app/qdrant_client.py" "ensure_collection"
check_function "services/api/app/qdrant_client.py" "upsert_chunks"
check_function "services/api/app/qdrant_client.py" "search"
check_function "services/api/app/qdrant_client.py" "delete_collection"
echo ""

echo "📋 Verificando funciones en retrieval.py..."
check_function "services/api/app/retrieval.py" "get_embedding"
check_function "services/api/app/retrieval.py" "retrieve_context"
echo ""

echo "📋 Verificando modelos en models.py..."
if grep -q "class ContextChunk" "services/api/app/models.py"; then
    echo -e "${GREEN}✅${NC} Model: ContextChunk"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Model: ContextChunk NOT FOUND"
    ((CHECKS_FAILED++))
fi

if grep -q "class QueryRequest" "services/api/app/models.py"; then
    echo -e "${GREEN}✅${NC} Model: QueryRequest"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Model: QueryRequest NOT FOUND"
    ((CHECKS_FAILED++))
fi

if grep -q "class QueryResponse" "services/api/app/models.py"; then
    echo -e "${GREEN}✅${NC} Model: QueryResponse"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Model: QueryResponse NOT FOUND"
    ((CHECKS_FAILED++))
fi
echo ""

echo "📋 Verificando endpoint en routes/query.py..."
if grep -q "async def query_rag" "services/api/app/routes/query.py"; then
    echo -e "${GREEN}✅${NC} Endpoint: query_rag()"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Endpoint: query_rag() NOT FOUND"
    ((CHECKS_FAILED++))
fi

if grep -q '@router.post("/query")' "services/api/app/routes/query.py"; then
    echo -e "${GREEN}✅${NC} Route: POST /query"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Route: POST /query NOT FOUND"
    ((CHECKS_FAILED++))
fi
echo ""

echo "🧪 Verificando test suite..."
if [ -f "tests/test_retrieval.py" ]; then
    test_count=$(grep -c "def test_" "tests/test_retrieval.py" || echo "0")
    echo -e "${GREEN}✅${NC} Tests: $test_count test functions found"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} Test suite not found"
    ((CHECKS_FAILED++))
fi
echo ""

echo "📚 Verificando documentación..."
if [ -f "docs/qdrant.md" ]; then
    doc_lines=$(wc -l < "docs/qdrant.md")
    echo -e "${GREEN}✅${NC} Documentación Qdrant ($doc_lines líneas)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌${NC} docs/qdrant.md NOT FOUND"
    ((CHECKS_FAILED++))
fi
echo ""

echo "📊 Verificando archivos de prueba completados..."
check_file "SUBPROJECT-7-SUMMARY.md" "Resumen SP7"
check_file "SUBPROJECT-7-PROOF.md" "Prueba SP7"
echo ""

# Resumen final
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                         RESULTADOS                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "Checks completados: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks fallidos: ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅ SUBPROJECT 7 VALIDATION PASSED                      ║${NC}"
    echo -e "${GREEN}║                  All components ready!                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║          ❌ SUBPROJECT 7 VALIDATION FAILED                       ║${NC}"
    echo -e "${RED}║              Please check missing files above                    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi