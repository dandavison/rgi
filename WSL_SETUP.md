# WSL Setup Guide for rgi

## Prerequisites

Ensure you have WSL2 with Ubuntu installed. Open WSL terminal and run:

```bash
# Update package list
sudo apt update

# Install required tools
sudo apt install -y git curl wget tmux

# Install ripgrep
curl -LO https://github.com/BurntSushi/ripgrep/releases/download/14.1.0/ripgrep_14.1.0-1_amd64.deb
sudo dpkg -i ripgrep_14.1.0-1_amd64.deb
rm ripgrep_14.1.0-1_amd64.deb

# Install bat (for file previews)
curl -LO https://github.com/sharkdp/bat/releases/download/v0.24.0/bat_0.24.0_amd64.deb
sudo dpkg -i bat_0.24.0_amd64.deb
rm bat_0.24.0_amd64.deb

# Install delta (for diff viewing)
curl -LO https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_amd64.deb
sudo dpkg -i git-delta_0.18.2_amd64.deb
rm git-delta_0.18.2_amd64.deb

# Install fzf (latest version)
curl -LO https://github.com/junegunn/fzf/releases/download/v0.55.0/fzf-0.55.0-linux_amd64.tar.gz
tar xzf fzf-0.55.0-linux_amd64.tar.gz
sudo mv fzf /usr/local/bin/
rm fzf-0.55.0-linux_amd64.tar.gz
```

## Installing rgi

### Option 1: Install from GitHub (Recommended)

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (also add this to your ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# Install rgi
uv tool install git+https://github.com/dandavison/rgi
```

### Option 2: Install from Local Clone

**IMPORTANT**: If you already cloned the repo and got line ending errors, you need to re-clone:

```bash
# Remove old clone if it exists
rm -rf rgi

# Configure git to handle line endings correctly
git config --global core.autocrlf input

# Clone fresh copy
git clone https://github.com/dandavison/rgi.git
cd rgi

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install rgi
uv tool install .
```

## Verification

After installation, verify everything works:

```bash
# Check all tools are installed
rg --version    # Should show ripgrep version
bat --version   # Should show bat version
delta --version # Should show delta version
fzf --version   # Should show fzf version
uv --version    # Should show uv version

# Test rgi
cd /tmp
echo "TODO: test this" > test.txt
rgi TODO

# You should see an interactive fzf interface with the TODO match
# Press Tab to switch modes
# Press Enter to open in editor (configure with export RGI_EDITOR=your_editor)
# Press Esc to exit
```

## Troubleshooting

### "python3\r: No such file or directory" Error

This is caused by Windows (CRLF) line endings. Solutions:

1. **Re-clone the repository** (see Option 2 above)
2. **Or fix existing clone**:
   ```bash
   cd rgi
   # Convert all files to Unix line endings
   find . -type f \( -name "*.sh" -o -name "*.py" -o -name "rgi*" \) -exec dos2unix {} \; 2>/dev/null || \
   find . -type f \( -name "*.sh" -o -name "*.py" -o -name "rgi*" \) -exec sed -i 's/\r$//' {} \;
   ```

### "tmux: command not found" Error

```bash
sudo apt install tmux
```

### fzf key bindings not working

Make sure you have fzf v0.55.0 or later (check with `fzf --version`).
The version in Ubuntu repos may be too old.

## What's Tested and Working

All functionality has been verified to work on WSL through our CI tests:

- ✅ Basic pattern search
- ✅ Command mode editing
- ✅ Tab key mode switching
- ✅ File preview (with bat)
- ✅ Multiple path searches
- ✅ Glob filtering
- ✅ Opening files in editor
- ✅ All helper scripts (rgi-preview, rgi-switch-mode, open-in-editor)

The CI runs these tests on every commit to ensure WSL compatibility.
