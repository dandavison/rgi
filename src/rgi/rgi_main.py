#!/usr/bin/env python3
"""
Main implementation of rgi - Interactive ripgrep with fzf.
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import typer

app = typer.Typer(add_completion=False)


def parse_rg_command(command: str) -> Tuple[str, List[str], List[str]]:
    """Parse an rg command to extract pattern, options, and paths.

    Returns:
        (pattern, options, paths) tuple
    """
    cmd = command.strip()
    
    # Extract the pattern by looking for --json followed by the pattern
    # The pattern is the next token after --json
    pattern = ""
    pattern_match = re.search(r'--json\s+(\S+)', cmd)
    if pattern_match:
        pattern_raw = pattern_match.group(1)
        # Try to parse as a shell-quoted string
        try:
            pattern = shlex.split(pattern_raw)[0]
        except (ValueError, IndexError):
            # If shlex fails, just strip outer quotes
            if (pattern_raw.startswith('"') and pattern_raw.endswith('"')) or \
               (pattern_raw.startswith("'") and pattern_raw.endswith("'")):
                pattern = pattern_raw[1:-1]
            else:
                pattern = pattern_raw
    
    # Extract everything before --json as potential options
    before_json = cmd.split('--json')[0] if '--json' in cmd else cmd
    
    # Extract everything after --json <pattern> as potential options/paths
    after_pattern = ""
    if '--json' in cmd and pattern_match:
        # Find where the pattern ends
        pattern_start = pattern_match.start(1)
        pattern_end = pattern_match.end(1)
        after_pattern = cmd[pattern_end:].strip()
    
    # Parse options and paths
    options = []
    paths = []
    
    # Remove "rg" and default options from before_json
    tokens_before = before_json.replace("rg", "", 1).strip()
    # Remove default options
    for default in ["--follow", "-i", "--hidden", "--color=always"]:
        tokens_before = tokens_before.replace(default, "")
    # Remove the default glob pattern in various formats
    tokens_before = re.sub(r"-g\s+'!\.git/\*'", "", tokens_before)
    tokens_before = re.sub(r'-g\s+"!\.git/\*"', "", tokens_before)
    tokens_before = re.sub(r"-g\s+!\.git/\*", "", tokens_before)
    
    # Parse remaining options from before --json
    if tokens_before.strip():
        try:
            parts = shlex.split(tokens_before)
        except ValueError:
            parts = tokens_before.split()
        
        i = 0
        while i < len(parts):
            if parts[i].startswith("-"):
                options.append(parts[i])
                # Check if this option takes an argument
                if parts[i] in ["-g", "--glob", "-t", "--type", "-e", "--regexp"] and i + 1 < len(parts):
                    i += 1
                    options.append(parts[i])
            i += 1
    
    # Parse after_pattern for additional options and paths
    if after_pattern:
        try:
            parts = shlex.split(after_pattern)
        except ValueError:
            parts = after_pattern.split()
        
        i = 0
        while i < len(parts):
            if parts[i].startswith("-"):
                options.append(parts[i])
                # Check if this option takes an argument
                if parts[i] in ["-g", "--glob", "-t", "--type", "-e", "--regexp"] and i + 1 < len(parts):
                    i += 1
                    options.append(parts[i])
            else:
                paths.append(parts[i])
            i += 1
    
    return pattern, options, paths


class RgiSession:
    """Manages an rgi interactive session."""

    def __init__(
        self,
        pattern: str = "",
        paths: List[str] = None,
        options: List[str] = None,
        command_mode: bool = False,
    ):
        self.pattern = pattern or ""
        self.paths = paths or ["."]
        self.options = options or []
        self.command_mode = command_mode
        self.script_path = sys.argv[0]
        self.setup_paths()

    def setup_paths(self):
        """Setup paths to scripts."""
        # Find rgi-preview script
        module_dir = Path(__file__).parent
        scripts_dir = module_dir / "scripts"

        if scripts_dir.exists():
            self.rgi_preview = scripts_dir / "rgi-preview"
        else:
            self.rgi_preview = module_dir / "rgi-preview"

        if not self.rgi_preview.exists():
            # Fall back to looking for it on PATH
            self.rgi_preview = "rgi-preview"

    def build_rg_base(self) -> str:
        """Build the base ripgrep command."""
        opts = " ".join(shlex.quote(opt) for opt in self.options)
        base = "rg --follow -i --hidden -g '!.git/*'"
        if opts:
            base += f" {opts}"
        base += " --color=always"
        return base

    def build_fzf_command(self) -> List[str]:
        """Build the complete fzf command with all bindings."""
        rg_base = self.build_rg_base()
        paths_str = " ".join(shlex.quote(p) for p in self.paths)
        delta = "delta --light --grep-output-type classic"

        # Base fzf command
        fzf_cmd = [
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
            "--bind",
            "ctrl-k:kill-line",
            "--bind",
            "alt-right:forward-word",
            "--bind",
            "alt-left:backward-word",
            "--preview-window",
            "up,70%",
            "-d",
            ":",
        ]

        if self.command_mode:
            # Command mode
            fzf_cmd.extend(self._build_command_mode_bindings(rg_base, paths_str, delta))
        else:
            # Pattern mode
            fzf_cmd.extend(self._build_pattern_mode_bindings(rg_base, paths_str, delta))

        return fzf_cmd

    def _build_command_mode_bindings(
        self, rg_base: str, paths_str: str, delta: str
    ) -> List[str]:
        """Build fzf bindings for command mode."""
        # Initial command to display
        pattern_quoted = shlex.quote(self.pattern) if self.pattern else '""'
        full_command = f"{rg_base} --json {pattern_quoted} {paths_str}"

        # Create the tab binding script for switching to pattern mode
        tab_script = self._create_command_to_pattern_script()

        return [
            "--query",
            full_command + " ",
            "--phony",
            "--bind",
            f"start:reload:{rg_base} --json {pattern_quoted} {paths_str} 2>/dev/null | {delta}",
            "--bind",
            "start:backward-delete-char",
            "--bind",
            f"change:reload:eval {{q}} 2>/dev/null | {delta}",
            "--bind",
            f"tab:execute:{tab_script}",
            "--bind",
            "enter:execute:wormhole {1}:{2}",
            "--preview",
            f'[[ -n {{1}} ]] && "{self.rgi_preview}" {{1}} {{2}}',
        ]

    def _build_pattern_mode_bindings(
        self, rg_base: str, paths_str: str, delta: str
    ) -> List[str]:
        """Build fzf bindings for pattern mode."""
        pattern_quoted = shlex.quote(self.pattern) if self.pattern else '""'

        # Build the options string for passing to command mode
        opts_str = " ".join(shlex.quote(opt) for opt in self.options)

        return [
            "--query",
            self.pattern + " " if self.pattern else "",
            "--phony",
            "--bind",
            f"start:reload:{rg_base} --json {pattern_quoted} {paths_str} 2>/dev/null | {delta}",
            "--bind",
            "start:backward-delete-char" if self.pattern else "start:reload:echo",
            "--bind",
            f"change:reload:{rg_base} --json {{q}} {paths_str} 2>/dev/null | {delta}",
            "--bind",
            f'tab:execute:kill -TERM $PPID 2>/dev/null; "{self.script_path}" --rgi-command-mode {opts_str} {{q}} {paths_str}',
            "--bind",
            "enter:execute:wormhole {1}:{2}",
            "--header",
            f"{rg_base} {{q}} {paths_str}",
            "--preview",
            f'[[ -n {{1}} ]] && "{self.rgi_preview}" {{1}} {{2}}',
        ]

    def _create_command_to_pattern_script(self) -> str:
        """Create the shell script for switching from command to pattern mode."""
        # Use Python to parse the command
        return f'''
            # Get the parsed components from Python
            PARSED=$("{self.script_path}" --rgi-parse-command "{{q}}")
            if [[ $? -ne 0 ]]; then
                echo "Failed to parse command" >&2
                exit 1
            fi
            
            # Read the parsed components (pattern|options|paths)
            IFS='|' read -r PATTERN OPTIONS PATHS <<< "$PARSED"
            
            # If no paths specified, use the original paths
            [[ -z "$PATHS" ]] && PATHS="{" ".join(self.paths)}"
            
            # Kill parent fzf and start new instance with parsed args
            kill -TERM $PPID 2>/dev/null
            "{self.script_path}" $OPTIONS "$PATTERN" $PATHS
        '''.strip()

    def run(self):
        """Run the interactive session."""
        fzf_cmd = self.build_fzf_command()

        try:
            # Use bash to run the command to handle the complex shell scripts in bindings
            # Pipe empty string to fzf to trigger initial display
            env = os.environ.copy()
            process = subprocess.Popen(fzf_cmd, stdin=subprocess.PIPE, env=env)
            # Send empty input to trigger initial display
            process.communicate(input=b"")
            return process.returncode
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(f"Error in fzf: {e}", file=sys.stderr)
            return 1


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
    rgi_command_mode: bool = typer.Option(
        False, "--rgi-command-mode", help="Start in command mode", hidden=True
    ),
    rgi_parse_command: Optional[str] = typer.Option(
        None, "--rgi-parse-command", help="Parse rg command and return components", hidden=True
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
    
    # Handle special parse-command mode
    if rgi_parse_command is not None:
        pattern, options, paths = parse_rg_command(rgi_parse_command)
        # Output in a format the shell script can parse
        print(f"{pattern}|{' '.join(options)}|{' '.join(paths)}")
        sys.exit(0)

    # Build options list
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
        pattern=pattern,
        paths=list(paths) if paths else None,
        options=options,
        command_mode=rgi_command_mode,
    )

    sys.exit(session.run())


if __name__ == "__main__":
    app()
