"""
fzf application framework.

This module provides the framework layer for building fzf-based terminal UIs,
separating the generic fzf interface from application-specific logic.

The design mirrors the standalone fzfui library's App class, but is tailored
for rgi's "command mode" paradigm where the query line IS the command.

Naming is kept consistent with fzfui to minimize diff if/when the two converge:
- App: Main class for building fzf commands (cf. fzfui.App)
- Config: Configuration dataclass (cf. fzfui's self._config dict)
- Action: Key binding specification (cf. fzfui.Action)
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Action:
    """Represents an fzf key binding/action.

    In fzfui, Action wraps a Python callback function.
    Here, it represents a raw fzf binding string.
    The naming is kept consistent for future convergence.
    """

    key: str
    action: str
    description: str = ""


@dataclass
class Config:
    """Configuration for fzf invocation.

    This dataclass mirrors fzfui's self._config dict but with
    typed fields for better documentation and IDE support.
    """

    # Core options
    height: str = "100%"
    layout: str = "reverse"
    prompt: str = " "
    info: str = "hidden"
    ansi: bool = True
    disabled: bool = False  # --disabled flag for command/preview mode
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

    # Bindings (key -> action string)
    bindings: Dict[str, str] = field(default_factory=dict)

    # Raw extra fzf arguments
    fzf_options: List[str] = field(default_factory=list)


class App:
    """
    Builds fzf command arguments from configuration.

    This class provides a declarative way to construct fzf commands,
    mirroring fzfui's App class. The main differences:

    - fzfui.App uses decorators (@app.action, @app.preview) to register
      Python callbacks that are invoked via script re-execution
    - This App uses add_action() to register raw fzf binding strings

    The naming and structure are kept consistent to enable future convergence.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the App.

        Args:
            config: Optional Config instance. If not provided, defaults are used.
        """
        self._config = config or Config()
        self._actions: List[Action] = []

    @property
    def config(self) -> Config:
        """Access the configuration."""
        return self._config

    def action(self, key: str, action: str, description: str = "") -> "App":
        """Register a key binding/action.

        This method mirrors fzfui's @app.action decorator but takes
        raw fzf action strings instead of Python callbacks.

        Args:
            key: The key combination (e.g., "ctrl-k", "alt-up", "enter")
            action: The fzf action string (e.g., "kill-line", "execute:cmd {}")
            description: Optional description for documentation

        Returns:
            self for method chaining
        """
        self._actions.append(Action(key, action, description))
        return self

    def build_args(self) -> List[str]:
        """Build the fzf argument list.

        Returns:
            List of command-line arguments for fzf
        """
        args = ["fzf"]
        cfg = self._config

        # Shell configuration (must come early)
        args.extend(["--with-shell", cfg.shell])

        # Core options
        args.extend(["--height", cfg.height])
        args.extend(["--layout", cfg.layout])
        args.extend(["--prompt", cfg.prompt])
        args.extend(["--info", cfg.info])

        if cfg.ansi:
            args.append("--ansi")

        if cfg.disabled:
            args.append("--disabled")

        if cfg.delimiter:
            args.extend(["-d", cfg.delimiter])

        if cfg.no_border:
            args.append("--no-border")

        # Query
        if cfg.initial_query:
            args.extend(["--query", cfg.initial_query])

        # Preview
        if cfg.preview_command:
            args.extend(["--preview", cfg.preview_command])
            args.extend(["--preview-window", cfg.preview_window])

        # History
        if cfg.history_file:
            args.extend(["--history", cfg.history_file])

        # Footer
        if cfg.footer:
            args.extend(["--footer", cfg.footer])
        else:
            # Explicitly set empty footer if none provided
            args.extend(["--footer", ""])

        # Static bindings from config dict
        for key, action in cfg.bindings.items():
            args.extend(["--bind", f"{key}:{action}"])

        # Dynamic actions
        for act in self._actions:
            args.extend(["--bind", f"{act.key}:{act.action}"])

        # Extra fzf options
        args.extend(cfg.fzf_options)

        return args

    def build_command_string(self) -> str:
        """Build a shell-escaped command string.

        Returns:
            Shell-escaped fzf command string
        """
        return " ".join(shlex.quote(arg) for arg in self.build_args())


def default_bindings() -> Dict[str, str]:
    """Return default keybindings common to fzfui apps.

    These ergonomic defaults can be overridden in Config.bindings.
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
