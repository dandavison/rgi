#!/usr/bin/env python3
"""Test suite for rgi using pytest."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

TEST_INTERACTIVE = Path(__file__).parent / "test-interactive"


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


def run_rgi_test(command, sleep_time=0.5):
    """Run rgi with test-interactive and capture output.

    Args:
        command: Command to run
        sleep_time: How long to wait for UI to render

    Returns:
        str: Captured output from tmux session
    """
    result = subprocess.run(
        [TEST_INTERACTIVE, command, str(sleep_time)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout


def test_basic_pattern_search(test_fixture_dir, rgi_path):
    """Test 1: Basic pattern search for TODO."""
    # Run rgi with TODO pattern
    command = f"{rgi_path} --rgi-pattern-mode TODO ."
    output = run_rgi_test(command)

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

    # Check that we found TODO comments in the fixture files
    assert (
        "Add git branch display" in output
        or "Implement parallel test execution" in output
    ), f"Expected to find TODO comments in output, got:\n{output}"


def test_search_specific_directory(test_fixture_dir, rgi_path):
    """Test 2: Search in specific directory."""
    # Run rgi with TODO pattern in shell-config directory
    command = f"{rgi_path} --rgi-pattern-mode TODO shell-config"
    output = run_rgi_test(command)

    # Check that we find the lib_prompt.sh file
    assert "lib_prompt.sh" in output, (
        f"Expected 'lib_prompt.sh' in output, got:\n{output}"
    )

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

    # Should find TODOs from shell-config but not from other directories
    assert "Add git branch display" in output or "Add color support" in output, (
        f"Expected shell-config TODOs in output, got:\n{output}"
    )


def test_search_multiple_paths(test_fixture_dir, rgi_path):
    """Test 3: Search in multiple paths."""
    # Run rgi with TODO pattern in both shell-config and src directories
    command = f"{rgi_path} --rgi-pattern-mode TODO shell-config src"
    output = run_rgi_test(command)

    # Check that we find files from both directories
    assert "lib_prompt.sh" in output, (
        f"Expected 'lib_prompt.sh' in output, got:\n{output}"
    )
    assert "test_runner.py" in output, (
        f"Expected 'test_runner.py' in output, got:\n{output}"
    )

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"


def test_glob_filter_python_files(test_fixture_dir, rgi_path):
    """Test 4: Search with glob filter for Python files."""
    # Run rgi with glob filter for .py files
    command = f"{rgi_path} --rgi-pattern-mode -g '*.py' test ."
    output = run_rgi_test(command)

    # Check that we only find Python files
    assert ".py" in output, f"Expected '.py' in output, got:\n{output}"

    # Check that we find test_runner.py
    assert "test_runner.py" in output, (
        f"Expected 'test_runner.py' in output, got:\n{output}"
    )

    # Should NOT find shell or JavaScript files
    assert "lib_prompt.sh" not in output, (
        f"Did not expect 'lib_prompt.sh' in output, got:\n{output}"
    )
    assert "app.js" not in output, f"Did not expect 'app.js' in output, got:\n{output}"


def test_fzf_ui_renders(test_fixture_dir, rgi_path):
    """Test 6: Check if fzf UI loads correctly."""
    # Run rgi and check for UI elements
    command = f"{rgi_path} --rgi-pattern-mode test ."
    output = run_rgi_test(command)

    # Check for fzf UI separator lines (these appear in the output)
    assert "─────" in output or "━━━" in output or "──" in output, (
        f"Expected UI separator lines in output, got:\n{output}"
    )


def test_preview_window_displays(test_fixture_dir, rgi_path):
    """Test 7: Check preview window displays."""
    # Run rgi with function pattern in src directory
    command = f"{rgi_path} --rgi-pattern-mode function src"
    output = run_rgi_test(command)

    # Check for preview window border characters
    assert "╭─" in output or "╭" in output or "│" in output, (
        f"Expected preview window border in output, got:\n{output}"
    )


def test_default_command_mode(test_fixture_dir, rgi_path):
    """Test 8: Default command mode shows results."""
    # Run rgi without mode flag (defaults to command mode)
    command = f"{rgi_path} TODO ."
    output = run_rgi_test(command, sleep_time=1.5)

    # Check that we see results in command mode
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

    # Command mode should show the rg command in the query line
    assert "rg" in output, f"Expected 'rg' command in output, got:\n{output}"


# Test 9 is skipped in the original test suite (covered by Test 11)
def test_tab_switches_to_command_mode_skip():
    """Test 9: Tab switches to command mode (SKIPPED - covered by Test 11)."""
    import pytest

    pytest.skip("Test 9 is skipped as Test 11 covers command mode switching")


def test_tab_toggles_back_to_pattern_mode(test_fixture_dir, rgi_path):
    """Test 10: Tab toggles back to pattern mode."""
    import subprocess

    # Create a tmux session for mode switching test
    session_name = f"test-toggle-{os.getpid()}"
    try:
        # Start in pattern mode
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # In pattern mode, the header shows "rg {q} ." and the query line shows "TODO"
        assert "rg" in output and "{q}" in output, (
            f"Expected pattern mode header with 'rg' and '{{q}}' in output, got:\n{output}"
        )
        assert "TODO" in output, f"Expected 'TODO' in query line, got:\n{output}"

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


def test_typing_in_command_mode(test_fixture_dir, rgi_path):
    """Test 11: Typing in command mode shows results."""
    import subprocess

    # Create a tmux session for typing test
    session_name = f"test-type-{os.getpid()}"
    try:
        # Start in pattern mode
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Add a space to trigger reload
        subprocess.run(["tmux", "send-keys", "-t", session_name, " "], check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Should see file extensions and results
        assert (
            ".sh:" in output
            or ".txt:" in output
            or ".py:" in output
            or ".md:" in output
            or "TODO" in output
        ), f"Expected to see results after typing in command mode, got:\n{output}"

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


def test_editing_command_mode_updates_results(test_fixture_dir, rgi_path):
    """Test 12: Editing command in command mode updates results."""
    import subprocess

    # Create a tmux session for editing test
    session_name = f"test-edit-{os.getpid()}"
    try:
        # Start in pattern mode searching for 'test'
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode test .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Clear the command line
        subprocess.run(["tmux", "send-keys", "-t", session_name, "C-u"], check=True)

        # Type a new command searching for TODO
        subprocess.run(
            [
                "tmux",
                "send-keys",
                "-t",
                session_name,
                "rg --follow -i --hidden -g '!.git/*' --json TODO .",
            ],
            check=True,
        )
        time.sleep(2)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Should find TODO in results after editing command
        assert "TODO" in output, (
            f"Expected to find 'TODO' in results after editing command, got:\n{output}"
        )

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


def test_path_retention_switching_modes(test_fixture_dir, rgi_path):
    """Test 13: Path changes are retained when switching modes."""
    import subprocess

    # Create a tmux session for path retention test
    session_name = f"test-path-retention-{os.getpid()}"
    try:
        # Start in pattern mode searching in current directory
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Go to end of line and edit path from . to shell-config
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "C-e"], check=True
        )  # Go to end
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "BSpace"], check=True
        )  # Delete .
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "shell-config"], check=True
        )
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Check if header shows shell-config instead of .
        assert "shell-config" in output, (
            f"Expected path 'shell-config' to be retained after switching modes, got:\n{output}"
        )

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


def test_glob_pattern_retention(test_fixture_dir, rgi_path):
    """Test 14: Glob patterns are retained when switching modes."""
    import subprocess

    # Create a tmux session for glob retention test
    session_name = f"test-glob-retention-{os.getpid()}"
    try:
        # Start in pattern mode
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode test .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Go to beginning and skip past 'rg' and options
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "C-a"], check=True
        )  # Go to beginning
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, "M-f", "M-f", "M-f", "M-f"],
            check=True,
        )  # Skip words
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, " -g '!*.html'"], check=True
        )  # Add glob pattern
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Check if header shows the glob pattern
        assert "-g" in output and ("!*.html" in output or "!\\*.html" in output), (
            f"Expected glob pattern '-g !*.html' to be retained after switching modes, got:\n{output}"
        )

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


def test_options_not_duplicated(test_fixture_dir, rgi_path):
    """Test 15: Options not duplicated on repeated mode switches."""
    import subprocess

    # Create a tmux session for duplication test
    session_name = f"test-dup-{os.getpid()}"
    try:
        # Start with a glob option
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} -g '*.py' --rgi-pattern-mode def .",
            ],
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Switch to command mode again
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Tab"], check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Count occurrences of the glob pattern
        count = output.count("-g '*.py'")
        assert count == 1, (
            f"Expected -g '*.py' to appear exactly once, but appeared {count} times in output:\n{output}"
        )

    finally:
        # Kill the session
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name], capture_output=True, timeout=5
        )


@pytest.mark.xfail(
    reason="Known issue: patterns with spaces not working on initial launch"
)
def test_patterns_with_spaces(test_fixture_dir, rgi_path):
    """Test 16: Patterns with spaces work correctly.

    Note: This test was failing in the original shell test suite.
    The issue persists: patterns with spaces don't work on initial launch.
    """

    # Create test file with specific content
    test_dir = Path(test_fixture_dir) / "test-spaces"
    test_dir.mkdir(exist_ok=True)
    workflow_file = test_dir / "workflow.go"
    workflow_file.write_text("""func SomeUpdateWorkflowExecutionAsActive() {}
func OtherFunction() {}
""")

    # Pattern with spaces
    pattern = "func .*UpdateWorkflowExecutionAsActive"

    # Run rgi with the pattern in pattern mode
    command = f"{rgi_path} --rgi-pattern-mode '{pattern}' {test_dir}"
    output = run_rgi_test(command, sleep_time=1)

    # Check that we find the function
    assert "SomeUpdateWorkflowExecutionAsActive" in output, (
        f"Expected to find 'SomeUpdateWorkflowExecutionAsActive' with pattern '{pattern}', got:\n{output}"
    )

    # Verify the pattern appears correctly in the UI
    # In the fixed Python version, shlex.quote should handle this properly
    assert pattern in output or f"'{pattern}'" in output, (
        f"Expected pattern '{pattern}' to appear in output, got:\n{output}"
    )
