#!/usr/bin/env python3
"""Run type checking and formatting checks."""

import subprocess
import sys


def main():
    """Run ty and ruff checks."""
    print("Running type checker (ty)...")
    ty_result = subprocess.run(["ty", "check"], capture_output=False)

    print("\nChecking code formatting with ruff...")
    ruff_format_result = subprocess.run(
        ["ruff", "format", "--check", "."], capture_output=False
    )

    print("\nChecking code quality with ruff...")
    ruff_check_result = subprocess.run(["ruff", "check", "."], capture_output=False)

    # Exit with non-zero if any check failed
    if (
        ty_result.returncode != 0
        or ruff_format_result.returncode != 0
        or ruff_check_result.returncode != 0
    ):
        sys.exit(1)

    print("\n✅ All checks passed!")


if __name__ == "__main__":
    main()
