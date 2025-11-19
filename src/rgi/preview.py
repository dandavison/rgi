#!/usr/bin/env python3
"""Preview file contents for rgi."""

import subprocess
import sys


def main():
    """Preview file with bat."""
    if len(sys.argv) < 3:
        sys.exit(1)

    file = sys.argv[1]
    line = int(sys.argv[2])

    start_line = max(1, line - 10)

    cmd = [
        "bat",
        "--color=always",
        "--style=header,grid",
        f"-H={line}",
        f"-r={start_line}:+70",
        file
    ]

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print(f"Error: 'bat' not found. Please install bat.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
