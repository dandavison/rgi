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
    return "microsoft" in platform.uname().release.lower()


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


def test_basic_pattern_search(test_fixture_dir, rgi_path):
    """Test 1: Basic pattern search for TODO."""
    # Run rgi with TODO pattern
    command = f"{rgi_path} TODO ."
    output = run_rgi_test(command)

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

    # Check that we found TODO comments in the fixture files
    assert (
        "Implement error handling" in output
        or "Review the test implementation" in output
        or "Add git branch display" in output
        or "Implement parallel test execution" in output
    ), f"Expected to find TODO comments in output, got:\n{output}"


def test_search_specific_directory(test_fixture_dir, rgi_path):
    """Test 2: Search in specific directory."""
    # Run rgi with TODO pattern in shell-config directory
    command = f"{rgi_path} TODO shell-config"
    output = run_rgi_test(command)

    # Check that we find the lib_prompt.sh file
    assert "lib_prompt.sh" in output, f"Expected 'lib_prompt.sh' in output, got:\n{output}"

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

    # Should find TODOs from shell-config but not from other directories
    assert "Add git branch display" in output or "Add color support" in output, (
        f"Expected shell-config TODOs in output, got:\n{output}"
    )


def test_search_multiple_paths(test_fixture_dir, rgi_path):
    """Test 3: Search in multiple paths."""
    # Run rgi with TODO pattern in both shell-config and src directories
    command = f"{rgi_path} TODO shell-config src"
    output = run_rgi_test(command)

    # Check that we find files from both directories
    # Note: with 70% preview window, only ~4 results are visible, so we check
    # for files that appear near the top of results
    assert "lib_prompt.sh" in output, f"Expected 'lib_prompt.sh' in output, got:\n{output}"
    assert "app.js" in output, f"Expected 'app.js' in output, got:\n{output}"

    # Check that TODO appears in the output
    assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"


def test_glob_filter_python_files(test_fixture_dir, rgi_path):
    """Test 4: Search with glob filter for Python files."""
    # Run rgi with glob filter for .py files
    command = f"{rgi_path} -g '*.py' test ."
    output = run_rgi_test(command)

    # Check that we only find Python files
    assert ".py" in output, f"Expected '.py' in output, got:\n{output}"

    # Check that we find test_runner.py
    assert "test_runner.py" in output, f"Expected 'test_runner.py' in output, got:\n{output}"

    # Should NOT find shell or JavaScript files
    assert "lib_prompt.sh" not in output, (
        f"Did not expect 'lib_prompt.sh' in output, got:\n{output}"
    )
    assert "app.js" not in output, f"Did not expect 'app.js' in output, got:\n{output}"


def test_fzf_ui_renders(test_fixture_dir, rgi_path):
    """Test 6: Check if fzf UI loads correctly."""
    # Run rgi and check for UI elements
    command = f"{rgi_path} test ."
    output = run_rgi_test(command)

    # Check for fzf UI separator lines (these appear in the output)
    assert "─────" in output or "━━━" in output or "──" in output, (
        f"Expected UI separator lines in output, got:\n{output}"
    )


def test_preview_window_displays(test_fixture_dir, rgi_path):
    """Test 7: Check preview window displays."""
    # Run rgi with function pattern in src directory
    command = f"{rgi_path} function src"
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
                    f"{rgi_path} TODO .",
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
                    f"{rgi_path} TODO .",
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
                f"{rgi_path} sr",
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
                f"{rgi_path} TODO sr",
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
                f"{rgi_path} TODO src/te",
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

    # Run rgi with the pattern
    command = f"{rgi_path} '{pattern}' {test_dir}"
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


# --- Tests for inline/pinned toggle feature ---


def _load_toggle_module():
    """Load the rgi-toggle-pinned module for testing.

    The script doesn't have a .py extension, so we use exec to load it.
    """
    from types import ModuleType

    script_path = Path(__file__).parent.parent / "src" / "rgi" / "scripts" / "rgi-toggle-pinned"
    module_code = script_path.read_text()

    # Create a module namespace and exec the script into it
    toggle_module = ModuleType("rgi_toggle_pinned")
    exec(compile(module_code, script_path, "exec"), toggle_module.__dict__)
    return toggle_module


