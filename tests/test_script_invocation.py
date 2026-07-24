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


def test_open_in_editor_arg_overrides_env(scripts_in_path, tmp_path, monkeypatch):
    """Test: a 3rd arg selects the editor, overriding RGI_EDITOR.

    This is how the alternate-editor key (ctrl-o) opens a result in a second
    editor without disturbing the Enter default.
    """
    test_file = tmp_path / "test.py"
    test_file.write_text("# Line 1\n# Line 2\n")

    monkeypatch.setenv("RGI_EDITOR", "no-such-editor-xyz")

    result = subprocess.run(
        ["open-in-editor", str(test_file), "2", "echo"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"3rd-arg editor override ignored: {result.stderr}"


def test_abbrev_home_filter(scripts_in_path, monkeypatch):
    """Test: rgi-abbrev-home replaces $HOME with ~ in the visible path but leaves
    OSC8 hyperlink targets (the click-to-open URL) absolute."""
    monkeypatch.setenv("HOME", "/Users/dan")
    esc = "\x1b"
    url = f"{esc}]8;;http://wormhole:7117/file//Users/dan/p/f.md:9?land-in=editor{esc}\\"
    visible = f"{esc}[31m/Users/dan/p/f.md{esc}[0m"
    line = f"{url}{visible}:{esc}[32m9{esc}[0m:hit\n"

    result = subprocess.run(
        ["rgi-abbrev-home"],
        input=line,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"rgi-abbrev-home failed: {result.stderr}"
    out = result.stdout
    assert f"{esc}[31m~/p/f.md{esc}[0m" in out, "visible path not abbreviated"
    assert "file//Users/dan/p/f.md:9?land-in=editor" in out, "hyperlink target was altered"


def test_open_in_editor_expands_tilde(scripts_in_path, monkeypatch):
    """Test: open-in-editor expands a leading ~ (rgi displays paths with ~)."""
    monkeypatch.setenv("RGI_EDITOR", "echo")

    result = subprocess.run(
        ["open-in-editor", "~/some/file.py", "7"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"open-in-editor failed: {result.stderr}"
    home = os.environ["HOME"]
    assert f"{home}/some/file.py" in result.stdout, f"~ not expanded: {result.stdout}"
    assert "~/some/file.py" not in result.stdout, "literal ~ leaked to editor"


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
    expected_scripts = [
        "rgi-preview",
        "rgi-switch-mode",
        "open-in-editor",
        "rgi-copy-command",
        "rgi-abbrev-home",
        "rgi-vscode-open",
    ]
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


def test_copy_command_invocation(scripts_in_path):
    """Test: Verify rgi-copy-command echoes the command and copies it to clipboard.

    Bound to Ctrl-C, fzf invokes: rgi-copy-command <command>
    The command is always echoed to stderr (for terminal scrollback) and copied
    to the clipboard when a clipboard tool is available.
    """
    command = "rg -il 'conflict policy' ."

    result = subprocess.run(
        ["rgi-copy-command", command],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert command in result.stderr, f"Expected command echoed to stderr, got: {result.stderr}"

    has_clipboard = any(shutil.which(tool) for tool in ("pbcopy", "xclip", "xsel", "wl-copy"))
    if has_clipboard:
        assert result.returncode == 0, f"rgi-copy-command failed: {result.stderr}"
    else:
        assert "clipboard" in result.stderr.lower()


def test_ctrl_c_binding_copies_command():
    """Test: Verify Ctrl-C is bound to copy the rg command to the clipboard and exit."""
    from rgi.cli import build_rgi_fzf_command

    args = build_rgi_fzf_command(pattern="", paths=[], rg_opts="", config_args="")
    binding = next(
        (
            args[i + 1]
            for i, a in enumerate(args)
            if a == "--bind" and args[i + 1].startswith("ctrl-c:")
        ),
        None,
    )
    assert binding is not None, "No ctrl-c binding found"
    assert "rgi-copy-command" in binding
    assert "abort" in binding


def test_rgi_cli_entry_point():
    """Test: Verify the Python entry point (rgi.cli:main) works correctly."""
    from rgi.cli import main

    assert callable(main), "rgi.cli:main should be callable"

    rgi_path = shutil.which("rgi")
    if rgi_path:
        assert os.path.isfile(rgi_path), f"rgi entry point at {rgi_path} is not a file"


def test_rgi_vscode_open_posts_json_boolean_focus(scripts_in_path, tmp_path, monkeypatch):
    """Test: rgi-vscode-open POSTs {"file", "line", "focus"} to the RPC server.

    The vscode-etc extension validates the payload strictly: `focus` must be a
    JSON boolean (true/false), not 0/1. This test runs the script against a
    capturing HTTP server exactly as fzf would invoke it.
    """
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            received.append(json.loads(self.rfile.read(length).decode()))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("RGI_VSCODE_PORT", str(server.server_address[1]))

        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\n")

        for focus_arg, expected in [("0", False), ("1", True)]:
            result = subprocess.run(
                ["rgi-vscode-open", str(test_file), "2", focus_arg],
                capture_output=True,
                text=True,
                timeout=5,
            )
            assert result.returncode == 0, f"rgi-vscode-open failed: {result.stderr}"

        assert len(received) == 2
        for payload, expected_focus in zip(received, [False, True]):
            assert payload["file"] == str(test_file)
            assert payload["line"] == 2
            assert payload["focus"] is expected_focus, (
                f"focus must be a JSON boolean, got {payload['focus']!r}"
            )
    finally:
        server.shutdown()
