#!/bin/bash
# Run multi-path tests with CodeWiki virtual environment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}CodeWiki Multi-Path Feature Test Suite${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Find CodeWiki root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEWIKI_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "\n${YELLOW}Setup:${NC}"
echo -e "  Test directory: $SCRIPT_DIR"
echo -e "  CodeWiki root:  $CODEWIKI_ROOT"

# Check virtual environment
if [ ! -d "$CODEWIKI_ROOT/venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at $CODEWIKI_ROOT/venv${NC}"
    exit 1
fi

echo -e "  Virtual env:    $CODEWIKI_ROOT/venv"

# Activate virtual environment and run tests
echo -e "\n${YELLOW}Running tests...${NC}\n"

cd "$SCRIPT_DIR"
source "$CODEWIKI_ROOT/venv/bin/activate"
python test_multi_path.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "\n${GREEN}✓ Test suite completed successfully${NC}"
else
    echo -e "\n${RED}✗ Test suite failed with exit code $exit_code${NC}"
fi

exit $exit_code
