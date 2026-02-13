#!/bin/bash
# Test Runner Script for Job Copilot Agent System
# Usage: ./run_tests.sh [test_name] [options]
# Uses `uv` for package management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/prateekbidve/Desktop/full_stack"
BACKEND_DIR="$PROJECT_ROOT/backend"
TESTS_DIR="$BACKEND_DIR/tests/agents"

echo -e "${YELLOW}Job Copilot Agent System - Test Runner${NC}"
echo "========================================"

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}Loading .env file...${NC}"
        export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
    else
        echo -e "${RED}⚠ OPENAI_API_KEY not set${NC}"
        echo "Set it in .env file or environment: export OPENAI_API_KEY=your_key"
    fi
fi

# Change to project directory
cd "$PROJECT_ROOT"

# Detect package manager (prefer uv, fallback to pip)
if command -v uv &> /dev/null; then
    PYTEST_CMD="uv run pytest"
    echo -e "${GREEN}Using uv${NC}"
else
    PYTEST_CMD="python3 -m pytest"
    echo -e "${YELLOW}uv not found, using pip${NC}"
fi

# Test functions
run_all_tests() {
    echo -e "\n${YELLOW}Running all tests...${NC}"
    $PYTEST_CMD "$TESTS_DIR" -v --tb=short
}

run_utils_tests() {
    echo -e "\n${YELLOW}Running utility tests...${NC}"
    $PYTEST_CMD "$TESTS_DIR/test_utils.py" -v
}

run_state_tests() {
    echo -e "\n${YELLOW}Running state management tests...${NC}"
    $PYTEST_CMD "$TESTS_DIR/test_state.py" -v
}

run_security_tests() {
    echo -e "\n${YELLOW}Running security tests...${NC}"
    $PYTEST_CMD "$TESTS_DIR/test_security.py" -v
}

run_api_tests() {
    echo -e "\n${YELLOW}Running API integration tests...${NC}"
    python3 -m pytest "$TESTS_DIR/test_fastapi_integration.py" -v
}

run_llm_tests() {
    echo -e "\n${YELLOW}Running LLM integration tests...${NC}"
    python3 -m pytest "$TESTS_DIR/test_llm.py" -v
}

run_nodes_tests() {
    echo -e "\n${YELLOW}Running workflow nodes tests...${NC}"
    python3 -m pytest "$TESTS_DIR/test_nodes.py" -v
}

run_integration_tests() {
    echo -e "\n${YELLOW}Running integration tests...${NC}"
    python3 -m pytest "$TESTS_DIR/test_integration.py" -v
}

run_coverage() {
    echo -e "\n${YELLOW}Running tests with coverage report...${NC}"
    python3 -m pytest "$TESTS_DIR" --cov=app.services.agents --cov-report=html --cov-report=term-missing
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

run_fast() {
    echo -e "\n${YELLOW}Running only fast tests...${NC}"
    python3 -m pytest "$TESTS_DIR" -v -m "not slow" 2>/dev/null || python3 -m pytest "$TESTS_DIR" -v
}

run_debug() {
    TEST_NAME=${1:-.}
    echo -e "\n${YELLOW}Running $TEST_NAME with debugging...${NC}"
    python3 -m pytest "$TESTS_DIR/$TEST_NAME" -vv --tb=long -s
}

# Main script logic
case "${1:-all}" in
    all)
        run_all_tests
        ;;
    utils)
        run_utils_tests
        ;;
    state)
        run_state_tests
        ;;
    security)
        run_security_tests
        ;;
    api)
        run_api_tests
        ;;
    llm)
        run_llm_tests
        ;;
    nodes)
        run_nodes_tests
        ;;
    integration)
        run_integration_tests
        ;;
    coverage)
        run_coverage
        ;;
    fast)
        run_fast
        ;;
    debug)
        run_debug "${2:-.}"
        ;;
    *)
        echo -e "${RED}Unknown test suite: ${1}${NC}"
        echo ""
        echo "Available test suites:"
        echo "  all          - Run all tests"
        echo "  utils        - Run utility function tests"
        echo "  state        - Run state management tests"
        echo "  security     - Run security tests"
        echo "  api          - Run API endpoint tests"
        echo "  llm          - Run LLM integration tests"
        echo "  nodes        - Run workflow node tests"
        echo "  integration  - Run integration tests"
        echo "  coverage     - Run all tests with coverage report"
        echo "  fast         - Run fast tests only"
        echo "  debug [test] - Run test with debugging enabled"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests completed successfully${NC}"
else
    echo -e "\n${RED}✗ Tests failed${NC}"
    exit 1
fi
