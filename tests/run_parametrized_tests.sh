#!/bin/bash

# Simple test runner for parametrized tests
# This demonstrates the test coverage even without pytest

echo "================================"
echo "  Parametrized Test Coverage"
echo "================================"
echo ""
echo "The following tests have been parametrized to test BOTH modes:"
echo ""

# Extract parametrized tests from test_rgi.py
echo "Parametrized tests in test_rgi.py:"
grep '@pytest.mark.parametrize("mode"' tests/test_rgi.py -A1 | grep "^def test_" | sed 's/def /  - /' | sed 's/(.*/:/'

echo ""
echo "================================"
echo "  Test Execution Matrix"
echo "================================"
echo ""
echo "Each parametrized test runs in:"
echo "  ✓ Pattern mode (--rgi-pattern-mode)"
echo "  ✓ Command mode (--rgi-command-mode)"
echo ""
echo "Total test scenarios:"
PARAM_COUNT=$(grep '@pytest.mark.parametrize("mode"' tests/test_rgi.py | wc -l)
echo "  - $PARAM_COUNT parametrized tests × 2 modes = $(($PARAM_COUNT * 2)) test runs"
echo ""
echo "Mode-specific tests (not parametrized):"
grep "^def test_" tests/test_rgi.py | grep -v -B1 '@pytest.mark.parametrize' | head -20 | sed 's/def /  - /' | sed 's/(.*/:/' | grep -v "test_basic_pattern_search" | grep -v "test_search_specific_directory" | grep -v "test_search_multiple_paths" | grep -v "test_glob_filter_python_files" | grep -v "test_fzf_ui_renders" | grep -v "test_preview_window_displays" | grep -v "test_patterns_with_spaces"

echo ""
echo "================================"
echo "  Running Sample Tests"  
echo "================================"
echo ""
echo "To run these tests with pytest:"
echo "  pip install pytest"
echo "  pytest tests/test_rgi.py -v"
echo ""
echo "To run only the parametrized tests:"
echo "  pytest tests/test_rgi.py -k 'test_basic_pattern_search or test_search_specific_directory or test_search_multiple_paths or test_glob_filter_python_files or test_fzf_ui_renders or test_preview_window_displays or test_patterns_with_spaces' -v"
echo ""
echo "To run a specific parametrized test in both modes:"
echo "  pytest tests/test_rgi.py::test_basic_pattern_search -v"
