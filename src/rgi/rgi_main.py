#!/usr/bin/env python3
"""
Main implementation of rgi - Interactive ripgrep with fzf.

Clean architecture: Python manages fzf sessions and handles all searches.
No shell scripts needed!
"""

import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import typer

app = typer.Typer(add_completion=False)


@dataclass
class FzfResult:
    """Result from an fzf session."""

    key: str  # The key that was pressed (tab, enter, esc, etc.)
    query: str  # The current query string
    selection: Optional[str] = None  # The selected item (if any)

    @property
    def file_path(self) -> Optional[str]:
        """Extract file path from selection."""
        if not self.selection:
            return None
        # Format is "filename:line: content"
        parts = self.selection.split(":", 2)
        return parts[0] if parts else None

    @property
    def line_number(self) -> Optional[int]:
        """Extract line number from selection."""
        if not self.selection:
            return None
        parts = self.selection.split(":", 2)
        try:
            return int(parts[1]) if len(parts) > 1 else None
        except ValueError:
            return None


class RgiSession:
    """Manages the interactive rgi session."""

    def __init__(
        self,
        initial_pattern: str = "",
        initial_paths: List[str] = None,
        initial_options: List[str] = None,
    ):
        self.pattern = initial_pattern
        self.paths = initial_paths or ["."]
        self.options = initial_options or []
        self.mode = "pattern"  # "pattern" or "command"

        # Get the path to the Python script for callbacks
        self.script_path = sys.argv[0]
        if not Path(self.script_path).is_absolute():
            self.script_path = str(Path.cwd() / self.script_path)

        # Find the rgi-preview script
        self.rgi_preview = self._find_rgi_preview()

    def _find_rgi_preview(self) -> Path:
        """Find the rgi-preview script."""
        module_dir = Path(__file__).parent
        scripts_dir = module_dir / "scripts"

        if scripts_dir.exists():
            preview = scripts_dir / "rgi-preview"
            if preview.exists():
                return preview

        # Check in module directory itself
        preview = module_dir / "rgi-preview"
        if preview.exists():
            return preview

        # Fall back to system PATH
        result = subprocess.run(
            ["which", "rgi-preview"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())

        # If not found, we'll error later when trying to use it
        return Path("rgi-preview")

    def run(self) -> int:
        """Run the main interactive loop."""
        while True:
            if self.mode == "pattern":
                result = self._run_pattern_mode()
            else:
                result = self._run_command_mode()

            if not result:
                # Error or empty result
                return 1

            if result.key == "ctrl-c" or result.key == "esc":
                # User wants to exit
                return 0

            elif result.key == "enter" or result.key == "":
                # User selected a file (empty key means default enter)
                if result.selection and result.file_path and result.line_number:
                    self._open_file(result.file_path, result.line_number)
                    return 0
                elif not result.selection:
                    # No selection, just exit
                    return 0

            elif result.key == "tab":
                # Switch modes
                if self.mode == "pattern":
                    # Save the current query as pattern and switch to command mode
                    if result.query:
                        self.pattern = result.query
                    self.mode = "command"
                else:
                    # Parse the command and switch back to pattern mode
                    command = result.query
                    new_pattern, new_options, new_paths = self._parse_command(command)

                    # Update state
                    if new_pattern:
                        self.pattern = new_pattern
                    if new_options:
                        self.options = new_options
                    if new_paths:
                        self.paths = new_paths

                    self.mode = "pattern"

            else:
                # Unexpected key
                print(f"Unexpected key: {result.key}", file=sys.stderr)
                return 1

    def _run_pattern_mode(self) -> Optional[FzfResult]:
        """Run fzf in pattern mode."""
        # Build the reload command - it will call back to this script
        python_exe = sys.executable
        reload_cmd = f'{python_exe} "{self.script_path}" --internal-search {{q}} {" ".join(shlex.quote(p) for p in self.paths)} -- {" ".join(shlex.quote(o) for o in self.options)}'

        # Build the header
        rg_base = self._build_rg_command()
        paths_str = " ".join(self.paths)
        header = f"Pattern Mode | {rg_base} {{q}} {paths_str}"

        # Build fzf command
        cmd = [
            "fzf",
            "--layout",
            "reverse",
            "--info",
            "hidden",
            "--prompt",
            " ",
            "--color",
            "light",
            "--ansi",
            "--delimiter",
            ":",
            "--expect",
            "tab,enter,esc,ctrl-c",
            "--print-query",
            "--query",
            self.pattern,
            "--phony",  # Don't filter, we provide the data
            "--bind",
            f"change:reload:{reload_cmd}",
            "--bind",
            f"start:reload:{reload_cmd}",
            "--header",
            header,
            "--preview",
            f'[[ -n {{1}} ]] && "{self.rgi_preview}" {{1}} {{2}}',
            "--preview-window",
            "up,70%",
        ]

        # Run fzf
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input="",  # Start with empty input, will be populated by reload
        )

        return self._parse_fzf_output(result.stdout)

    def _run_command_mode(self) -> Optional[FzfResult]:
        """Run fzf in command mode."""
        # Build the initial command
        rg_base = self._build_rg_command()
        paths_str = " ".join(shlex.quote(p) for p in self.paths)
        pattern_quoted = shlex.quote(self.pattern) if self.pattern else '""'
        initial_command = f"{rg_base} --json {pattern_quoted} {paths_str}"

        # Build the reload command - evaluate the command in {q}
        reload_cmd = "eval {q} 2>/dev/null | delta --light --grep-output-type classic"

        # Build fzf command
        cmd = [
            "fzf",
            "--layout",
            "reverse",
            "--info",
            "hidden",
            "--prompt",
            " ",
            "--color",
            "light",
            "--ansi",
            "--delimiter",
            ":",
            "--expect",
            "tab,enter,esc,ctrl-c",
            "--print-query",
            "--query",
            initial_command,
            "--phony",
            "--bind",
            f"change:reload:{reload_cmd}",
            "--bind",
            f"start:reload:{reload_cmd}",
            "--header",
            "Command Mode | Edit the rg command directly",
            "--preview",
            f'[[ -n {{1}} ]] && "{self.rgi_preview}" {{1}} {{2}}',
            "--preview-window",
            "up,70%",
        ]

        # Run fzf
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input="",
        )

        return self._parse_fzf_output(result.stdout)

    def _build_rg_command(self) -> str:
        """Build the base rg command with options."""
        base = "rg --follow -i --hidden -g '!.git/*'"
        if self.options:
            opts = " ".join(shlex.quote(opt) for opt in self.options)
            base += f" {opts}"
        base += " --color=always"
        return base

    def _parse_fzf_output(self, output: str) -> Optional[FzfResult]:
        """Parse the output from fzf --expect --print-query."""
        lines = output.strip().split("\n")

        if len(lines) < 2:
            return None

        # First line is the key pressed (from --expect)
        key = lines[0].strip()

        # Second line is the query
        query = lines[1] if len(lines) > 1 else ""

        # Third line is the selection (if any)
        selection = lines[2] if len(lines) > 2 else None

        return FzfResult(key=key, query=query, selection=selection)

    def _parse_command(self, command: str) -> Tuple[str, List[str], List[str]]:
        """Parse an rg command to extract pattern, options, and paths."""
        cmd = command.strip()

        # Find the pattern after --json
        pattern = ""
        pattern_match = re.search(r"--json\s+(\S+)", cmd)
        if pattern_match:
            pattern_raw = pattern_match.group(1)
            # Remove quotes if present
            if pattern_raw.startswith('"') and pattern_raw.endswith('"'):
                pattern = pattern_raw[1:-1]
            elif pattern_raw.startswith("'") and pattern_raw.endswith("'"):
                pattern = pattern_raw[1:-1]
            else:
                pattern = pattern_raw

        # Extract options (everything that starts with -)
        # Skip default options
        options = []
        paths = []

        # Remove the rg command and defaults
        cmd_clean = re.sub(r"^rg\s+", "", cmd)
        cmd_clean = re.sub(r"--follow\s*", "", cmd_clean)
        cmd_clean = re.sub(r"-i\s*", "", cmd_clean)
        cmd_clean = re.sub(r"--hidden\s*", "", cmd_clean)
        cmd_clean = re.sub(r"--color=always\s*", "", cmd_clean)
        cmd_clean = re.sub(r"-g\s+'!\.git/\*'\s*", "", cmd_clean)
        cmd_clean = re.sub(
            r"--json\s+\S+\s*", "", cmd_clean
        )  # Remove --json and pattern

        # Parse what's left
        try:
            tokens = shlex.split(cmd_clean)
        except ValueError:
            tokens = cmd_clean.split()

        i = 0
        while i < len(tokens):
            if tokens[i].startswith("-"):
                options.append(tokens[i])
                # Check if this option needs an argument
                if tokens[i] in [
                    "-g",
                    "--glob",
                    "-t",
                    "--type",
                    "-e",
                    "--regexp",
                ] and i + 1 < len(tokens):
                    i += 1
                    options.append(tokens[i])
            else:
                paths.append(tokens[i])
            i += 1

        return pattern, options, paths

    def _open_file(self, file_path: str, line_number: int):
        """Open a file at the specified line using wormhole or $EDITOR."""
        # Try wormhole first
        try:
            subprocess.run(["wormhole", f"{file_path}:{line_number}"], check=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fall back to $EDITOR
        editor = os.environ.get("EDITOR", "vi")
        try:
            # Most editors support +LINE syntax
            subprocess.run([editor, f"+{line_number}", file_path])
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Just open the file
            subprocess.run([editor, file_path])


def internal_search(pattern: str, paths: List[str], options: List[str]):
    """Execute an rg search and output results formatted for fzf."""
    # Build the rg command
    cmd_parts = ["rg", "--follow", "-i", "--hidden", "-g", "!.git/*"]
    cmd_parts.extend(options)
    cmd_parts.extend(["--json", pattern])
    cmd_parts.extend(paths)

    # Run rg and pipe to delta
    rg_proc = subprocess.Popen(
        cmd_parts,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    delta_proc = subprocess.Popen(
        ["delta", "--light", "--grep-output-type", "classic"],
        stdin=rg_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    rg_proc.stdout.close()
    output, _ = delta_proc.communicate()

    # Output the results
    print(output, end="")


@app.command()
def main(
    pattern: Optional[str] = typer.Argument(None, help="Search pattern"),
    paths: List[str] = typer.Argument(None, help="Paths to search"),
    glob: Optional[List[str]] = typer.Option(
        None, "-g", "--glob", help="Include/exclude globs"
    ),
    type_filter: Optional[List[str]] = typer.Option(
        None, "-t", "--type", help="Filter by file type"
    ),
    regexp: Optional[List[str]] = typer.Option(
        None, "-e", "--regexp", help="Regular expression patterns"
    ),
    real_code_only: bool = typer.Option(
        False, "--real-code-only", help="Search only in real code"
    ),
    internal_search_flag: Optional[str] = typer.Option(
        None,
        "--internal-search",
        help="Internal search mode for fzf callback",
        hidden=True,
    ),
):
    """
    Interactive ripgrep with fzf.

    Search through files interactively using ripgrep, fzf, bat, and delta.

    Examples:
        rgi TODO                    # Search for "TODO" in current directory
        rgi "fn main" src/          # Search for "fn main" in src directory
        rgi -t py "import" .        # Search Python files for "import"
        rgi -g '!*.html' test .     # Search for "test" excluding HTML files
    """

    # Handle internal search mode
    if internal_search_flag is not None:
        # Parse the remaining args after --internal-search
        # Format: --internal-search PATTERN PATH1 PATH2 ... -- OPTION1 OPTION2 ...
        search_pattern = internal_search_flag
        search_paths = []
        search_options = []

        # Collect paths until we hit "--" or run out of args
        in_options = False
        for arg in paths or []:
            if arg == "--":
                in_options = True
            elif in_options:
                search_options.append(arg)
            else:
                search_paths.append(arg)

        # Add any options from the main command
        if glob:
            for g in glob:
                search_options.extend(["-g", g])
        if type_filter:
            for t in type_filter:
                search_options.extend(["-t", t])
        if regexp:
            for r in regexp:
                search_options.extend(["-e", r])

        if not search_paths:
            search_paths = ["."]

        internal_search(search_pattern, search_paths, search_options)
        sys.exit(0)

    # Build options list for normal mode
    options = []
    if glob:
        for g in glob:
            options.extend(["-g", g])
    if type_filter:
        for t in type_filter:
            options.extend(["-t", t])
    if regexp:
        for r in regexp:
            options.extend(["-e", r])
    if real_code_only:
        options.append("--real-code-only")

    # Create and run session
    session = RgiSession(
        initial_pattern=pattern or "",
        initial_paths=paths if paths else None,
        initial_options=options,
    )

    sys.exit(session.run())


if __name__ == "__main__":
    app()
