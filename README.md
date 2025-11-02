An interactive UI for ripgrep.

## Installation

```
brew install ripgrep fzf bat git-delta
uv tool install git+https://github.com/dandavison/rgi
export RGI_EDITOR=vscode  # vscode | cursor | idea
```

## Usage

The `rgi` command-line interface is the same as [ripgrep](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html) (`rg`).

### Configuration Files

`rgi` supports ripgrep configuration files via the `RIPGREP_CONFIG_PATH` environment variable. When set, the configuration file arguments are:
- Automatically applied to all searches
- Displayed in the command view so you can see the effective command

Example usage:
```bash
export RIPGREP_CONFIG_PATH=~/.ripgreprc
rgi pattern .
```

See `example-ripgreprc` in this repository for a sample configuration file.

### Keyboard shortcuts

- **Tab**: Switch between pattern mode and command mode
- **Enter**: Open the selected file at the matched line

### Modes

- **Pattern mode**: You edit the `rg` regular expression
- **Command mode**: You edit the full `rg` command
