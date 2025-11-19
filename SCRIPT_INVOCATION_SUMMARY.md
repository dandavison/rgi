# Script Invocation Summary for rgi

## 1. How Each Script is Invoked When Installed per README

### **rgi** (Main Entry Point)
- **Installation**: When user runs `uv tool install git+https://github.com/dandavison/rgi`, the `rgi` command is installed as a console script
- **Invocation**: `rgi [options] [pattern] [path]`
- **Mechanism**:
  - The Python entry point `rgi.cli:main` (defined in `pyproject.toml`) is called
  - This finds and executes `src/rgi/scripts/rgi` (a Python script with shebang `#!/usr/bin/env python3`)
  - The script adds its own directory to PATH (line 10-11) to make helper scripts available

### **rgi-preview** (File Preview)
- **Invocation**: Automatically called by fzf as `rgi-preview <filepath> <linenumber>`
- **When**: When user navigates through search results in the fzf interface
- **Mechanism**:
  - The main rgi script configures fzf with `--preview "[[ -n {1} ]] && rgi-preview {1} {2}"`
  - This is a bash script (`#!/bin/bash`) that uses `bat` for syntax highlighting

### **rgi-switch-mode** (Mode Toggle)
- **Invocation**: Called by fzf as `rgi-switch-mode [pattern|command] <query> [additional args]`
- **When**: When user presses Tab key to toggle between pattern mode and command mode
- **Mechanism**:
  - The main rgi script binds this to Tab: `tab:execute:rgi-switch-mode ...`
  - This is a Python script (`#!/usr/bin/env python3`) that re-invokes rgi with opposite mode

### **open-in-editor** (Editor Integration)
- **Invocation**: Called by fzf as `open-in-editor <filepath> <linenumber>`
- **When**: When user presses Enter on a search result
- **Mechanism**:
  - The main rgi script binds this to Enter: `enter:execute:open-in-editor {1} {2}`
  - This is a bash script (`#!/bin/bash`) that uses `$RGI_EDITOR` to open the file

## 2. Tests Added to Confirm Script Invocation

A comprehensive test suite has been added in `tests/test_script_invocation.py` with 8 tests:

1. **test_rgi_script_exists_and_executable**: Verifies main rgi script exists and has proper shebang
2. **test_rgi_preview_invocation**: Simulates how fzf invokes rgi-preview with file and line number
3. **test_rgi_switch_mode_invocation**: Tests both pattern and command mode switching as fzf would
4. **test_open_in_editor_invocation**: Tests editor opening with mocked editor command
5. **test_main_rgi_adds_scripts_to_path**: Verifies PATH manipulation code exists
6. **test_scripts_available_after_uv_install**: Confirms all scripts are packaged as expected
7. **test_script_invocation_on_platform**: Platform-specific tests (Linux/macOS/Windows)
8. **test_rgi_cli_entry_point**: Tests the Python entry point works correctly

## CI Integration

The GitHub Actions workflow has been updated to run these tests on all platforms:
- **Ubuntu** (Python 3.9, 3.10, 3.11, 3.12)
- **macOS** (Python 3.9, 3.10, 3.11, 3.12)
- **Windows WSL** (Python 3.11)

All tests verify that scripts can be invoked as they would be in real usage after installation.

