#!/bin/bash
#
# File: scripts/test-subproject-2.sh
# Purpose: Automated test suite for Subproject 2 (Docker Compose)
# Usage: ./scripts/test-subproject-2.sh
# Output: Test results with pass/fail status
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log_test() {
    echo -e "${BLUE}▶ TEST: $1${NC}"
    ((TESTS_TOTAL++))
}

pass() {
    echo -e "${GREEN}  ✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}  ❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${YELLOW}  ℹ️  $1${NC}"
}

header() {
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
}

# ==================== TESTS ====================

test_file_exists() {
    log_test "File exists: deploy/compose/docker-compose.yml"
    
    if [ -f "deploy/compose/docker-compose.yml" ]; then
        pass "File exists"
    else
        fail "File does not exist"
        return 1
    fi
}

test_file_size() {
    log_test "File size is reasonable (> 500 bytes)"
    
    size=$(stat -f%z "deploy/compose/docker-compose.yml" 2>/dev/null || stat -c%s "deploy/compose/docker-compose.yml")
    
    if [ "$size" -gt 500 ]; then
        pass "File size: $size bytes"
    else
        fail "File size too small: $size bytes"
        return 1
    fi
}

test_docker_compose_syntax() {
    log_test "Docker Compose YAML syntax is valid"
    
    if docker compose -f deploy/compose/docker-compose.yml config > /dev/null 2>&1; then
        pass "Syntax is valid"
    else
        fail "Syntax is invalid"
        docker compose -f deploy/compose/docker-compose.yml config 2>&1 | head -5
        return 1
    fi
}

test_services_defined() {
    log_test "All 5 services are defined"
    
    services=("api" "qdrant" "redis" "nginx" "ingest-worker")
    all_found=true
    
    for service in "${services[@]}"; do
        if docker compose -f deploy/compose/docker-compose.yml config 2>/dev/null | grep -q "service: $service"; then
            info "Service found: $service"
        else
            fail "Service not found: $service"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        pass "All 5 services defined"
    fi
}

test_containers_running() {
    log_test "All 5 containers are running"
    
    running=$(docker compose -f deploy/compose/docker-compose.yml ps --services 2>/dev/null | wc -l)
    
    if [ "$running" -eq 5 ]; then
        pass "5 containers are running"
    else
        fail "Expected 5 containers, found $running"
        docker compose -f deploy/compose/docker-compose.yml ps
        return 1
    fi
}

