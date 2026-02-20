"""
Tests to verify that all rgi scripts can be invoked correctly when installed.

These tests simulate the way each script is invoked by the main rgi tool
to ensure they're properly accessible and executable on all platforms.

HOW EACH SCRIPT IS INVOKED WHEN RGI IS INSTALLED PER README:

1. rgi: Main entry point
   - Installed via 'uv tool install' as a console script
   - User invokes: `rgi [options] [pattern] [path]`
   - Python entry point (rgi.cli:main) runs directly

2. rgi-preview: File preview in fzf
   - Invoked by fzf via: `rgi-preview <filepath> <linenumber>`
   - Called automatically when navigating search results
   - rgi.cli:main adds the scripts directory to PATH before invoking fzf

3. rgi-switch-mode: Toggle between pattern/command mode
   - Invoked by fzf when Tab key is pressed
   - Called as: `rgi-switch-mode [pattern|command] <query> [args]`
   - Re-invokes rgi with the opposite mode

4. open-in-editor: Open file in user's editor
   - Invoked by fzf when Enter key is pressed
   - Called as: `open-in-editor <filepath> <linenumber>`
   - Uses $RGI_EDITOR environment variable to determine editor

All helper scripts (rgi-preview, rgi-switch-mode, open-in-editor) are made
available through PATH manipulation by rgi.cli:main.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def get_rgi_scripts_dir():
    """Get the path to the rgi scripts directory."""
    # In the source tree
    scripts_dir = Path(__file__).parent.parent / "src" / "rgi" / "scripts"
    if scripts_dir.exists():
        return scripts_dir

    # When installed as a package
    import rgi

    scripts_dir = Path(rgi.__file__).parent / "scripts"
    if scripts_dir.exists():
        return scripts_dir

    raise RuntimeError("Could not find rgi scripts directory")


@pytest.fixture
def scripts_in_path():
    """Add scripts directory to PATH for testing."""
    scripts_dir = str(get_rgi_scripts_dir())
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{scripts_dir}:{old_path}"
    yield scripts_dir
    os.environ["PATH"] = old_path


def test_rgi_preview_invocation(scripts_in_path, tmp_path):
    """Test: Verify rgi-preview can be invoked as fzf would invoke it.

    When a user installs rgi according to README, the rgi script adds its
    directory to PATH, making rgi-preview available. Fzf then invokes it as:
    rgi-preview <filepath> <linenumber>

    Note: rgi-preview requires 'bat' to be installed. In CI, bat may not be
    available, so we accept exit code 127 (command not found) as valid since
    it proves the script was invoked.
    """
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Test invocation as fzf would do it
    result = subprocess.run(
        ["rgi-preview", str(test_file), "2"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # The script should be invocable, even if bat is not installed
    # Exit code 127 means 'command not found' (bat not installed) - this is OK
    # Exit code 0 means it worked (bat is installed)
    # Any other exit code is an actual error
    if result.returncode == 127:
        # Verify it's specifically bat that's missing
        assert "bat: command not found" in result.stderr, f"Unexpected error: {result.stderr}"
        return

    # If bat is installed, it should work properly
    assert result.returncode == 0, f"rgi-preview failed: {result.stderr}"

    # Should show content around line 2
    assert "Line 2" in result.stdout or "2" in result.stdout, (
        f"Expected line content in preview output, got: {result.stdout}"
    )


def test_rgi_switch_mode_invocation(scripts_in_path):
    """Test: Verify rgi-switch-mode script exists and has correct structure.

    When Tab is pressed, fzf invokes:
    rgi-switch-mode [pattern|command] <query> [additional args]

    Note: We don't actually invoke this script in tests because it:
    - Kills its parent process (expects to be run under fzf)
    - Uses os.execvp to replace itself with rgi
    - Would launch an interactive fzf session

    Instead, we verify the script exists and can be imported/parsed.
    """
    scripts_dir = get_rgi_scripts_dir()
    switch_mode_script = scripts_dir / "rgi-switch-mode"

    assert switch_mode_script.exists(), f"rgi-switch-mode not found at {switch_mode_script}"

    with open(switch_mode_script) as f:
        first_line = f.readline()
        assert first_line.startswith("#!/usr/bin/env python"), (
            "rgi-switch-mode should have Python shebang"
        )

    with open(switch_mode_script) as f:
        code = f.read()
        try:
            compile(code, str(switch_mode_script), "exec")
        except SyntaxError as e:
            pytest.fail(f"rgi-switch-mode has syntax errors: {e}")

    assert "switch_to_pattern_mode" in code
    assert "switch_to_command_mode" in code
    assert "os.execvp" in code


def test_open_in_editor_invocation(scripts_in_path, tmp_path, monkeypatch):
    """Test: Verify open-in-editor can be invoked as fzf would invoke it.

    When Enter is pressed, fzf invokes:
    open-in-editor <filepath> <linenumber>
    """
    test_file = tmp_path / "test.py"
    test_file.write_text("# Line 1\n# Line 2\n# Line 3\n")

    monkeypatch.setenv("RGI_EDITOR", "echo")

    result = subprocess.run(
        ["open-in-editor", str(test_file), "2"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"open-in-editor failed: {result.stderr}"


def test_cli_adds_scripts_to_path():
    """Test: Verify rgi.cli:main adds scripts directory to PATH.

    This is crucial for making the helper scripts available to fzf.
    """
    import rgi.cli

    source = Path(rgi.cli.__file__).read_text()
    assert "scripts" in source
    assert 'os.environ["PATH"]' in source or "os.environ['PATH']" in source


def test_helper_scripts_packaged():
    """Test: Verify helper scripts are packaged correctly for installation."""
    expected_scripts = ["rgi-preview", "rgi-switch-mode", "open-in-editor"]
    scripts_dir = get_rgi_scripts_dir()

    for script_name in expected_scripts:
        script_path = scripts_dir / script_name
        assert script_path.exists(), f"Script {script_name} not found at {script_path}"

        with open(script_path) as f:
            first_line = f.readline()
            assert first_line.startswith("#!"), f"Script {script_name} should have a shebang"


@pytest.mark.parametrize(
    "platform",
    [
        pytest.param(
            "linux", marks=pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
        ),
        pytest.param(
            "darwin", marks=pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
        ),
        pytest.param(
            "win32", marks=pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
        ),
    ],
)
def test_script_invocation_on_platform(scripts_in_path, platform):
    """Test: Platform-specific verification that scripts can be invoked."""
    scripts = ["rgi-preview", "open-in-editor"]

    for script_name in scripts:
        result = subprocess.run(
            [script_name],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if "python" in result.stderr.lower() or "import" in result.stderr.lower():
            assert "ModuleNotFoundError" not in result.stderr, (
                f"{script_name} has import errors: {result.stderr}"
            )
            assert "SyntaxError" not in result.stderr, (
                f"{script_name} has syntax errors: {result.stderr}"
            )


def test_rgi_cli_entry_point():
    """Test: Verify the Python entry point (rgi.cli:main) works correctly."""
    from rgi.cli import main

    assert callable(main), "rgi.cli:main should be callable"

    rgi_path = shutil.which("rgi")
    if rgi_path:
        assert os.path.isfile(rgi_path), f"rgi entry point at {rgi_path} is not a file"
