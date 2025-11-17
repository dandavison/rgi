An interactive UI for ripgrep.

## Installation

Install [uv](https://docs.astral.sh/ty/installation/), [ripgrep](https://github.com/BurntSushi/ripgrep), [fzf](https://github.com/junegunn/fzf), [bat](https://github.com/sharkdp/bat), [delta](https://dandavison.github.io/delta/installation.html).

E.g. on MacOS `brew install uv ripgrep fzf bat git-delta`.

Then:

```
uv tool install git+https://github.com/dandavison/rgi
export RGI_EDITOR=vscode  # vscode | cursor | idea
```

**Update to latest version**

```
uv tool uninstall rgi
uv tool install git+https://github.com/dandavison/rgi
```

## Usage

`rgi`

Then use [ripgrep](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html) as usual: search results will update dynamically.


**Notable ripgrep features**
- `-g, --glob` for on-the-fly file path filtering
- [config file](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html#configuration%20files) for project-specific file path inclusions/exclusions

See `rg --help` or an [rg manpage](https://manpages.ubuntu.com/manpages/jammy/man1/rg.1.html).


**Keyboard shortcuts**


- **Enter**: Open the selected file at the matched line in your editor / IDE
- **Tab**: Toggle between editing the full `rg` command vs editing just the search regex (experimental)
