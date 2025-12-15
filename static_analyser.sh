#!/bin/bash

# Static Code Analysis Script
# Runs comprehensive code quality checks on Python files
# Usage: ./static_analysis.sh [file_pattern]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# File pattern to analyze (default: all Python files in current directory)
FILE_PATTERN="${1:-*.py}"

# Summary counters
TOTAL_ERRORS=0
CHECKERS_RUN=0
ERROR_CHECKERS=0

echo -e "${BLUE}🔍 Static Code Analysis Report${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Analyzing files: ${FILE_PATTERN}"
echo -e "Time: $(date)"
echo ""

# Function to run a checker with error handling
run_checker() {
    local checker_name=$1
    local checker_command=$2
    local checker_options=$3

    echo -e "${YELLOW}📋 Running $checker_name...${NC}"

    if command -v $checker_name &> /dev/null; then
        CHECKERS_RUN=$((CHECKERS_RUN + 1))

        # Run the checker and capture output
        local output
        local exit_code

        output=$(eval "$checker_command $checker_options $FILE_PATTERN" 2>&1)
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✅ $checker_name: PASSED${NC}"
        else
            echo -e "${RED}❌ $checker_name: FAILED${NC}"
            echo "$output"
            ERROR_CHECKERS=$((ERROR_CHECKERS + 1))
        fi

        # Count actual error lines (exclude headers, summaries, etc.)
        local error_count
        error_count=$(echo "$output" | grep -E "(error|Error|ERROR|warning|Warning|WARNING|:[0-9]+:)" | wc -l)
        TOTAL_ERRORS=$((TOTAL_ERRORS + error_count))

        echo ""
    else
        echo -e "${RED}⚠️  $checker_name: NOT INSTALLED${NC}"
        echo ""
    fi
}

# Check if virtual environment should be activated
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    echo -e "${BLUE}🐍 Activating virtual environment (.venv)...${NC}"
    source .venv/bin/activate
    echo ""
elif [ -d ".." ] && [ -f "../bin/activate" ]; then
    echo -e "${BLUE}🐍 Activating parent virtual environment...${NC}"
    source ../bin/activate
    echo ""
fi

# Run all static analysis tools
run_checker "ruff" "ruff" "check"
run_checker "mypy" "python -m mypy" "--ignore-missing-imports"
run_checker "pylint" "python -m pylint" "--score=yes"
run_checker "pyflakes" "python -m pyflakes" ""
run_checker "pycodestyle" "python -m pycodestyle" "--first --max-line-length=100"
run_checker "flake8" "flake8" "--max-line-length=100"

# Summary
echo -e "${BLUE}📊 Analysis Summary${NC}"
echo -e "${BLUE}=================${NC}"
echo -e "Checkers run: $CHECKERS_RUN"
echo -e "Checkers failed: $ERROR_CHECKERS"
echo -e "Total issues found: $TOTAL_ERRORS"

if [ $ERROR_CHECKERS -eq 0 ]; then
    echo -e "${GREEN}🎉 All static analysis checks PASSED!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some checks FAILED. Please review the issues above.${NC}"
    exit 1
fi
