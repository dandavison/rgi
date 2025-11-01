# rgi

An interactive UI for ripgrep.

## Prerequisites

rgi requires the following tools to be installed:
- `rg` (ripgrep)
- `fzf`
- `bat`
- `delta`
- `tmux` (for running tests)

## Installation

### Using uvx (recommended)

Install and run directly from PyPI (once published):
```bash
uvx rgi <pattern> [paths...]
```

Install globally:
```bash
uv tool install rgi
rgi <pattern> [paths...]
```

### From source

Clone the repository and install in development mode:
```bash
git clone <repo-url> 
cd rgi
uv sync
uv run rgi <pattern> [paths...]
```

### For development

```bash
# Run from the repository
./rgi <pattern> [paths...]

# Or through uv
uv run rgi <pattern> [paths...]
```

## Usage

### Basic search
```bash
rgi TODO                    # Search for "TODO" in current directory
rgi "fn main" src/          # Search for "fn main" in src directory  
rgi -t py "import" .        # Search Python files for "import"
```

### Keyboard shortcuts

- **Tab**: Switch between pattern mode and command mode
- **Enter**: Open the selected file at the matched line
- **Ctrl-K**: Clear the current query
- **Alt-Left/Right**: Move cursor by word

### Pattern mode vs Command mode

- **Pattern mode** (default): The query is your search pattern
- **Command mode**: The query is the full ripgrep command for advanced control

## Testing

Run the test suite:
```bash
uv run test
```

## Building

Build the package for distribution:
```bash
uv build
```

This creates wheel and source distributions in the `dist/` directory.

## Publishing

To publish to PyPI (requires authentication):
```bash
uv publish
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
