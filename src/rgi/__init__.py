"""
rgi - Interactive ripgrep with fzf

A tool for interactive searching through files using ripgrep, fzf, bat, and delta.
"""

__version__ = "0.1.0"

from .cli import main

__all__ = ["main"]
