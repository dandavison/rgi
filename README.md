An interactive UI for ripgrep.

## Usage

Enter `rgi`, then use [ripgrep](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html) as usual: search results will update dynamically.


**Keyboard shortcuts**

- **`Enter`**: Open the line in your editor / IDE
- **`Ctrl+\`**: Toggle `rg` options inline for editing vs pinned in footer
- **`Alt+Up/Down`**: Navigate history of past `rgi` searches

<br>

**`rg` usage notes**

Consider using:
- `-g` for on-the-fly file path filtering
- [config file](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html#configuration%20files) for project-specific file path inclusions/exclusions

See `rg --help` or an [rg manpage](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html).


<br>

**`fzf` usage notes**

Use the `FZF_DEFAULT_OPTS` environment variable to set `fzf` options.
Please open an issue if `rgi` is setting `fzf` options that you wish to control yourself.
See the environment variables section of `fzf --man`.

<br>

**Editor configuration**

Set `RGI_EDITOR` to one of the values with built-in support (`vscode`, `cursor`, `idea`, `zed`, `vim`, `emacs`, `pycharm`, `helix`, `wormhole`). Alternatively set it to the absolute path of an executable that accepts two arguments: an absolute file path, and a line number.


## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), [ripgrep](https://github.com/BurntSushi/ripgrep), [fzf](https://github.com/junegunn/fzf), [bat](https://github.com/sharkdp/bat), [delta](https://dandavison.github.io/delta/installation.html) (e.g. on macos `brew install uv ripgrep fzf bat git-delta`).

Then:

```
uv tool install git+https://github.com/dandavison/rgi
export RGI_EDITOR=vscode  # vscode | cursor | idea | zed | vim | emacs | pycharm | helix | wormhole | /path/to/custom-editor
```

<br>

**Update to latest version**

```
uv tool uninstall rgi
uv tool install git+https://github.com/dandavison/rgi
```

