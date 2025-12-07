#!/usr/bin/env python3
"""Test suite for rgi using pytest."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator, List

import pytest


def is_wsl() -> bool:
    """Check if we're running in WSL (Windows Subsystem for Linux).

    WSL kernels include 'microsoft' in the release string.
    This works for both WSL1 and WSL2.
    """
    return 'microsoft' in platform.uname().release.lower()

TEST_INTERACTIVE = Path(__file__).parent / "test-interactive"


@pytest.fixture(scope="function")
def test_fixture_dir() -> Generator[str, None, None]:
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
def rgi_path() -> str:
    """Get the path to the rgi script."""
    return str(Path(__file__).parent.parent / "src" / "rgi" / "scripts" / "rgi")


def run_rgi_test(command: str, sleep_time: float = 0.5) -> str:
    """Run rgi with test-interactive and capture output.

    Args:
        command: Command to run
        sleep_time: How long to wait for UI to render

    Returns:
        str: Captured output from tmux session
    """
    # In CI, we might need more time for processes to start
    if os.environ.get("CI") == "true":
        sleep_time += 0.5

    result = subprocess.run(
        [TEST_INTERACTIVE, command, str(sleep_time)],
        capture_output=True,
        text=True,
        timeout=10,  # Increased timeout for CI
    )
    return result.stdout


def get_test_tmux_socket(session_name: str) -> str:
    """Get a unique tmux socket name for testing.

    This ensures tests run in an isolated tmux server that doesn't
    interfere with the user's tmux session.

    Args:
        session_name: Name of the test session

    Returns:
        str: Socket name for tmux -L flag
    """
    return f"test-socket-{session_name}"


def tmux_cmd(socket: str, *args: str) -> List[str]:
    """Build a tmux command with the test socket.

    Args:
        socket: Socket name for tmux -L flag
        *args: Additional tmux arguments

    Returns:
        list: Command list for subprocess.run
    """
    return ["tmux", "-L", socket] + list(args)


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_basic_pattern_search(test_fixture_dir, rgi_path, mode):
    """Test 1: Basic pattern search for TODO in both modes."""
    # Run rgi with TODO pattern
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode TODO ."
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode TODO ."
    output = run_rgi_test(command)

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in {mode} mode output, got:\n{output}"

    # Check that we found TODO comments in the fixture files
    assert (
        "Implement error handling" in output
        or "Review the test implementation" in output
        or "Add git branch display" in output
        or "Implement parallel test execution" in output
    ), f"Expected to find TODO comments in {mode} mode output, got:\n{output}"


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_search_specific_directory(test_fixture_dir, rgi_path, mode):
    """Test 2: Search in specific directory in both modes."""
    # Run rgi with TODO pattern in shell-config directory
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode TODO shell-config"
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode TODO shell-config"
    output = run_rgi_test(command)

    # Check that we find the lib_prompt.sh file
    assert "lib_prompt.sh" in output, (
        f"Expected 'lib_prompt.sh' in {mode} mode output, got:\n{output}"
    )

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in {mode} mode output, got:\n{output}"

    # Should find TODOs from shell-config but not from other directories
    assert "Add git branch display" in output or "Add color support" in output, (
        f"Expected shell-config TODOs in {mode} mode output, got:\n{output}"
    )


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_search_multiple_paths(test_fixture_dir, rgi_path, mode):
    """Test 3: Search in multiple paths in both modes."""
    # Run rgi with TODO pattern in both shell-config and src directories
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode TODO shell-config src"
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode TODO shell-config src"
    output = run_rgi_test(command)

    # Check that we find files from both directories
    assert "lib_prompt.sh" in output, (
        f"Expected 'lib_prompt.sh' in {mode} mode output, got:\n{output}"
    )
    assert "test_runner.py" in output, (
        f"Expected 'test_runner.py' in {mode} mode output, got:\n{output}"
    )

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in {mode} mode output, got:\n{output}"


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_glob_filter_python_files(test_fixture_dir, rgi_path, mode):
    """Test 4: Search with glob filter for Python files in both modes."""
    # Run rgi with glob filter for .py files
    if mode == "pattern":
        command = f"{rgi_path} -g '*.py' --rgi-pattern-mode test ."
    else:  # command mode
        command = f"{rgi_path} -g '*.py' --rgi-command-mode test ."
    output = run_rgi_test(command)

    # Check that we only find Python files
    assert ".py" in output, f"Expected '.py' in {mode} mode output, got:\n{output}"

    # Check that we find test_runner.py
    assert "test_runner.py" in output, (
        f"Expected 'test_runner.py' in {mode} mode output, got:\n{output}"
    )

    # Should NOT find shell or JavaScript files
    assert "lib_prompt.sh" not in output, (
        f"Did not expect 'lib_prompt.sh' in {mode} mode output, got:\n{output}"
    )
    assert "app.js" not in output, f"Did not expect 'app.js' in {mode} mode output, got:\n{output}"


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_fzf_ui_renders(test_fixture_dir, rgi_path, mode):
    """Test 6: Check if fzf UI loads correctly in both modes."""
    # Run rgi and check for UI elements
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode test ."
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode test ."
    output = run_rgi_test(command)

    # Check for fzf UI separator lines (these appear in the output)
    assert "─────" in output or "━━━" in output or "──" in output, (
        f"Expected UI separator lines in {mode} mode output, got:\n{output}"
    )


@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_preview_window_displays(test_fixture_dir, rgi_path, mode):
    """Test 7: Check preview window displays in both modes."""
    # Run rgi with function pattern in src directory
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode function src"
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode function src"
    output = run_rgi_test(command)

    # Check for preview window border characters
    assert "╭─" in output or "╭" in output or "│" in output, (
        f"Expected preview window border in {mode} mode output, got:\n{output}"
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
    socket = get_test_tmux_socket(session_name)

    try:
        # Start in pattern mode
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_typing_in_command_mode(test_fixture_dir, rgi_path):
    """Test 11: Typing in command mode shows results."""
    import subprocess

    # Create a tmux session for typing test
    session_name = f"test-type-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start in pattern mode
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Add a space to trigger reload
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, " "), check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


@pytest.mark.skipif(
    is_wsl(),
    reason="Complex keyboard editing in tmux doesn't work reliably in WSL CI environment"
)
def test_editing_command_mode_updates_results(test_fixture_dir, rgi_path):
    """Test 12: Editing command in command mode updates results."""
    import subprocess

    # Create a tmux session for editing test
    session_name = f"test-edit-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start in pattern mode searching for 'test'
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode test .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Clear the command line
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "C-u"), check=True)

        # Type a new command searching for TODO
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                "rg TODO .",
            ),
            check=True,
        )
        time.sleep(2)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_path_retention_switching_modes(test_fixture_dir, rgi_path):
    """Test 13: Path changes are retained when switching modes."""
    import subprocess

    # Create a tmux session for path retention test
    session_name = f"test-path-retention-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start in pattern mode searching in current directory
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode TODO .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Go to end of line and edit path from . to shell-config
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "C-e"), check=True
        )  # Go to end
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "BSpace"), check=True
        )  # Delete .
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "shell-config"),
            check=True,
        )
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_glob_pattern_retention(test_fixture_dir, rgi_path):
    """Test 14: Glob patterns are retained when switching modes."""
    import subprocess

    # Create a tmux session for glob retention test
    session_name = f"test-glob-retention-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start in pattern mode
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-pattern-mode test .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Go to beginning and skip past 'rg' and options
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "C-a"), check=True
        )  # Go to beginning
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "M-f", "M-f", "M-f", "M-f"),
            check=True,
        )  # Skip words
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, " -g '!*.html'"),
            check=True,
        )  # Add glob pattern
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_options_not_duplicated(test_fixture_dir, rgi_path):
    """Test 15: Options not duplicated on repeated mode switches."""
    import subprocess

    # Create a tmux session for duplication test
    session_name = f"test-dup-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start with a glob option
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} -g '*.py' --rgi-pattern-mode def .",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Switch to command mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Switch back to pattern mode
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Switch to command mode again
        subprocess.run(tmux_cmd(socket, "send-keys", "-t", session_name, "Tab"), check=True)
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
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
        # Kill the session and server
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_history_navigation(test_fixture_dir, rgi_path):
    """Test: Alt+Up/Alt+Down navigates search history in command mode."""
    import subprocess

    # Create a history file with a previous search
    history_file = Path.home() / ".rgi_history"
    original_history = None
    if history_file.exists():
        original_history = history_file.read_text()

    try:
        # Write a known history entry
        history_file.write_text("rg PREVIOUS_HISTORY_ENTRY .\n")

        # Create a tmux session
        session_name = f"test-history-{os.getpid()}"
        socket = get_test_tmux_socket(session_name)

        try:
            # Start rgi in command mode with a different query
            subprocess.run(
                tmux_cmd(
                    socket,
                    "new-session",
                    "-d",
                    "-s",
                    session_name,
                    "-c",
                    test_fixture_dir,
                    f"{rgi_path} --rgi-command-mode TODO .",
                ),
                check=True,
                timeout=5,
            )
            time.sleep(1.5)

            # Press Alt+Up to go to previous history
            subprocess.run(
                tmux_cmd(socket, "send-keys", "-t", session_name, "M-Up"),
                check=True,
            )
            time.sleep(0.5)

            # Capture output
            result = subprocess.run(
                tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout

            # The query line should now show the history entry
            assert "PREVIOUS_HISTORY_ENTRY" in output, (
                f"Expected history entry 'PREVIOUS_HISTORY_ENTRY' after Alt+Up, got:\n{output}"
            )

        finally:
            subprocess.run(
                tmux_cmd(socket, "kill-session", "-t", session_name),
                capture_output=True,
                timeout=5,
            )
            subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)

    finally:
        # Restore original history
        if original_history is not None:
            history_file.write_text(original_history)
        elif history_file.exists():
            history_file.unlink()


def test_history_saves_on_enter(test_fixture_dir, rgi_path):
    """Test: History is saved when pressing Enter to open a result."""
    import subprocess

    history_file = Path.home() / ".rgi_history"
    original_history = None
    if history_file.exists():
        original_history = history_file.read_text()

    try:
        # Start with empty history
        if history_file.exists():
            history_file.unlink()

        session_name = f"test-history-save-{os.getpid()}"
        socket = get_test_tmux_socket(session_name)

        try:
            # Start rgi with a unique query
            subprocess.run(
                tmux_cmd(
                    socket,
                    "new-session",
                    "-d",
                    "-s",
                    session_name,
                    "-c",
                    test_fixture_dir,
                    f"{rgi_path} --rgi-command-mode TODO .",
                ),
                check=True,
                timeout=5,
            )
            time.sleep(1.5)

            # Press Enter to select a result (this should save to history)
            subprocess.run(
                tmux_cmd(socket, "send-keys", "-t", session_name, "Enter"),
                check=True,
            )
            time.sleep(1.0)

            # Press Escape to exit the editor (vim/nvim)
            subprocess.run(
                tmux_cmd(socket, "send-keys", "-t", session_name, "Escape", ":q!", "Enter"),
                check=True,
            )
            time.sleep(0.5)

        finally:
            subprocess.run(
                tmux_cmd(socket, "kill-session", "-t", session_name),
                capture_output=True,
                timeout=5,
            )
            subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)

        # Check that history file now contains the query
        assert history_file.exists(), "History file should exist after pressing Enter"
        history_content = history_file.read_text()
        assert "rg TODO ." in history_content, (
            f"Expected 'rg TODO .' in history file, got:\n{history_content}"
        )

    finally:
        # Restore original history
        if original_history is not None:
            history_file.write_text(original_history)
        elif history_file.exists():
            history_file.unlink()


def test_incremental_typing_with_explicit_path(test_fixture_dir, rgi_path):
    """Test: rgi always shows explicit path (. for current dir).

    rgi command format: rg <options+pattern> PATH
    Path is always explicit and always last. User types pattern before the path.
    """
    import subprocess

    session_name = f"test-incremental-explicit-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi with NO pattern - should show 'rg .' with explicit current dir
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-command-mode",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.0)

        # Clear line and type 'rg TODO .' (explicit path)
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "C-u"),
            check=True,
        )
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "rg TODO ."),
            check=True,
        )
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Should find TODO matches in current directory
        assert "TODO" in output and (
            "test_runner.py" in output
            or "lib_prompt.sh" in output
            or "app.js" in output
            or "README.md" in output
        ), f"Expected to find TODO results with explicit '.' path, got:\n{output}"

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_cursor_position_with_glob_matching_pattern(test_fixture_dir, rgi_path):
    """Test: Cursor should be before '.' even when pattern matches paths via glob.

    Bug: When starting with a pattern like 'sr' that glob-matches 'src/',
    the cursor was ending up after the '.' instead of before it.
    """
    import subprocess

    session_name = f"test-cursor-glob-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi with pattern 'sr' which glob-matches 'src/'
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-command-mode sr",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Type 'c' - if cursor is correctly positioned before ' .',
        # the query should become 'rg src .' not 'rg sr .c'
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "c"),
            check=True,
        )
        time.sleep(0.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # The query line should show 'rg src .' (c inserted before space-dot)
        # NOT 'rg sr .c' (c appended after dot)
        assert "rg src ." in output or "rg src" in output, (
            f"Expected cursor to be before '.' so typing 'c' gives 'rg src .', got:\n{output}"
        )
        assert ".c" not in output, (
            f"Cursor was after '.', typing 'c' gave '.c' instead of 'src', got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_path_prefix_matching_directory(test_fixture_dir, rgi_path):
    """Test: Path prefix matching works for directory names without slashes.

    If user types 'rg TODO sr', it should match 'src/' directory.
    The last word is always the path, so it gets glob-expanded.
    """
    import subprocess

    session_name = f"test-path-prefix-dir-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi with partial directory name 'sr' (should match 'src/')
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                f"{rgi_path} --rgi-command-mode TODO sr",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Should find results from src/ even though we only typed 'sr'
        assert "test_runner.py" in output or "app.js" in output, (
            f"Expected files from 'src/' to match path prefix 'sr', got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_path_prefix_matching(test_fixture_dir, rgi_path):
    """Test: Path prefix matching - partial paths should match with implicit wildcard.

    If user types 'rg TODO src/te', it should match files in 'src/test_runner.py'
    as if they had typed 'rg TODO src/te*'.
    """
    import subprocess

    session_name = f"test-path-prefix-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi with a PARTIAL path 'src/te' (should match 'src/test_runner.py')
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
                # Note: 'src/te' is a prefix of 'src/test_runner.py'
                f"{rgi_path} --rgi-command-mode TODO src/te",
            ),
            check=True,
            timeout=5,
        )
        time.sleep(1.5)

        # Capture output
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # Should find results from src/test_runner.py even though we only typed 'src/te'
        assert "test_runner.py" in output, (
            f"Expected 'test_runner.py' to match path prefix 'src/te', got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


@pytest.mark.xfail(reason="Known issue: patterns with spaces not working on initial launch")
@pytest.mark.parametrize("mode", ["pattern", "command"])
def test_patterns_with_spaces(test_fixture_dir, rgi_path, mode):
    """Test 16: Patterns with spaces work correctly in both modes.

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

    # Run rgi with the pattern in the specified mode
    if mode == "pattern":
        command = f"{rgi_path} --rgi-pattern-mode '{pattern}' {test_dir}"
    else:  # command mode
        command = f"{rgi_path} --rgi-command-mode '{pattern}' {test_dir}"
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