def test_toggle_inject_to_inline():
    """Test: inject_to_inline moves header options into query."""
    toggle_module = _load_toggle_module()

    # Test: pinned -> inline (inject header into query)
    new_header, new_query = toggle_module.inject_to_inline("--smart-case --hidden", "rg test .")
    assert new_header == ""
    assert new_query == "rg --smart-case --hidden test ."


def test_toggle_eject_to_pinned():
    """Test: eject_to_pinned extracts options from query to header."""
    toggle_module = _load_toggle_module()

    # Test: inline -> pinned (extract options from query)
    new_header, new_query = toggle_module.eject_to_pinned("rg --smart-case --hidden test .")
    assert new_header == "--smart-case --hidden"
    assert new_query == "rg test ."


def test_toggle_eject_with_glob_option():
    """Test: eject_to_pinned handles options with values like -g '*.py'."""
    toggle_module = _load_toggle_module()

    # Test with glob option
    new_header, new_query = toggle_module.eject_to_pinned("rg --smart-case -g '*.py' test src/")
    assert "--smart-case" in new_header
    assert "-g" in new_header
    assert new_query == "rg test src/"


def test_toggle_roundtrip():
    """Test: inject then eject returns to original state."""
    toggle_module = _load_toggle_module()

    # Start in pinned mode
    original_header = "--smart-case --hidden"
    original_query = "rg test ."

    # Inject (pinned -> inline)
    _, inline_query = toggle_module.inject_to_inline(original_header, original_query)
    assert inline_query == "rg --smart-case --hidden test ."

    # Eject (inline -> pinned)
    new_header, new_query = toggle_module.eject_to_pinned(inline_query)
    assert new_header == "--smart-case --hidden"
    assert new_query == "rg test ."


