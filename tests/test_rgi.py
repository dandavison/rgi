#!/usr/bin/env python3
"""Test suite for rgi using pytest."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def test_fixture_dir():
    """Create a temporary directory with test fixtures."""
    # Create temporary directory
    fixture_dir = tempfile.mkdtemp(prefix="test-fixture-")
    
    # Setup fixtures
    fixtures_script = Path(__file__).parent / "fixtures" / "setup_fixtures.sh"
    subprocess.run(["bash", str(fixtures_script), fixture_dir], check=True)
    
    # Change to fixture directory
    original_dir = os.getcwd()
    os.chdir(fixture_dir)
    
    yield fixture_dir
    
    # Cleanup
    os.chdir(original_dir)
    shutil.rmtree(fixture_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def rgi_path():
    """Get the path to the rgi script."""
    return str(Path(__file__).parent.parent / "src" / "rgi" / "scripts" / "rgi")


@pytest.fixture(scope="module")
def test_interactive():
    """Get the path to the test-interactive script."""
    return str(Path(__file__).parent / "test-interactive")


def run_rgi_test(test_interactive, command, sleep_time=0.5):
    """Run rgi with test-interactive and capture output.
    
    Args:
        test_interactive: Path to test-interactive script
        command: Command to run
        sleep_time: How long to wait for UI to render
        
    Returns:
        str: Captured output from tmux session
    """
    result = subprocess.run(
        [test_interactive, command, str(sleep_time)],
        capture_output=True,
        text=True,
        timeout=5
    )
    return result.stdout


def test_basic_pattern_search(test_fixture_dir, rgi_path, test_interactive):
    """Test 1: Basic pattern search for TODO."""
    # Run rgi with TODO pattern
    command = f"{rgi_path} --rgi-pattern-mode TODO ."
    output = run_rgi_test(test_interactive, command)
    
    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"
    
    # Check that we found TODO comments in the fixture files
    assert "Add git branch display" in output or "Implement parallel test execution" in output, \
        f"Expected to find TODO comments in output, got:\n{output}"


def test_search_specific_directory(test_fixture_dir, rgi_path, test_interactive):
    """Test 2: Search in specific directory."""
    # Run rgi with TODO pattern in shell-config directory
    command = f"{rgi_path} --rgi-pattern-mode TODO shell-config"
    output = run_rgi_test(test_interactive, command)
    
    # Check that we find the lib_prompt.sh file
    assert "lib_prompt.sh" in output, f"Expected 'lib_prompt.sh' in output, got:\n{output}"
    
    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"
    
    # Should find TODOs from shell-config but not from other directories
    assert "Add git branch display" in output or "Add color support" in output, \
        f"Expected shell-config TODOs in output, got:\n{output}"


def test_search_multiple_paths(test_fixture_dir, rgi_path, test_interactive):
    """Test 3: Search in multiple paths."""
    # Run rgi with TODO pattern in both shell-config and src directories
    command = f"{rgi_path} --rgi-pattern-mode TODO shell-config src"
    output = run_rgi_test(test_interactive, command)
    
    # Check that we find files from both directories
    assert "lib_prompt.sh" in output, f"Expected 'lib_prompt.sh' in output, got:\n{output}"
    assert "test_runner.py" in output, f"Expected 'test_runner.py' in output, got:\n{output}"
    
    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"


def test_glob_filter_python_files(test_fixture_dir, rgi_path, test_interactive):
    """Test 4: Search with glob filter for Python files."""
    # Run rgi with glob filter for .py files
    command = f"{rgi_path} --rgi-pattern-mode -g '*.py' test ."
    output = run_rgi_test(test_interactive, command)
    
    # Check that we only find Python files
    assert ".py" in output, f"Expected '.py' in output, got:\n{output}"
    
    # Check that we find test_runner.py
    assert "test_runner.py" in output, f"Expected 'test_runner.py' in output, got:\n{output}"
    
    # Should NOT find shell or JavaScript files
    assert "lib_prompt.sh" not in output, f"Did not expect 'lib_prompt.sh' in output, got:\n{output}"
    assert "app.js" not in output, f"Did not expect 'app.js' in output, got:\n{output}"


def test_real_code_only_option(test_fixture_dir, rgi_path, test_interactive):
    """Test 5: Search with --real-code-only option."""
    # Run rgi with --real-code-only option (passes through to ripgrep)
    command = f"{rgi_path} --rgi-pattern-mode --real-code-only TODO ."
    output = run_rgi_test(test_interactive, command)
    
    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"
    
    # With --real-code-only, we should still find TODOs in code files
    # This option is likely a custom alias that gets passed to ripgrep


def test_fzf_ui_renders(test_fixture_dir, rgi_path, test_interactive):
    """Test 6: Check if fzf UI loads correctly."""
    # Run rgi and check for UI elements
    command = f"{rgi_path} --rgi-pattern-mode test ."
    output = run_rgi_test(test_interactive, command)
    
    # Check for fzf UI separator lines (these appear in the output)
    assert "─────" in output or "━━━" in output or "──" in output, \
        f"Expected UI separator lines in output, got:\n{output}"


def test_preview_window_displays(test_fixture_dir, rgi_path, test_interactive):
    """Test 7: Check preview window displays."""
    # Run rgi with function pattern in src directory
    command = f"{rgi_path} --rgi-pattern-mode function src"
    output = run_rgi_test(test_interactive, command)
    
    # Check for preview window border characters
    assert "╭─" in output or "╭" in output or "│" in output, \
        f"Expected preview window border in output, got:\n{output}"
