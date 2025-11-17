# CI/CD Setup for rgi

## Overview

This project uses GitHub Actions for continuous integration testing across multiple platforms and Python versions.

## Platforms Tested

- **Linux** (Ubuntu latest)
- **macOS** (latest)
- **Windows** (via WSL - Windows Subsystem for Linux)

## Python Versions

Tests run on Python 3.9, 3.10, 3.11, and 3.12 to ensure broad compatibility.

## Key Dependencies

The CI pipeline automatically installs:
- **tmux** - Terminal multiplexer required for interactive testing
- **ripgrep (rg)** - The core search tool
- **fzf** - Fuzzy finder for the interactive UI
- **git-delta** - For enhanced diff output
- **uv** - Fast Python package manager

## Workflow Triggers

The tests run automatically on:
- Push to `main` branch
- Pull requests targeting `main`
- Manual workflow dispatch

## Test Execution

Tests use an isolated tmux server socket to prevent interference with any existing tmux sessions. The test suite includes:
- Unit tests for all major functionality
- Interactive UI testing via tmux capture
- Type checking with `ty`

## CI Environment Adaptations

The test suite automatically detects CI environments and:
- Increases timeouts for slower CI runners
- Adds extra wait time for UI rendering
- Uses isolated tmux server sockets

## Viewing Results

Check the workflow status:
```bash
gh run list --limit 5
```

View a specific run:
```bash
gh run view <run-id>
```

Watch a run in real-time:
```bash
gh run watch <run-id>
```

## Local Testing

To run tests locally as they would in CI:
```bash
export CI=true
uv run pytest tests/test_rgi.py -v
```

## Windows Development

For Windows developers, tests run in WSL. Install WSL and Ubuntu:
```powershell
wsl --install -d Ubuntu-22.04
```

Then install dependencies in WSL:
```bash
sudo apt-get update
sudo apt-get install -y tmux ripgrep fzf
```

## Troubleshooting

If tests fail in CI but pass locally, check:
1. Timing issues - CI runners may be slower
2. Missing system dependencies
3. Platform-specific behavior differences
4. tmux version compatibility

## Type Checking

The project uses type annotations checked by `ty`. Run locally:
```bash
uvx ty check
```


