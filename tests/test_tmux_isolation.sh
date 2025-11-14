#!/bin/bash

# Test script to verify tmux isolation works

echo "================================"
echo "  Testing Tmux Isolation"
echo "================================"
echo ""

# Check if user has a tmux session running
USER_SESSIONS=$(tmux list-sessions 2>/dev/null | wc -l)
echo "User tmux sessions before test: $USER_SESSIONS"

# Run a simple test with isolated socket
echo ""
echo "Running test with isolated tmux socket..."
SOCKET="test-isolation-$$"

# Create a test session
tmux -L "$SOCKET" new-session -d -s test-session "echo 'Test in isolated tmux'"
sleep 0.5

# List sessions in isolated server
echo "Sessions in test socket:"
tmux -L "$SOCKET" list-sessions 2>/dev/null || echo "  (none)"

# List sessions in default server
echo ""
echo "Sessions in default tmux server:"
tmux list-sessions 2>/dev/null || echo "  (none)"

# Check that user sessions are unchanged
USER_SESSIONS_AFTER=$(tmux list-sessions 2>/dev/null | wc -l)
echo ""
echo "User tmux sessions after test: $USER_SESSIONS_AFTER"

# Clean up
tmux -L "$SOCKET" kill-server 2>/dev/null

if [ "$USER_SESSIONS" -eq "$USER_SESSIONS_AFTER" ]; then
    echo ""
    echo "✓ SUCCESS: Test tmux server is isolated from user's tmux sessions"
else
    echo ""
    echo "✗ FAILURE: Test affected user's tmux sessions"
fi






