#!/usr/bin/env python3
"""
Quick validation script for Subproject 7: Vector Retrieval & Ranking
Verifies all components are in place and working.
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  {text}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅{NC} {text}")

def print_error(text):
    """Print error message."""
    print(f"{RED}❌{NC} {text}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️{NC} {text}")

def check_file(path, description):
    """Check if file exists."""
    if os.path.isfile(path):
        size = os.path.getsize(path)
        print_success(f"{description} ({size} bytes)")
        return True
    else:
        print_error(f"{description} (NOT FOUND: {path})")
        return False

def check_dir(path, description):
    """Check if directory exists."""
    if os.path.isdir(path):
        print_success(f"{description}")
        return True
    else:
        print_error(f"{description} (NOT FOUND: {path})")
        return False

def check_function_in_file(filepath, function_name):
    """Check if function exists in file."""
    if not os.path.isfile(filepath):
        print_error(f"Function {function_name}() - FILE NOT FOUND: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if f"def {function_name}" in content or f"async def {function_name}" in content:
            print_success(f"Function: {function_name}()")
            return True
        else:
            print_error(f"Function: {function_name}() NOT FOUND in {filepath}")
            return False

def check_class_in_file(filepath, class_name):
    """Check if class exists in file."""
    if not os.path.isfile(filepath):
        print_error(f"Class {class_name} - FILE NOT FOUND: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if f"class {class_name}" in content:
            print_success(f"Class: {class_name}")
            return True
        else:
            print_error(f"Class: {class_name} NOT FOUND in {filepath}")
            return False

def check_import(module_path):
    """Check if module can be imported."""
    try:
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        parts = module_path.replace('/', '.').replace('\\', '.').replace('.py', '').split('.')
        module_name = '.'.join(parts)
        __import__(module_name)
        print_success(f"Import: {module_name}")
        return True
    except Exception as e:
        print_error(f"Import: {module_path} - {str(e)}")
        return False

def count_lines(filepath):
    """Count lines in file."""
    if not os.path.isfile(filepath):
        return 0
    with open(filepath, 'r', encoding='utf-8') as f:
        return len(f.readlines())

def main():
    """Main validation routine."""
    print_header("SUBPROJECT 7 QUICK VALIDATION")
    
    checks_passed = 0
    checks_failed = 0
    
    # Define paths
    base_path = Path(__file__).parent.parent
    app_path = base_path / "services" / "api" / "app"
    routes_path = app_path / "routes"
    
    # ============ DIRECTORIES ============
    print_header("1. CHECKING DIRECTORIES")
    
    if check_dir(str(app_path), "Directory: services/api/app/"):
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_dir(str(routes_path), "Directory: services/api/app/routes/"):
        checks_passed += 1
    else:
        checks_failed += 1
    
    # ============ CORE FILES ============
    print_header("2. CHECKING CORE FILES")
    
    files_to_check = [
        (str(app_path / "qdrant_client.py"), "Qdrant Client"),
        (str(app_path / "retrieval.py"), "Retrieval Module"),
        (str(app_path / "models.py"), "Data Models"),
        (str(app_path / "__init__.py"), "App Module Init"),
        (str(routes_path / "query.py"), "Query Endpoint"),
        (str(routes_path / "__init__.py"), "Routes Init"),
    ]
    
    for filepath, description in files_to_check:
        if check_file(filepath, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # ============ SUPPORT FILES ============
    print_header("3. CHECKING SUPPORT FILES")
    
    support_files = [
        (str(app_path / "README.md"), "Module README"),
        (str(base_path / "scripts" / "seed_demo_data.py"), "Demo Data Script"),
        (str(base_path / "docs" / "qdrant.md"), "Qdrant Documentation"),
        (str(base_path / "tests" / "test_retrieval.py"), "Test Suite"),
    ]
    
    for filepath, description in support_files:
        if check_file(filepath, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # ============ FUNCTIONS ============
    print_header("4. CHECKING FUNCTIONS")
    
    print(f"{YELLOW}In qdrant_client.py:{NC}")
    for func in ["get_client", "ensure_collection", "upsert_chunks", "search", "delete_collection"]:
        if check_function_in_file(str(app_path / "qdrant_client.py"), func):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print(f"\n{YELLOW}In retrieval.py:{NC}")
    for func in ["get_embedding", "retrieve_context"]:
        if check_function_in_file(str(app_path / "retrieval.py"), func):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print(f"\n{YELLOW}In routes/query.py:{NC}")
    if check_function_in_file(str(routes_path / "query.py"), "query_rag"):
        checks_passed += 1
    else:
        checks_failed += 1
    
    # ============ CLASSES ============
    print_header("5. CHECKING PYDANTIC MODELS")
    
    for cls in ["ContextChunk", "QueryRequest", "QueryResponse"]:
        if check_class_in_file(str(app_path / "models.py"), cls):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # ============ CODE METRICS ============
    print_header("6. CODE METRICS")
    
    files_to_count = [
        (str(app_path / "qdrant_client.py"), "qdrant_client.py"),
        (str(app_path / "retrieval.py"), "retrieval.py"),
        (str(app_path / "models.py"), "models.py"),
        (str(routes_path / "query.py"), "query.py"),
        (str(app_path / "__init__.py"), "app/__init__.py"),
        (str(routes_path / "__init__.py"), "routes/__init__.py"),
        (str(base_path / "scripts" / "seed_demo_data.py"), "seed_demo_data.py"),
        (str(base_path / "docs" / "qdrant.md"), "qdrant.md"),
        (str(base_path / "tests" / "test_retrieval.py"), "test_retrieval.py"),
    ]
    
    total_lines = 0
    for filepath, name in files_to_count:
        lines = count_lines(filepath)
        total_lines += lines
        if lines > 0:
            print_info(f"{name}: {lines} lines")
    
    print_success(f"Total code: {total_lines} lines")
    
    # ============ TEST COUNT ============
    print_header("7. TEST COVERAGE")
    
    test_file = str(base_path / "tests" / "test_retrieval.py")
    if os.path.isfile(test_file):
        with open(test_file, 'r') as f:
            content = f.read()
            test_count = content.count("def test_")
            print_success(f"Test functions: {test_count}")
            checks_passed += 1
    else:
        print_error(f"Test file not found: {test_file}")
        checks_failed += 1
    
    # ============ FINAL SUMMARY ============
    print_header("VALIDATION SUMMARY")
    
    print_info(f"Checks passed: {GREEN}{checks_passed}{NC}")
    print_info(f"Checks failed: {RED}{checks_failed}{NC}")
    
    if checks_failed == 0:
        print_header("✅ SUBPROJECT 7 VALIDATION PASSED")
        print_success("All components are in place and ready!")
        print_success("Next: Run 'bash scripts/validate-sp7.sh' for full validation")
        return 0
    else:
        print_header("❌ SUBPROJECT 7 VALIDATION FAILED")
        print_error(f"{checks_failed} issues found - please check above")
        return 1

if __name__ == "__main__":
    sys.exit(main())