def test_pinned_mode_startup_with_config(test_fixture_dir, rgi_path):
    """Test: rgi starts in pinned mode when RIPGREP_CONFIG_PATH is set.

    This test verifies BOTH:
    1. Header shows the config options
    2. The options are actually APPLIED to the search (not just displayed)
    """
    import subprocess

    # Create test files - one visible, one that should be excluded by glob
    visible_file = Path(test_fixture_dir) / "visible.py"
    visible_file.write_text("# CONFIGTEST marker in visible file\n")

    excluded_file = Path(test_fixture_dir) / "excluded.secret"
    excluded_file.write_text("# CONFIGTEST marker in excluded file\n")

    # Create a config file that excludes *.secret files
    config_file = Path(test_fixture_dir) / ".ripgreprc"
    config_file.write_text("-g '!*.secret'\n")

    session_name = f"test-pinned-startup-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
            ),
            check=True,
            timeout=5,
        )

        # Start rgi with config
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH={config_file} {rgi_path} CONFIGTEST .",
                "Enter",
            ),
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

        # 1. Header should show the config options
        assert "!*.secret" in output, (
            f"Expected exclusion glob in header (pinned mode), got:\n{output}"
        )

        # 2. The visible file SHOULD appear in results
        assert "visible.py" in output, f"Expected 'visible.py' in results, got:\n{output}"

        # 3. The excluded file should NOT appear - this verifies options are APPLIED
        assert "excluded.secret" not in output, (
            f"'excluded.secret' should be excluded by config glob, got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_inline_mode_startup_without_config(test_fixture_dir, rgi_path):
    """Test: rgi starts in inline mode when RIPGREP_CONFIG_PATH is not set."""
    import subprocess

    session_name = f"test-inline-startup-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi without config file
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
            ),
            check=True,
            timeout=5,
        )

        # Explicitly unset RIPGREP_CONFIG_PATH and run rgi
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH= {rgi_path} TODO .",
                "Enter",
            ),
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

        # Should find TODO results (inline mode works)
        assert "TODO" in output, f"Expected 'TODO' in output, got:\n{output}"

        # Query should show 'rg TODO .'
        assert "rg TODO ." in output or "rg TODO" in output, (
            f"Expected query line with 'rg TODO', got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_glob_expand_respects_exclusion_patterns(test_fixture_dir, rgi_path):
    """Test: Glob expansion should not defeat -g exclusion patterns.

    Bug: When user types partial path like 'code', rgi expands to 'code.py code.test'.
    These become explicit file args to rg, and -g '!*.test' exclusions don't apply
    to explicit files - only to files discovered through directory traversal.

    The fix: glob_expand should filter results against exclusion patterns, OR
    prefer directory expansion over file expansion when exclusions are present.
    """
    import subprocess

    # Create files with a common prefix
    code_py = Path(test_fixture_dir) / "code.py"
    code_py.write_text("# PREFIXMARK in included\n")

    code_test = Path(test_fixture_dir) / "code.test"
    code_test.write_text("# PREFIXMARK in excluded\n")

    # Create config that excludes *.test files
    config_file = Path(test_fixture_dir) / ".ripgreprc"
    config_file.write_text("-g '!*.test'\n")

    session_name = f"test-glob-excl-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        subprocess.run(
            tmux_cmd(socket, "new-session", "-d", "-s", session_name, "-c", test_fixture_dir),
            check=True,
            timeout=5,
        )

        # Run rgi with partial path 'code' which will glob-expand to 'code.py code.test'
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH={config_file} {rgi_path} PREFIXMARK code",
                "Enter",
            ),
            check=True,
        )
        time.sleep(1.5)

        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout

        # The included file SHOULD appear
        assert "code.py" in output, f"Expected 'code.py' in results, got:\n{output}"

        # The excluded file should NOT appear - glob_expand should respect exclusions
        assert "code.test" not in output, (
            f"'code.test' should be excluded even with glob expansion, got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_pinned_options_applied_after_query_change(test_fixture_dir, rgi_path):
    """Test: Pinned options are applied AFTER changing the query.

    This is the key test: the 'change' event uses transform to read state,
    and must apply pinned options. The bug is that initial load (start event)
    works, but subsequent changes don't apply pinned options.
    """
    import subprocess

    # Create test files - one that should be included, one excluded
    include_file = Path(test_fixture_dir) / "code.py"
    include_file.write_text("# UNIQUEMARK marker in included file\n")

    exclude_file = Path(test_fixture_dir) / "code.test"
    exclude_file.write_text("# UNIQUEMARK marker in excluded file\n")

    # Create config that excludes *.test files
    config_file = Path(test_fixture_dir) / ".ripgreprc"
    config_file.write_text("-g '!*.test'\n")

    session_name = f"test-pinned-change-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
            ),
            check=True,
            timeout=5,
        )

        # Start rgi with NO pattern - just the config
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH={config_file} {rgi_path}",
                "Enter",
            ),
            check=True,
        )
        time.sleep(1.0)

        # Now TYPE a pattern to trigger change event
        # The query should be "rg  ." initially, type "UNIQUEMARK" before the space-dot
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "UNIQUEMARK"),
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

        # The included file SHOULD appear
        assert "code.py" in output, (
            f"Expected 'code.py' in results after typing pattern, got:\n{output}"
        )

        # The excluded file should NOT appear - this tests the change event applies pinned opts
        assert "code.test" not in output, (
            f"'code.test' should be excluded by pinned glob after query change, got:\n{output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_inline_mode_glob_expand_respects_exclusions(test_fixture_dir, rgi_path):
    """Test: glob expansion respects exclusions from query line in inline mode.

    Bug: When toggling from pinned to inline mode (Ctrl-]), the exclusion options
    move from the header to the query line. But glob_expand was only checking
    pinned_opts (now empty), not the query line. This caused excluded files
    to appear in results after the toggle.
    """
    import subprocess

    # Create test files
    code_py = Path(test_fixture_dir) / "code.py"
    code_test = Path(test_fixture_dir) / "code.test"
    code_py.write_text("# INLINEMARK\n")
    code_test.write_text("# INLINEMARK\n")

    # Create a config with exclusion pattern
    config_file = Path(test_fixture_dir) / ".ripgreprc"
    config_file.write_text("-g '!*.test'\n")

    session_name = f"test-inline-glob-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
            ),
            check=True,
            timeout=5,
        )

        # Start rgi with partial path 'code' in pinned mode
        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH={config_file} {rgi_path} INLINEMARK code",
                "Enter",
            ),
            check=True,
        )
        time.sleep(1.5)

        # Verify we're in pinned mode and code.test is NOT in results
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        pinned_output = result.stdout

        # Sanity check: pinned mode should work (this was already fixed)
        assert "code.py" in pinned_output, (
            f"Expected code.py in pinned mode results, got:\n{pinned_output}"
        )

        # Press ctrl-] to toggle to inline mode
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "C-]"),
            check=True,
        )
        time.sleep(1.0)

        # Capture output after toggle
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        inline_output = result.stdout

        # The query line should now contain the exclusion pattern
        assert "-g '!*.test'" in inline_output, (
            f"Expected exclusion pattern in query after toggle, got:\n{inline_output}"
        )

        # BUG TEST: code.test should NOT appear in results even after toggle
        # The glob expansion should respect exclusions from the query line
        result_lines = [
            line
            for line in inline_output.split("\n")
            if "code.test:" in line and "INLINEMARK" in line
        ]
        assert len(result_lines) == 0, (
            f"BUG: code.test should be excluded even in inline mode, "
            f"but found in results:\n{inline_output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)


def test_ctrl_bracket_toggles_mode(test_fixture_dir, rgi_path):
    """Test: ctrl-] toggles between inline and pinned modes."""
    import subprocess

    # Create a config file
    config_file = Path(test_fixture_dir) / ".ripgreprc"
    config_file.write_text("--smart-case\n")

    session_name = f"test-toggle-{os.getpid()}"
    socket = get_test_tmux_socket(session_name)

    try:
        # Start rgi in pinned mode (with config)
        subprocess.run(
            tmux_cmd(
                socket,
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                test_fixture_dir,
            ),
            check=True,
            timeout=5,
        )

        subprocess.run(
            tmux_cmd(
                socket,
                "send-keys",
                "-t",
                session_name,
                f"RIPGREP_CONFIG_PATH={config_file} {rgi_path} TODO .",
                "Enter",
            ),
            check=True,
        )
        time.sleep(1.5)

        # Verify we're in pinned mode (header shows config)
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        initial_output = result.stdout
        assert "--smart-case" in initial_output, (
            f"Expected '--smart-case' in header initially, got:\n{initial_output}"
        )

        # Press ctrl-] to toggle to inline mode
        subprocess.run(
            tmux_cmd(socket, "send-keys", "-t", session_name, "C-]"),
            check=True,
        )
        time.sleep(1.0)

        # Capture output after toggle
        result = subprocess.run(
            tmux_cmd(socket, "capture-pane", "-t", session_name, "-p"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        toggled_output = result.stdout

        # After toggle to inline: query should contain --smart-case
        # The header line should now be empty or gone
        # IMPORTANT: Check that the raw action string is NOT displayed
        # (this was a false positive before - the broken output showed "+change-query:rg --smart-case..."
        # which matched the substring check even though the feature wasn't working)
        assert "+change-query" not in toggled_output, (
            f"Raw fzf action should not be displayed in output, got:\n{toggled_output}"
        )
        assert "rg --smart-case" in toggled_output, (
            f"Expected '--smart-case' in query after toggle to inline, got:\n{toggled_output}"
        )

    finally:
        subprocess.run(
            tmux_cmd(socket, "kill-session", "-t", session_name),
            capture_output=True,
            timeout=5,
        )
        subprocess.run(tmux_cmd(socket, "kill-server"), capture_output=True, timeout=5)
