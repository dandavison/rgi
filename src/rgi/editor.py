#!/usr/bin/env python3
"""Open files in editor for rgi."""

import os
import subprocess
import sys
import platform


def main():
    """Open file in editor at specified line."""
    if len(sys.argv) < 3:
        print("Usage: open-in-editor <file> <line>", file=sys.stderr)
        sys.exit(1)

    file = sys.argv[1]
    line = sys.argv[2]
    editor = os.environ.get("RGI_EDITOR", os.environ.get("EDITOR", "vscode"))

    # Platform-specific handling
    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"
    is_wsl = "microsoft" in platform.uname().release.lower()

    if editor in ["idea", "intellij"]:
        url = f"idea://open?file={file}&line={line}"
        if is_macos:
            subprocess.run(["open", url])
        elif is_windows or is_wsl:
            subprocess.run(["cmd.exe", "/c", "start", url])
        else:
            print(f"Opening {url} not supported on this platform", file=sys.stderr)
            sys.exit(1)

    elif editor in ["vscode", "code"]:
        if is_wsl:
            # Use code.cmd for WSL
            subprocess.run(["code.cmd", f"{file}:{line}"])
        elif is_macos:
            subprocess.run(["open", f"vscode://file/{file}:{line}"])
        elif is_windows:
            subprocess.run(["code", f"{file}:{line}"])
        else:
            subprocess.run(["code", f"{file}:{line}"])

    elif editor == "cursor":
        url = f"cursor://file/{file}:{line}"
        if is_macos:
            subprocess.run(["open", url])
        elif is_windows or is_wsl:
            subprocess.run(["cursor", f"{file}:{line}"])
        else:
            subprocess.run(["cursor", f"{file}:{line}"])

    elif editor == "wormhole":
        subprocess.run(["wormhole", f"{file}:{line}"])

    else:
        # Try to run as a generic editor
        try:
            subprocess.run([editor, f"+{line}", file])
        except FileNotFoundError:
            print(
                f"Error: Unknown editor '{editor}'. Set RGI_EDITOR or EDITOR to one of:\n"
                "idea, vscode, cursor, wormhole, or path to an editor",
                file=sys.stderr
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
