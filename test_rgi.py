#!/usr/bin/env python3
"""Test the rgi script can build valid commands."""

import sys
import os
sys.path.insert(0, 'src/rgi/scripts')
os.environ['PATH'] = 'src/rgi/scripts:' + os.environ.get('PATH', '')

# Mock sys.argv for testing
original_argv = sys.argv
sys.argv = ['rgi', 'test', '.']

try:
    # Import after setting sys.argv
    import rgi
    
    # Test parsing arguments
    mode, pattern, paths, rg_opts = rgi.parse_arguments(['test', '.'])
    print(f"Parsed: mode={mode}, pattern={pattern}, paths={paths}, rg_opts={rg_opts}")
    
    # Test building command
    config_args = ""
    IMPLICIT_OPTS = "--json"
    RG = f"rg{rg_opts} {IMPLICIT_OPTS}"
    DELTA = "delta --grep-output-type classic"
    RIPGREP_CONFIG_PATH = ""
    
    fzf_cmd = rgi.build_pattern_mode_fzf(
        pattern, paths, rg_opts, config_args, RG, DELTA, RIPGREP_CONFIG_PATH
    )
    
    print(f"\nFzf command built successfully!")
    print(f"Command parts: {len(fzf_cmd)} items")
    
    # Check the reload command
    for i, part in enumerate(fzf_cmd):
        if 'reload:' in part:
            print(f"\nReload command at index {i}:")
            print(f"  {part[:100]}...")
            break

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sys.argv = original_argv
