"""
CLI entry point for rgi
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Main entry point for rgi command."""
    # Get the path to the bundled shell script
    rgi_script = Path(__file__).parent / "scripts" / "rgi"

    if not rgi_script.exists():
        print(f"Error: rgi script not found at {rgi_script}", file=sys.stderr)
        sys.exit(1)

    # Execute the shell script with all arguments passed through
    try:
        result = subprocess.run([str(rgi_script)] + sys.argv[1:], check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(130)  # Standard exit code for Ctrl-C
    except Exception as e:
        print(f"Error running rgi: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
