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
