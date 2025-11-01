"""
Test suite for rgi - Interactive ripgrep with fzf.

This pytest suite replaces the original shell test suite,
testing the Python implementation of rgi.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import pytest


class Fixtures:
    """Manages test fixtures for rgi tests."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def create(self):
        """Create test fixture files."""
        # Create subdirectories
        (self.base_dir / "shell-config").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "src").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "docs").mkdir(parents=True, exist_ok=True)
        
        # Shell script with TODO comments
        (self.base_dir / "shell-config" / "lib_prompt.sh").write_text("""#!/bin/bash
# Shell prompt library

# TODO: Add git branch display
function setup_prompt() {
    PS1="\\u@\\h:\\w$ "
}

# TODO: Add color support
function colorize_prompt() {
    # Function to add colors to prompt
    echo "Not implemented"
}

export -f setup_prompt
export -f colorize_prompt
""")
        
        # Python file with test functions and TODOs
        (self.base_dir / "src" / "test_runner.py").write_text("""#!/usr/bin/env python3
\"\"\"Test runner module with test utilities\"\"\"

import unittest

# TODO: Implement parallel test execution
def run_tests():
    \"\"\"Run all test suites\"\"\"
    loader = unittest.TestLoader()
    suite = loader.discover('.')
    runner = unittest.TextTestRunner()
    return runner.run(suite)

def test_function():
    \"\"\"A test function for demonstration\"\"\"
    # TODO: Add more test cases
    assert True, "This should pass"

if __name__ == "__main__":
    run_tests()
""")
        
        # Markdown documentation with TODOs
        (self.base_dir / "docs" / "README.md").write_text("""# Test Documentation

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
""")
        
        # Simple text file with various patterns
        (self.base_dir / "notes.txt").write_text("""Project Notes
=============

TODO: Review the test implementation
TODO: Update function signatures
TODO: Check import statements

Remember to test the following functions:
- test_function()
- setup_prompt()
- colorize_prompt()

Import the necessary modules before testing.
""")
        
        # JavaScript file with patterns
        (self.base_dir / "src" / "app.js").write_text("""// Application main file

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
""")
        
        # Config file
        (self.base_dir / ".rgi-test.conf").write_text("""# Configuration for testing
# TODO: Add more configuration options

test_enabled=true
function_tracing=on
import_checking=strict
""")


@pytest.fixture
def test_dir():
    """Create a temporary directory with test fixtures."""
    with tempfile.TemporaryDirectory(prefix="rgi-test-") as tmpdir:
        test_path = Path(tmpdir)
        fixtures = Fixtures(test_path)
        fixtures.create()
        yield test_path


