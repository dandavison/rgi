"""
fzf command builder and configuration.

This module provides the framework layer for building fzf commands,
separating the generic fzf interface from rgi-specific application logic.

The design resembles fzfui's App class but is tailored for rgi's "command mode"
paradigm where the query line IS the command being constructed.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Binding:
    """Represents an fzf key binding."""

    key: str
    action: str
    description: str = ""


@dataclass
class FzfConfig:
    """Configuration for fzf invocation."""

    # Core options
    height: str = "100%"
    layout: str = "reverse"
    prompt: str = " "
    info: str = "hidden"
    ansi: bool = True
    disabled: bool = False  # --disabled flag for command mode
    delimiter: str = ""  # -d option

    # Query
    initial_query: str = ""

    # Preview
    preview_command: Optional[str] = None
    preview_window: str = "up,70%,~3,noinfo"

    # History
    history_file: Optional[str] = None

    # Footer (for pinned mode display)
    footer: str = ""

    # Border
    no_border: bool = True

    # Shell
    shell: str = "bash -c"

    # Bindings
    bindings: Dict[str, str] = field(default_factory=dict)

    # Raw extra arguments
    extra_args: List[str] = field(default_factory=list)


class FzfCommandBuilder:
    """
    Builds fzf command arguments from configuration.

    This class provides a declarative way to construct fzf commands,
    similar to fzfui's approach but without the decorator-based API.
    """

    def __init__(self, config: Optional[FzfConfig] = None):
        self.config = config or FzfConfig()
        self._bindings: List[Binding] = []

    def add_binding(self, key: str, action: str, description: str = "") -> "FzfCommandBuilder":
        """Add a key binding.

        Args:
            key: The key combination (e.g., "ctrl-k", "alt-up", "enter")
            action: The fzf action string (e.g., "kill-line", "execute:command {}")
            description: Optional description for documentation

        Returns:
            self for chaining
        """
        self._bindings.append(Binding(key, action, description))
        return self

    def build_args(self) -> List[str]:
        """Build the fzf argument list.

        Returns:
            List of command-line arguments for fzf
        """
        args = ["fzf"]

        # Shell configuration (must come early)
        args.extend(["--with-shell", self.config.shell])

        # Core options
        args.extend(["--height", self.config.height])
        args.extend(["--layout", self.config.layout])
        args.extend(["--prompt", self.config.prompt])
        args.extend(["--info", self.config.info])

        if self.config.ansi:
            args.append("--ansi")

        if self.config.disabled:
            args.append("--disabled")

        if self.config.delimiter:
            args.extend(["-d", self.config.delimiter])

        if self.config.no_border:
            args.append("--no-border")

        # Query
        if self.config.initial_query:
            args.extend(["--query", self.config.initial_query])

        # Preview
        if self.config.preview_command:
            args.extend(["--preview", self.config.preview_command])
            args.extend(["--preview-window", self.config.preview_window])

        # History
        if self.config.history_file:
            args.extend(["--history", self.config.history_file])

        # Footer
        if self.config.footer:
            args.extend(["--footer", self.config.footer])
        else:
            # Explicitly set empty footer if none provided
            args.extend(["--footer", ""])

        # Static bindings from config dict
        for key, action in self.config.bindings.items():
            args.extend(["--bind", f"{key}:{action}"])

        # Dynamic bindings
        for binding in self._bindings:
            args.extend(["--bind", f"{binding.key}:{binding.action}"])

        # Extra args
        args.extend(self.config.extra_args)

        return args

    def build_command_string(self) -> str:
        """Build a shell-escaped command string.

        Returns:
            Shell-escaped fzf command string
        """
        return " ".join(shlex.quote(arg) for arg in self.build_args())


def base_bindings() -> Dict[str, str]:
    """Return the base keybindings common to rgi modes.

    These are ergonomic defaults that can be overridden.
    """
    return {
        "ctrl-k": "kill-line",
        "alt-right": "forward-word",
        "alt-left": "backward-word",
        "alt-up": "prev-history",
        "alt-down": "next-history",
        "ctrl-p": "up",
        "ctrl-n": "down",
    }
