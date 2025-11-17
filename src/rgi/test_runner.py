"""
Test runner for rgi test suite
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the rgi test suite."""
    # Get the path to the test directory
    project_root = Path(__file__).parent.parent.parent
    test_dir = project_root / "tests"

    # Check for required test files
    run_all = test_dir / "run-all.sh"
    test_interactive = test_dir / "test-interactive"

    if not run_all.exists():
        print(f"Error: Test runner not found at {run_all}", file=sys.stderr)
        sys.exit(1)

    if not test_interactive.exists():
        print(
            f"Error: test-interactive not found at {test_interactive}", file=sys.stderr
        )
        sys.exit(1)

    # Make sure test files are executable
    run_all.chmod(0o755)
    test_interactive.chmod(0o755)

    # Run the test suite
    try:
        print("Running test suite...")
        result = subprocess.run(["bash", str(run_all)], cwd=str(test_dir), check=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
