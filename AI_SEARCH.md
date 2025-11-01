# AI-Powered Search in rgi

## Overview

`rgi` now supports AI-powered search generation! Simply describe what you're looking for in plain English, and the tool will generate multiple ripgrep commands to help you find it.

## How to Use

1. **Trigger AI Mode**: In pattern mode, type `??` followed by your search description
   ```
   ??find all TODO comments in Python files
   ```

2. **Generate Commands**: Press `Tab` to send your description to an AI assistant, which will generate multiple search strategies

3. **Navigate Results**: The tool switches to command mode showing the first AI-generated command
   - Use `↑` and `↓` arrow keys to cycle through different commands
   - The header shows which command you're viewing (e.g., "AI Command 2/5")

4. **Execute or Return**: 
   - Press `Enter` to select a file from the search results
   - Press `Tab` to return to pattern mode
   - Press `Esc` to exit

## Examples

Try these AI prompts:

- `??find all TODO comments in Python files`
- `??locate class definitions`
- `??search for import statements in JavaScript`
- `??find function definitions with async/await`
- `??look for error handling code`
- `??find database connection strings`
- `??search for API endpoints`
- `??find test files and test functions`

## Requirements

This feature requires one of the following LLM CLI tools:
- `claude code --print` (Claude AI)
- `cursor agent --print` (Cursor AI)

The tool will try both and use whichever is available.

## Technical Details

- The AI generates a JSON array of complete `rg` commands
- Each command includes appropriate flags and search patterns
- Commands are comprehensive, providing multiple search strategies
- The tool maintains state to allow cycling through commands
- If LLM tools aren't available, a message is displayed in stderr
