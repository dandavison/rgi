"""
fzfui - Framework for building fzf-based terminal UIs.

This module mirrors the structure of the standalone fzfui library,
enabling potential future convergence.
"""

from rgi.fzfui.app import Action, App, Config, default_bindings

__all__ = ["App", "Config", "Action", "default_bindings"]
