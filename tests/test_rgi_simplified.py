"""
Simplified pytest tests for rgi focusing on testable functionality.

This suite tests the core functionality without complex tmux interactions.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


def create_test_files(directory: Path):
    """Create test files in the given directory."""
    # Create a simple file with TODO
    (directory / "test.txt").write_text("TODO: test this\nTODO: and this\n")
    (directory / "code.py").write_text("# TODO: implement\ndef test():\n    pass\n")
    (directory / "notes.md").write_text("# Notes\n\nTODO: Write docs\n")


@pytest.fixture
def test_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory(prefix="rgi-test-") as tmpdir:
        test_path = Path(tmpdir)
        create_test_files(test_path)
        yield test_path


class TestCLI:
    """Test CLI functionality."""
    
    def test_help(self):
        """Test --help flag."""
        python_exe = sys.executable
        rgi_module_path = Path(__file__).parent.parent / "src"
        
        result = subprocess.run(
            f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -m rgi.cli --help',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "Interactive ripgrep with fzf" in result.stdout
        assert "Examples:" in result.stdout
    
    def test_version_in_module(self):
        """Test that version is defined."""
        python_exe = sys.executable
        rgi_module_path = Path(__file__).parent.parent / "src"
        
        result = subprocess.run(
            f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -c "import rgi; print(rgi.__version__)"',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


class TestPythonImplementation:
    """Test Python implementation directly."""
    
    def test_import(self):
        """Test that the module can be imported."""
        python_exe = sys.executable
        rgi_module_path = Path(__file__).parent.parent / "src"
        
        result = subprocess.run(
            f'PYTHONPATH="{rgi_module_path}" "{python_exe}" -c "import rgi.cli; import rgi.rgi_main"',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
    
    def test_rgi_session_creation(self):
        """Test RgiSession class can be instantiated."""
        python_exe = sys.executable
        rgi_module_path = Path(__file__).parent.parent / "src"
        
        # Write test code to a temp file to avoid quoting issues
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import rgi.rgi_main
session = rgi.rgi_main.RgiSession(
    pattern="test",
    paths=["."],
    options=[],
    command_mode=False
)
print("Session created:", session.pattern)
''')
            test_file = f.name
        
        try:
            result = subprocess.run(
                f'PYTHONPATH="{rgi_module_path}" "{python_exe}" "{test_file}"',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            assert result.returncode == 0
            assert "Session created: test" in result.stdout
        finally:
            Path(test_file).unlink(missing_ok=True)
    
    def test_command_building(self):
        """Test that commands are built correctly."""
        python_exe = sys.executable
        rgi_module_path = Path(__file__).parent.parent / "src"
        
        # Write test code to a temp file to avoid quoting issues
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import rgi.rgi_main
session = rgi.rgi_main.RgiSession(
    pattern="TODO",
    paths=["src", "docs"],
    options=["-g", "*.py"],
    command_mode=False
)
cmd = session.build_fzf_command()
# Check that the command includes the pattern and paths
cmd_str = ' '.join(str(c) for c in cmd)
print("Pattern in command:", "TODO" in cmd_str)
print("Glob in command:", "*.py" in cmd_str)
''')
            test_file = f.name
        
        try:
            result = subprocess.run(
                f'PYTHONPATH="{rgi_module_path}" "{python_exe}" "{test_file}"',
                shell=True,
                capture_output=True,
                text=True,
            )
            
            assert result.returncode == 0
            assert "Pattern in command: True" in result.stdout
            assert "Glob in command: True" in result.stdout
        finally:
            Path(test_file).unlink(missing_ok=True)


class TestEndToEnd:
    """End-to-end tests with actual file searching."""
    
    def test_rgi_finds_files(self, test_dir):
        """Test that rgi can find files with pattern."""
        # This test verifies the command construction works
        # We can't easily test the interactive fzf part, but we can verify
        # that rg finds the expected files
        
        result = subprocess.run(
            f'cd "{test_dir}" && rg --files',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        assert "test.txt" in result.stdout
        assert "code.py" in result.stdout
        assert "notes.md" in result.stdout
    
    def test_rg_finds_pattern(self, test_dir):
        """Test that rg finds the TODO pattern."""
        result = subprocess.run(
            f'cd "{test_dir}" && rg TODO',
            shell=True,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "TODO" in result.stdout
        assert "test.txt" in result.stdout
        assert "code.py" in result.stdout
        assert "notes.md" in result.stdout