test_api_health() {
    log_test "API health check responds"
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        response=$(curl -s http://localhost:8000/health)
        pass "API health check: $response"
    else
        fail "API health check failed"
        return 1
    fi
}

test_api_root() {
    log_test "API root endpoint responds"
    
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        response=$(curl -s http://localhost:8000/ | head -c 50)
        pass "API root: $response..."
    else
        fail "API root endpoint failed"
        return 1
    fi
}

test_nginx_proxy() {
    log_test "Nginx reverse proxy responds"
    
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        response=$(curl -s http://localhost:8080/health)
        pass "Nginx proxy: $response"
    else
        fail "Nginx proxy failed"
        return 1
    fi
}

test_docker_network() {
    log_test "Docker network is created"
    
    if docker network ls 2>/dev/null | grep -q "rag_network\|compose_rag_network"; then
        pass "Docker network found"
    else
        fail "Docker network not found"
        return 1
    fi
}

test_volumes_created() {
    log_test "Docker volumes are created"
    
    volumes=("qdrant_data" "redis_data" "sources_data" "logs_data")
    all_found=true
    
    for volume in "${volumes[@]}"; do
        if docker volume ls 2>/dev/null | grep -q "compose_${volume}\|${volume}"; then
            info "Volume found: $volume"
        else
            fail "Volume not found: $volume"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        pass "All 4 volumes created"
    fi
}

test_nginx_config() {
    log_test "Nginx configuration file exists"
    
    if [ -f "deploy/nginx/nginx.conf" ]; then
        pass "nginx.conf exists"
    else
        fail "nginx.conf not found"
        return 1
    fi
}

test_dockerfiles_exist() {
    log_test "Dockerfiles exist for services"
    
    dockerfiles=("services/api/Dockerfile" "services/ingest/Dockerfile")
    all_found=true
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [ -f "$dockerfile" ]; then
            info "Dockerfile found: $dockerfile"
        else
            fail "Dockerfile not found: $dockerfile"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        pass "All Dockerfiles exist"
    fi
}

test_requirements_files() {
    log_test "Requirements.txt files exist"
    
    req_files=("services/api/requirements.txt" "services/ingest/requirements.txt")
    all_found=true
    
    for req_file in "${req_files[@]}"; do
        if [ -f "$req_file" ]; then
            info "Requirements found: $req_file"
        else
            fail "Requirements not found: $req_file"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        pass "All requirements.txt files exist"
    fi
}

test_env_file() {
    log_test "Environment file exists"
    
    if [ -f ".env" ]; then
        pass ".env file exists"
    else
        fail ".env file not found"
        return 1
    fi
}

test_env_example() {
    log_test ".env.example file exists"
    
    if [ -f ".env.example" ]; then
        pass ".env.example file exists"
    else
        fail ".env.example file not found"
        return 1
    fi
}

test_makefile_exists() {
    log_test "Makefile exists"
    
    if [ -f "Makefile" ]; then
        pass "Makefile exists"
    else
        fail "Makefile not found"
        return 1
    fi
}

test_validate_script_exists() {
    log_test "Validation script exists"
    
    if [ -f "scripts/validate-deployment.sh" ]; then
        pass "validate-deployment.sh exists"
    else
        fail "validate-deployment.sh not found"
        return 1
    fi
}

test_documentation_exists() {
    log_test "Documentation files exist"
    
    docs=("README.md" "docs/architecture.md" "docs/operations.md" "docs/security.md")
    all_found=true
    
    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            info "Doc found: $doc"
        else
            fail "Doc not found: $doc"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        pass "All documentation files exist"
    fi
}

test_lessons_learned() {
    log_test "Lessons learned documentation exists"
    
    if [ -d "specs/lessons-learned" ]; then
        count=$(find specs/lessons-learned -type f -name "*.md" 2>/dev/null | wc -l)
        pass "Lessons learned directory with $count documents"
    else
        fail "Lessons learned directory not found"
        return 1
    fi
}

# ==================== MAIN ====================

main() {
    clear
    
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║   SUBPROJECT 2 - AUTOMATED TEST SUITE                 ║
║   Docker Compose Validation                           ║
╚═══════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Change to project root
    cd "$(dirname "$0")/.." || exit 1
    
    # Run all tests
    header "STRUCTURAL TESTS"
    test_file_exists
    test_file_size
    test_docker_compose_syntax
    test_services_defined
    test_dockerfiles_exist
    test_requirements_files
    test_env_file
    test_env_example
    
    header "DOCKER TESTS"
    test_docker_network
    test_volumes_created
    test_containers_running
    
    header "ENDPOINT TESTS"
    test_api_health
    test_api_root
    test_nginx_proxy
    test_nginx_config
    
    header "AUTOMATION & DOCUMENTATION"
    test_makefile_exists
    test_validate_script_exists
    test_documentation_exists
    test_lessons_learned
    
    # Summary
    header "TEST SUMMARY"
    
    echo -e "${BLUE}Total Tests:${NC}     $TESTS_TOTAL"
    echo -e "${GREEN}Passed:${NC}         $TESTS_PASSED"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed:${NC}         $TESTS_FAILED"
    else
        echo -e "${GREEN}Failed:${NC}         $TESTS_FAILED"
    fi
    
    pass_percentage=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    echo -e "${BLUE}Success Rate:${NC}   ${pass_percentage}%"
    
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ ALL TESTS PASSED - SUBPROJECT 2 COMPLETE${NC}"
        echo -e "${GREEN}════════════════════════════════════════${NC}"
        return 0
    else
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${RED}❌ SOME TESTS FAILED - CHECK ERRORS ABOVE${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        return 1
    fi
}

# Execute main function
main "$@"
exit $?