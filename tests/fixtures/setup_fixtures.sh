#!/bin/bash

# Setup test fixtures for rgi tests
# Creates a temporary directory with sample files for testing

FIXTURE_DIR="${1:-test-fixture}"

# Create the fixture directory
mkdir -p "$FIXTURE_DIR"
cd "$FIXTURE_DIR"

# Create subdirectories
mkdir -p shell-config
mkdir -p src
mkdir -p docs

# Create sample shell script with TODO comments
cat > shell-config/lib_prompt.sh << 'EOF'
#!/bin/bash
# Shell prompt library

# TODO: Add git branch display
function setup_prompt() {
    PS1="\u@\h:\w$ "
}

# TODO: Add color support
function colorize_prompt() {
    # Function to add colors to prompt
    echo "Not implemented"
}

export -f setup_prompt
export -f colorize_prompt
EOF

# Create Python file with test functions and TODOs
cat > src/test_runner.py << 'EOF'
#!/usr/bin/env python3
"""Test runner module with test utilities"""

import unittest

# TODO: Implement parallel test execution
def run_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = loader.discover('.')
    runner = unittest.TextTestRunner()
    return runner.run(suite)

def test_function():
    """A test function for demonstration"""
    # TODO: Add more test cases
    assert True, "This should pass"

if __name__ == "__main__":
    run_tests()
EOF

# Create markdown documentation with TODOs
cat > docs/README.md << 'EOF'
# Test Documentation

This is a test document for rgi testing.

## TODO List

- [ ] TODO: Write comprehensive documentation
- [ ] TODO: Add usage examples
- [ ] TODO: Include API reference

## Functions

The `test_function()` is used for testing.
The `setup_prompt()` function configures the shell prompt.

## Import Statements

```python
import unittest
import sys
```
EOF

# Create a simple text file with various patterns
cat > notes.txt << 'EOF'
Project Notes
=============

TODO: Review the test implementation
TODO: Update function signatures
TODO: Check import statements

Remember to test the following functions:
- test_function()
- setup_prompt()
- colorize_prompt()

Import the necessary modules before testing.
EOF

# Create a JavaScript file with patterns
cat > src/app.js << 'EOF'
// Application main file

// TODO: Implement error handling
function testFunction() {
    console.log("Test function called");
    return true;
}

// TODO: Add import for utilities
// import { utils } from './utils';

function handleRequest() {
    // Function to handle incoming requests
    testFunction();
}

module.exports = { testFunction, handleRequest };
EOF

# Create a config file
cat > .rgi-test.conf << 'EOF'
# Configuration for testing
# TODO: Add more configuration options

test_enabled=true
function_tracing=on
import_checking=strict
EOF

echo "Test fixtures created in $FIXTURE_DIR"
echo "Files created:"
find . -type f | sort