def run_rgi(args: str, cwd: Path, timeout: float = 2.0) -> tuple[int, str, str]:
    """Run rgi command and capture output."""
    python_exe = sys.executable
    rgi_module_path = Path(__file__).parent.parent / "src"
    try:
        result = subprocess.run(
            f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -m rgi.cli {args}',
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def run_rgi_interactive(args: str, cwd: Path, sleep_time: float = 3.0) -> str:
    """Run rgi interactively in tmux and capture output."""
    session_name = f"test-{os.getpid()}-{int(time.time() * 1000)}"
    
    # Find the Python executable and rgi module path
    python_exe = sys.executable
    rgi_module_path = Path(__file__).parent.parent / "src"
    
    try:
        # Create tmux session running rgi with the current Python environment
        cmd = f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -m rgi.cli {args}'
        result = subprocess.run(
            f'tmux new-session -d -s "{session_name}" -c "{cwd}" bash -c \'{cmd}\'',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print(f"Failed to create tmux session: {result.stderr}")
            print(f"Command was: {cmd}")
            return ""
        
        # Wait for output
        time.sleep(sleep_time)
        
        # Capture pane content
        result = subprocess.run(
            f'tmux capture-pane -t "{session_name}" -p',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        return result.stdout
    finally:
        # Kill tmux session
        subprocess.run(
            f'tmux kill-session -t "{session_name}"',
            shell=True,
            capture_output=True,
        )


def get_rgi_command(args: str) -> str:
    """Get the command to run rgi with the current Python environment."""
    python_exe = sys.executable
    rgi_module_path = Path(__file__).parent.parent / "src"
    return f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -m rgi.cli {args}'


def send_keys_to_tmux(session_name: str, keys: str, sleep_after: float = 0.5):
    """Send keys to a tmux session."""
    subprocess.run(
        f'tmux send-keys -t "{session_name}" {keys}',
        shell=True,
        capture_output=True,
    )
    time.sleep(sleep_after)


class TestBasicFunctionality:
    """Test basic rgi functionality."""
    
    def test_basic_pattern_search(self, test_dir):
        """Test basic pattern search."""
        output = run_rgi_interactive("TODO .", test_dir)
        assert "TODO" in output, "Should find TODO in output"
    
    def test_search_specific_directory(self, test_dir):
        """Test searching in a specific directory."""
        output = run_rgi_interactive("TODO shell-config", test_dir)
        assert "lib_prompt.sh" in output, "Should find lib_prompt.sh"
    
    def test_multiple_paths(self, test_dir):
        """Test searching in multiple paths."""
        output = run_rgi_interactive("function src docs", test_dir)
        assert "function" in output, "Should find function"
    
    def test_glob_filter_python(self, test_dir):
        """Test glob filter for Python files."""
        output = run_rgi_interactive("-g '*.py' test .", test_dir)
        assert ".py" in output, "Should find Python files"
    
    def test_real_code_only_option(self, test_dir):
        """Test --real-code-only option."""
        output = run_rgi_interactive("--real-code-only TODO .", test_dir)
        assert "TODO" in output, "Should find TODO with --real-code-only"


class TestUIRendering:
    """Test UI rendering."""
    
    def test_fzf_ui_loads(self, test_dir):
        """Test if fzf UI loads correctly."""
        output = run_rgi_interactive("test .", test_dir)
        # Look for fzf border characters
        assert "─" in output or "│" in output, "Should show fzf UI borders"
    
    def test_preview_window_displays(self, test_dir):
        """Test if preview window displays."""
        output = run_rgi_interactive("function src", test_dir)
        # Look for preview window border
        assert "╭" in output or "─" in output, "Should show preview window"


class TestModeSwitching:
    """Test switching between pattern and command modes."""
    
    def test_tab_switches_to_command_mode(self, test_dir):
        """Test that Tab switches to command mode."""
        session_name = f"test-tab-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("TODO .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(3.0)
            
            # Press Tab
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # In command mode, the query should contain the full rg command
            assert "rg --follow" in result.stdout or "--json" in result.stdout, \
                   "Should show command mode with rg command"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )
    
    def test_tab_toggles_back_to_pattern_mode(self, test_dir):
        """Test that Tab toggles back to pattern mode."""
        session_name = f"test-toggle-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("TODO .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(3.0)
            
            # Press Tab twice
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # Should be back in pattern mode with header showing
            assert "rg --follow" in result.stdout, \
                   "Should show pattern mode header"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )
    
    def test_typing_in_command_mode_shows_results(self, test_dir):
        """Test that typing in command mode shows results."""
        session_name = f"test-type-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("TODO .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(3.0)
            
            # Switch to command mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Add a space to trigger reload
            send_keys_to_tmux(session_name, '" "', sleep_after=1.5)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # Should see results
            assert ("TODO" in result.stdout or 
                    ".sh:" in result.stdout or 
                    ".txt:" in result.stdout or
                    ".py:" in result.stdout), \
                   "Should show search results in command mode"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )
    
    def test_editing_command_updates_results(self, test_dir):
        """Test that editing command in command mode updates results."""
        session_name = f"test-edit-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("test .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(3.0)
            
            # Switch to command mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Edit command - go to end, delete ".", type "src"
            send_keys_to_tmux(session_name, "C-e", sleep_after=0.5)
            send_keys_to_tmux(session_name, "BSpace", sleep_after=0.5)
            send_keys_to_tmux(session_name, '"src"', sleep_after=1.5)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # Should see src results
            assert "src/test_runner.py" in result.stdout, \
                   "Should show results from src directory"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )
    
    def test_path_retention_when_switching_modes(self, test_dir):
        """Test that path changes are retained when switching modes."""
        session_name = f"test-path-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("TODO .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(3.0)
            
            # Switch to command mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Edit command to change . to shell-config
            send_keys_to_tmux(session_name, "C-e", sleep_after=0.5)
            send_keys_to_tmux(session_name, "BSpace", sleep_after=0.5)
            send_keys_to_tmux(session_name, '"shell-config"', sleep_after=1.5)
            
            # Switch back to pattern mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=1.5)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # Header should show shell-config
            assert "shell-config" in result.stdout, \
                   "Should retain path change in pattern mode header"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )
    
    def test_options_retention_in_mode_switch(self, test_dir):
        """Test that options added in command mode are retained."""
        session_name = f"test-options-{os.getpid()}"
        
        try:
            # Start rgi
            cmd = get_rgi_command("test .")
            subprocess.run(
                f'tmux new-session -d -s "{session_name}" -c "{test_dir}" bash -c \'{cmd}\'',
                shell=True,
                check=True,
                capture_output=True,
            )
            time.sleep(2.0)
            
            # Switch to command mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=2.0)
            
            # Clear line and retype with additional option
            send_keys_to_tmux(session_name, "C-u", sleep_after=0.5)
            send_keys_to_tmux(
                session_name, 
                '"rg --follow -i --hidden -g \'!.git/*\' -g \'!*.html\' --json test ."',
                sleep_after=2.0
            )
            
            # Switch back to pattern mode
            send_keys_to_tmux(session_name, "Tab", sleep_after=2.0)
            
            # Capture output
            result = subprocess.run(
                f'tmux capture-pane -t "{session_name}" -p',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            # Check if the header shows the glob filter
            assert ("-g" in result.stdout and "*.html" in result.stdout), \
                   "Should retain glob filter in pattern mode header"
        finally:
            subprocess.run(
                f'tmux kill-session -t "{session_name}"',
                shell=True,
                capture_output=True,
            )


class TestHelp:
    """Test help functionality."""
    
    def test_help_flag(self):
        """Test --help flag."""
        returncode, stdout, stderr = run_rgi("--help", Path.cwd())
        assert returncode == 0, "Should exit successfully"
        assert "Interactive ripgrep with fzf" in stdout, "Should show help text"
        assert "Examples:" in stdout, "Should show examples"
