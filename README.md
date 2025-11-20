An interactive UI for ripgrep.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), [ripgrep](https://github.com/BurntSushi/ripgrep), [fzf](https://github.com/junegunn/fzf), [bat](https://github.com/sharkdp/bat), [delta](https://dandavison.github.io/delta/installation.html) (e.g. on MacOS `brew install uv ripgrep fzf bat git-delta`).

Then:

```
uv tool install git+https://github.com/dandavison/rgi
export RGI_EDITOR=vscode  # vscode | cursor | idea | vim
```

<br>

**Update to latest version**

```
uv tool uninstall rgi
uv tool install git+https://github.com/dandavison/rgi
```

## Usage

`rgi`

Then use [ripgrep](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html) as usual: search results will update dynamically.


**Keyboard shortcuts**


- **Enter**: Open the selected file at the matched line in your editor / IDE
- **Tab**: Toggle between editing the full `rg` command vs editing just the search regex (experimental/buggy)

**`rg` usage notes**

Consider using:
- `-g` for on-the-fly file path filtering
- [config file](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html#configuration%20files) for project-specific file path inclusions/exclusions

See `rg --help` or an [rg manpage](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html).


**`fzf` usage notes**

Use the `FZF_DEFAULT_OPTS` environment variable to set `fzf` options.
Please open an issue if `rgi` is setting `fzf` options that you wish to control yourself.
See the environment variables section of `fzf --man`.