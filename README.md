An interactive UI for ripgrep.

## Installation

```
brew install ripgrep fzf bat git-delta
uv tool install git+https://github.com/dandavison/rgi
export RGI_EDITOR=vscode  # vscode | cursor | idea
```

**Update to latest version**

```
uv tool uninstall rgi
uv tool install git+https://github.com/dandavison/rgi
```

## Usage

Enter [ripgrep](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html) commands as usual, but use `rgi` instead of `rg`.

**Keyboard shortcuts**


- **Enter**: Open the selected file at the matched line in your editor / IDE
- **Tab**: Toggle between editing the full `rg` command vs editing just the search regex
